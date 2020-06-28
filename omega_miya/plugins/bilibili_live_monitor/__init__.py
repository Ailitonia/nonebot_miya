import nonebot
import re
from omega_miya.plugins.bilibili_live_monitor.config import MONITOR_LIST, CHECK_LIST, CHECK_INTERVAL
from omega_miya.plugins.bilibili_live_monitor.get_live_info import init_live_status, init_live_title, get_live_info
from aiocqhttp import Event
from omega_miya.plugins.Group_manage.group_permissions import *


__plugin_name__ = 'B站直播间监控'
__plugin_usage__ = r'''【B站直播间监控】

随时更新直播间状态

在群里问：“***在直播吗/开播了吗/播了吗”等
即可查询在监控列表中的up的直播间状态'''


# 初始化直播间状态
live_status = {}
for _room_id in MONITOR_LIST.keys():
    # 直播状态放入live_status全局变量中
    live_status[_room_id] = init_live_status(_room_id)

# 初始化直播间标题
live_title = {}
for _room_id in MONITOR_LIST.keys():
    # 直播间标题放入live_title全局变量中
    live_title[_room_id] = init_live_title(_room_id)

bot = nonebot.get_bot()


@nonebot.scheduler.scheduled_job('interval', minutes=CHECK_INTERVAL)
async def live_check():
    global live_status
    global live_title
    # 检查监控列表内的直播间
    for room_id in MONITOR_LIST.keys():
        # 获取直播间信息
        live_info = await get_live_info(room_id)
        # 检查是否是已开播状态，若已开播则监测直播间标题变动
        if live_info['status'] == 1 and live_info['title'] != live_title[room_id]:
            for group_id in query_all_noitce_groups():
                msg = '{}的直播间换标题啦！\n\n【{}】\n{}'.format(
                    MONITOR_LIST[room_id][0], live_info['title'], live_info['url'])
                await bot.send_group_msg(group_id=group_id, message=msg)
                # 更新标题
                live_title[room_id] = live_info['title']
        # 检查直播间状态与原状态是否一致
        if live_info['status'] != live_status[room_id]:
            # 现在状态为未开播
            if live_info['status'] == 0:
                # 通知每个群组
                for group_id in query_all_noitce_groups():
                    msg = '{}下播了'.format(MONITOR_LIST[room_id][0])
                    await bot.send_group_msg(group_id=group_id, message=msg)
                    # 更新直播间状态
                    live_status[room_id] = live_info['status']
            # 现在状态为直播中
            elif live_info['status'] == 1:
                for group_id in query_all_noitce_groups():
                    msg = '{}\n{}开播啦！\n\n【{}】\n{}'.format(
                        live_info['time'], MONITOR_LIST[room_id][0],
                        live_info['title'], live_info['url'])
                    await bot.send_group_msg(group_id=group_id, message=msg)
                    live_status[room_id] = live_info['status']
            # 现在状态为未开播（轮播中）
            elif live_info['status'] == 2:
                for group_id in query_all_noitce_groups():
                    msg = '{}下播了（轮播中）'.format(MONITOR_LIST[room_id][0])
                    await bot.send_group_msg(group_id=group_id, message=msg)
                    live_status[room_id] = live_info['status']


@bot.on_message('group')
async def check_live_status(event: Event):
    group_id = event.group_id
    if group_id not in query_all_command_groups():
        return
    msg = str(event.message)
    # 用正则来匹配发言中的查询命令
    p = r'^.+(在直?播|开?播)了?[吗嘛]$'
    if re.match(p, msg):
        alias = re.sub(r'(在直?播|开?播)了?[吗嘛]$', '', msg)
        if alias in CHECK_LIST.keys():
            status = await get_live_info(CHECK_LIST[alias])
            if status['status'] in [0, 2]:
                msg = '{}没在播'.format(alias)
                await bot.send_group_msg(group_id=group_id, message=msg)
            elif status['status'] == 1:
                msg = '{}正在直播:\n\n【{}】\n{}'.format(alias, status['title'], status['url'])
                await bot.send_group_msg(group_id=group_id, message=msg)
        else:
            msg = '没有{}，你在想什么啊？'.format(alias)
            await bot.send_group_msg(group_id=group_id, message=msg)
