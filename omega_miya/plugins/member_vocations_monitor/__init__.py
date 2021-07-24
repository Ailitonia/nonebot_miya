import nonebot
from nonebot import log
from omega_miya.plugins.member_vocations_monitor.check_member_vocation import \
    check_member_vocation, clear_member_vocation
from omega_miya.plugins.Group_manage.group_permissions import *

__CHECK_GROUP_LIST = []


bot = nonebot.get_bot()


@bot.server_app.before_serving
async def init_vocation_check_list():
    # 这会在 NoneBot 启动后立即运行
    global __CHECK_GROUP_LIST
    # 检查所有具备command权限的组
    try:
        __CHECK_GROUP_LIST = query_all_command_groups()
        log.logger.info(f'{__name__}: 已成功完成群组请假监控列表初始化')
    except Exception as err:
        log.logger.error(f'{__name__}: 初始化群组请假监控列表时发生了错误: {err}')


@nonebot.scheduler.scheduled_job(
    'cron',
    # year=None,
    # month=None,
    # day=None,
    # week=None,
    # day_of_week=None,
    hour='*/1',
    # minute=None,
    # second=None,
    # start_date=None,
    # end_date=None,
    # timezone=None,
    coalesce=True,
    misfire_grace_time=30
)
async def refresh_check_list():
    try:
        global __CHECK_GROUP_LIST
        __CHECK_GROUP_LIST = query_all_command_groups()
        log.logger.info(f'{__name__}: 已成功完成群组请假监控列表更新')
    except Exception as e:
        log.logger.warning(f'{__name__}: 更新群组请假监控列表时发生了错误: {e}')


@nonebot.scheduler.scheduled_job(
    'cron',
    # year=None,
    # month=None,
    # day=None,
    # week=None,
    # day_of_week=None,
    # hour=None,
    minute='*/3',
    # second=None,
    # start_date=None,
    # end_date=None,
    # timezone=None,
    coalesce=True,
    misfire_grace_time=30
)
async def member_vocations_monitor():
    log.logger.debug(f"{__name__}: 计划任务: member_vocations_monitor, 开始检查请假状态")
    over_vocation_user = set()
    for GROUP_ID in __CHECK_GROUP_LIST:
        try:
            group_user_list = await bot.get_group_member_list(group_id=GROUP_ID)
            log.logger.debug(f"{__name__}: 计划任务: member_vocations_monitor, 已获取成员列表")
            for user_info in group_user_list:
                __user_nickname = user_info['card']
                if not __user_nickname:
                    __user_nickname = user_info['nickname']
                __user_qq = user_info['user_id']
                __result = await check_member_vocation(user_qq=__user_qq)
                if __result:
                    over_vocation_user.add(__user_qq)
                    msg = f'{__user_nickname}的假期已经结束啦~\n快给他/她安排工作吧！'
                    await bot.send_group_msg(group_id=GROUP_ID, message=msg)
                    log.logger.info(f'{__name__}: 群组: {GROUP_ID}, 用户: {__user_qq} 的假期已经结束, 已更新发送通知信息')
            log.logger.debug(f"{__name__}: 计划任务: member_vocations_monitor, 已获完成请假状态检查")
        except Exception as e:
            log.logger.warning(f'{__name__}: 请假监控试图检查群组: {GROUP_ID} 请假状态时发生了错误: {e}')
            continue
    # 重置假期结束用户状态
    for user_qq in over_vocation_user:
        try:
            __result = await clear_member_vocation(user_qq=user_qq)
            if __result:
                await bot.send_private_msg(user_id=user_qq, message='告诉你个鬼故事~')
                await bot.send_private_msg(user_id=user_qq, message='你假期没啦~')
                log.logger.info(f'{__name__}: 用户: {user_qq} 的假期已经结束, 已更新用户数据库信息')
            else:
                log.logger.warning(f'{__name__}: 请假监控试图重置用户: {user_qq} 请假状态时发生了错误, 错误信息见日志')
        except Exception as e:
            log.logger.error(f'{__name__}: 请假监控试图重置用户: {user_qq} 请假状态时发生了错误: {e}')
            continue
