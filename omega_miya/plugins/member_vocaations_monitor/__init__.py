import nonebot
from omega_miya.plugins.member_vocaations_monitor.check_member_vocation import check_member_vocation
from omega_miya.plugins.Group_manage.group_permissions import *

# 检查间隔，单位分钟
CHECK_INTERVAL = 1

# 检查所有具备command权限的组
__CHECK_GROUP_LIST = query_all_command_groups()

bot = nonebot.get_bot()


@nonebot.scheduler.scheduled_job('interval', minutes=60)
async def refresh_check_list():
    global __CHECK_GROUP_LIST
    __CHECK_GROUP_LIST = query_all_command_groups()


@nonebot.scheduler.scheduled_job('interval', minutes=CHECK_INTERVAL)
async def member_vocations_monitor():
    for GROUP_ID in __CHECK_GROUP_LIST:
        group_user_list = await bot.get_group_member_list(group_id=GROUP_ID)
        for user_info in group_user_list:
            __user_nickname = user_info['card']
            if not __user_nickname:
                __user_nickname = user_info['nickname']
            __user_qq = user_info['user_id']
            __result = await check_member_vocation(user_qq=__user_qq)
            if __result:
                msg = f'{__user_nickname}的假期已经结束啦~\n快给他/她安排工作吧！'
                await bot.send_group_msg(group_id=GROUP_ID, message=msg)
                await bot.send_private_msg(user_id=__user_qq, message='告诉你个鬼故事~')
                await bot.send_private_msg(user_id=__user_qq, message='你假期没啦~')
