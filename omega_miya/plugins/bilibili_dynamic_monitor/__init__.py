import nonebot
import re
from omega_miya.plugins.bilibili_dynamic_monitor.config import MONITOR_LIST, CHECK_LIST, CHECK_INTERVAL
from omega_miya.plugins.bilibili_dynamic_monitor.get_dynamic_info import init_live_info, get_dynamic_info
from aiocqhttp import Event
from omega_miya.plugins.Group_manage.group_permissions import *


__plugin_name__ = 'B站动态监控'
__plugin_usage__ = r'''【B站动态监控】

随时更新up动态

在群里问：“给/让我康康***的动态”
即可查询在监控列表中的up的最新动态'''


# 初始化动态ID列表
dynamic_id_list = {}
for _dy_uid in MONITOR_LIST.keys():
    # 动态列表放入live_status全局变量中
    dynamic_id_list[_dy_uid] = init_live_info(_dy_uid)


bot = nonebot.get_bot()


@nonebot.scheduler.scheduled_job('interval', minutes=CHECK_INTERVAL)
async def dynamic_check():
    global dynamic_id_list
    # 检查监控列表中的up
    for dy_uid in MONITOR_LIST.keys():
        dynamic_info = await get_dynamic_info(dy_uid)
        for num in range(len(dynamic_info)):
            # 如果有新的
            if dynamic_info[num]['id'] not in dynamic_id_list[dy_uid]:
                # 转发的动态
                if dynamic_info[num]['type'] == 1:
                    for group_id in query_all_noitce_groups():
                        msg = '{}转发了{}的动态！\n\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['origin'],
                            dynamic_info[num]['content'], dynamic_info[num]['url'])
                        await bot.send_group_msg(group_id=group_id, message=msg)
                # 原创的动态
                elif dynamic_info[num]['type'] == 2:
                    for group_id in query_all_noitce_groups():
                        msg = '{}发布了新动态！\n\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['content'], dynamic_info[num]['url'])
                        await bot.send_group_msg(group_id=group_id, message=msg)
                # 视频
                elif dynamic_info[num]['type'] == 8:
                    for group_id in query_all_noitce_groups():
                        msg = '{}发布了新的视频！\n\n《{}》\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['origin'],
                            dynamic_info[num]['content'], dynamic_info[num]['url'])
                        await bot.send_group_msg(group_id=group_id, message=msg)
                # 文章
                elif dynamic_info[num]['type'] == 64:
                    for group_id in query_all_noitce_groups():
                        msg = '{}发布了新的文章！\n\n《{}》\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['origin'],
                            dynamic_info[num]['content'], dynamic_info[num]['url'])
                        await bot.send_group_msg(group_id=group_id, message=msg)
        # 刷新动态列表
        dynamic_id_list[dy_uid] = init_live_info(dy_uid)


@bot.on_message('group')
async def check_dynamic_status(event: Event):
    group_id = event.group_id
    if group_id not in query_all_command_groups():
        return
    msg = str(event.message)
    # 用正则来匹配发言中的查询命令
    p = r'^[让给]我康康.+的动态$'
    if re.match(p, msg):
        msg = re.sub(r'^[让给]我康康', '', msg)
        alias = re.sub(r'的动态$', '', msg)
        if alias in CHECK_LIST.keys():
            info = await get_dynamic_info(CHECK_LIST[alias])
            msg = '{}最新发布的动态是：\n\n“{}”\n{}'.format(
                info[0]['name'], info[0]['content'], info[0]['url'])
            await bot.send_group_msg(group_id=group_id, message=msg)
        else:
            msg = '没有{}，你在想什么啊？'.format(alias)
            await bot.send_group_msg(group_id=group_id, message=msg)
