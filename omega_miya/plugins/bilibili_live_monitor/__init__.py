import nonebot
import asyncio
import re
from nonebot.command.argfilter import validators, controllers
from omega_miya.plugins.bilibili_live_monitor.get_live_info import *
from nonebot import on_command, CommandSession, permission, log
from omega_miya.plugins.Group_manage.group_permissions import *

__plugin_name__ = 'B站直播间订阅'
__plugin_usage__ = r'''【B站直播间订阅】

随时更新直播间状态

用法: 
/清空(重置)直播间订阅 *群管理员可用

/订阅直播间 *群管理员可用

/查看直播间订阅

/谁在播'''

# 初始化直播间标题, 状态, up名称
live_title = {}
live_status = {}
live_up_name = {}


async def init_live_info():
    global live_title
    global live_status
    global live_up_name

    for __room_id in query_live_sub_list():
        try:
            # 获取直播间信息
            __live_info = await get_live_info(__room_id)

            # 获取直播间UP名称
            __up_uid = __live_info['uid']
            __up_info = await get_user_info(__up_uid)

            # 直播状态放入live_status全局变量中
            live_status[__room_id] = int(__live_info['status'])

            # 直播间标题放入live_title全局变量中
            live_title[__room_id] = str(__live_info['title'])

            # 直播间up名称放入live_up_name全局变量中
            live_up_name[__room_id] = str(__up_info['name'])
        except Exception as err:
            log.logger.error(f'{__name__}: 初始化直播间状态列表时发生了错误: {err}, room_id: {__room_id}')
            continue
    log.logger.info(f'{__name__}: 已成功完成直播间状态列表初始化')


bot = nonebot.get_bot()


@bot.server_app.before_serving
async def init_live():
    # 这会在 NoneBot 启动后立即运行
    await init_live_info()


@on_command('clear_live_sub', aliases=('清空直播间订阅', '重置直播间订阅'), only_to_me=False,
            permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def clear_live_sub(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        await session.send('本命令不支持在私聊中使用QAQ')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令, 已中止命令执行')
        return
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    try:
        __is_success = await clean_group_live_sub_in_db(group_id=group_id)
        if not __is_success:
            await session.send('发生了意料之外的错误OvO')
            log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图清空直播间订阅时发生了错误, '
                               f'数据库操作失败, 错误信息见日志.')
            return
        await session.send('已清空本群组直播间订阅OvO')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 已成功清空群组: {group_id} 的直播间订阅')
    except Exception as e:
        await session.send('发生了未知的错误QAQ')
        log.logger.warning(f'{__name__}: 用户: {session.event.user_id} 试图清空群组: {group_id} 的群组直播间订阅时发生了错误: {e}')


@on_command('new_live_sub', aliases='订阅直播间', only_to_me=False,
            permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def new_live_sub(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        await session.send('本命令不支持在私聊中使用QAQ')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令, 已中止命令执行')
        return
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    # 从会话状态（session.state）中获取sub_id, 如果当前不存在, 则询问用户
    __sub_id = session.get('sub_id', prompt='请输入直播间房间号: ',
                           arg_filters=[controllers.handle_cancellation(session),
                                        validators.not_empty('输入不能为空'),
                                        validators.match_regex(r'^\d+$', '房间号格式不对哦, 请重新输入~',
                                                               fullmatch=True)])
    # 获取直播间信息
    __live_info = await get_live_info(__sub_id)
    if __live_info['status'] == 'error':
        await session.send('似乎并没有这个直播间QAQ')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 添加直播间订阅失败, '
                        f'没有找到该房间号: {__sub_id} 对应的直播间')
        return
    else:
        __up_info = await get_user_info(__live_info['uid'])
        __up_name = __up_info['name']
        __sub_check = session.get('check', prompt=f'即将订阅【{__up_name}】的直播间！\n确认吗？\n\n【是/否】',
                                  arg_filters=[controllers.handle_cancellation(session),
                                               validators.not_empty('输入不能为空'),
                                               validators.match_regex(r'^[是否]$', '输入不对哦, 请重新输入~',
                                                                      fullmatch=True)])
        if __sub_check == '否':
            await session.send('那就不订阅好了QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 已取消添加直播间订阅, 操作中止')
            return
        elif __sub_check == '是':
            try:
                # 首先更新直播间信息
                __is_success = await add_live_sub_to_db(sub_id=__sub_id, up_name=__up_name)
                if not __is_success:
                    await session.send('发生了意料之外的错误OvO')
                    log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                       f'试图订阅直播间{__sub_id}时发生了错误, 更新直播间信息数据库操作失败, 错误信息见日志.')
                    return
                # 然后添加群组订阅
                __is_success = await add_group_live_sub_to_db(sub_id=__sub_id, group_id=group_id)
                if not __is_success:
                    await session.send('发生了意料之外的错误OvO')
                    log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                       f'试图订阅直播间{__sub_id}时发生了错误, 添加群组订阅数据库操作失败, 错误信息见日志.')
                    return
                # 添加直播间时需要刷新全局监控列表

                # 执行一次初始化
                await init_live_info()

                await session.send(f'已成功的订阅【{__up_name}】的直播间！')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 已成功添加: {__up_name} 的直播间订阅')
            except Exception as e:
                log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                   f'试图添加: {__sub_id} 直播间订阅时发生了错误: {e}')
                session.finish('发生了未知的错误QAQ')


@new_live_sub.args_parser
async def _(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            return
    elif session_type == 'private':
        return
    else:
        return
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()
    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空, 意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if len(splited_arg) == 1 and re.match(r'^\d+$', splited_arg[0]):
                session.state['sub_id'] = splited_arg[0]
                return
            else:
                session.finish('输入的格式好像不对呢, 请确认后重新输入命令吧~')
    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


@on_command('query_group_live_sub', aliases=('查看直播间订阅', '查询直播间订阅'), only_to_me=False, permission=permission.GROUP)
async def query_group_sub(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        await session.send('本命令不支持在私聊中使用QAQ')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令, 已中止命令执行')
        return
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    try:
        __group_sub_list = await query_group_live_sub_list(group_id=group_id)
        if not __group_sub_list:
            await session.send('本群组还没有订阅任何直播间QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询了群组直播间订阅')
            return
        msg = ''
        for __sub_id in __group_sub_list:
            __live_info = await get_live_info(__sub_id)
            __up_uid = __live_info['uid']
            __up_info = await get_user_info(__up_uid)
            __up_name = __up_info['name']
            msg += f'\n【{__up_name}】'
        await session.send(f'本群已订阅了以下直播间: \n{msg}')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询了群组直播间订阅')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图查询群组直播间订阅时发生了错误: {e}')


@nonebot.scheduler.scheduled_job(
    'cron',
    # year=None,
    # month=None,
    # day=None,
    # week=None,
    # day_of_week=None,
    # hour=None,
    minute='*/2',
    # second=None,
    # start_date=None,
    # end_date=None,
    # timezone=None,
    coalesce=True,
    misfire_grace_time=30
)
async def live_check():
    async def check_user_live(room_id):
        try:
            # 获取直播间信息
            live_info = await get_live_info(room_id)
            # 获取订阅了该直播间的所有群
            group_which_sub_live = await query_group_whick_sub_live(room_id)
            log.logger.debug(f"{__name__}: 计划任务: live_check, 已获取直播间状态: {room_id}")
        except Exception as get_info_err:
            log.logger.warning(f'{__name__}: 试图检查直播间: {room_id} 状态时发生了错误: {get_info_err}')
            return

        __up_name = live_up_name[room_id]

        # 检查是否是已开播状态, 若已开播则监测直播间标题变动
        # 为避免开播时同时出现标题变更通知和开播通知, 在检测到直播状态变化时更新标题, 且仅在直播状态为直播中时发送标题变更通知
        if live_info['status'] != live_status[room_id]\
                and live_info['status'] == 1\
                and live_info['title'] != live_title[room_id]:
            try:
                # 更新标题
                live_title[room_id] = live_info['title']
                log.logger.info(f'{__name__}: 已成功更新标题状态列表中直播间: {room_id} 的标题信息')
            except Exception as get_title_err:
                log.logger.warning(f'{__name__}: 更新直播间: {room_id} 的标题时发生了错误: {get_title_err}')
                return
        elif live_info['status'] == 1 and live_info['title'] != live_title[room_id]:
            try:
                # 通知有通知权限且订阅了该直播间的群
                msg = '{}的直播间换标题啦！\n\n【{}】\n{}'.format(
                    __up_name, live_info['title'], live_info['url'])
                for group_id in list(set(all_noitce_groups) & set(group_which_sub_live)):
                    try:
                        await bot.send_group_msg(group_id=group_id, message=msg)
                        log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送直播间: {room_id} 标题变更的通知")
                    except Exception as err:
                        log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                           f"发送直播间: {room_id} 标题变更的通知失败, error info: {err}.")
                        continue
                # 更新标题
                live_title[room_id] = live_info['title']
                log.logger.info(f'{__name__}: 已成功更新标题状态列表中直播间: {room_id} 的标题信息')
            except Exception as get_title_err:
                log.logger.warning(f'{__name__}: 试图向群组发送直播间: {room_id} 的标题变更通知时发生了错误: {get_title_err}')
                return
        # 检查直播间状态与原状态是否一致
        if live_info['status'] != live_status[room_id]:
            try:
                # 现在状态为未开播
                if live_info['status'] == 0:
                    # 通知有通知权限且订阅了该直播间的群
                    msg = '{}下播了'.format(__up_name)
                    for group_id in list(set(all_noitce_groups) & set(group_which_sub_live)):
                        try:
                            await bot.send_group_msg(group_id=group_id, message=msg)
                            log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送直播间: {room_id} 下播通知")
                        except Exception as err:
                            log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                               f"发送直播间: {room_id} 下播通知失败, error info: {err}.")
                            continue
                        # 更新直播间状态
                    live_status[room_id] = live_info['status']
                    log.logger.info(f'{__name__}: 已成功更新直播状态列表中直播间: {room_id} 的状态信息')
                # 现在状态为直播中
                elif live_info['status'] == 1:

                    # 打一条log记录准确开播信息
                    log.logger.info(f"{__name__}: LiveStart! Room: {room_id}/{__up_name}, Title: {live_info['title']}, "
                                    f"TrueTime: {live_info['time']}")

                    msg = '{}\n{}开播啦！\n\n【{}】\n{}'.format(
                        live_info['time'], __up_name,
                        live_info['title'], live_info['url'])
                    for group_id in list(set(all_noitce_groups) & set(group_which_sub_live)):
                        try:
                            await bot.send_group_msg(group_id=group_id, message=msg)
                            log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送直播间: {room_id} 开播通知")
                        except Exception as err:
                            log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                               f"发送直播间: {room_id} 开播通知失败, error info: {err}.")
                            continue
                    live_status[room_id] = live_info['status']
                    log.logger.info(f'{__name__}: 已成功更新直播状态列表中直播间: {room_id} 的状态信息')
                # 现在状态为未开播（轮播中）
                elif live_info['status'] == 2:
                    msg = '{}下播了（轮播中）'.format(__up_name)
                    for group_id in list(set(all_noitce_groups) & set(group_which_sub_live)):
                        try:
                            await bot.send_group_msg(group_id=group_id, message=msg)
                            log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送直播间: {room_id} 下播通知")
                        except Exception as err:
                            log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                               f"发送直播间: {room_id} 下播通知失败, error info: {err}.")
                            continue
                    live_status[room_id] = live_info['status']
                    log.logger.info(f'{__name__}: 已成功更新直播状态列表中直播间: {room_id} 的状态信息')
            except Exception as get_status_err:
                log.logger.warning(f'{__name__}: 试图向群组发送直播间: {room_id} 的直播通知时发生了错误: {get_status_err}')

    log.logger.debug(f"{__name__}: 计划任务: live_check, 开始检查直播间")
    global live_title
    global live_status
    global live_up_name

    all_noitce_groups = query_all_notice_groups()

    # 检查所有在订阅表里面的直播间(异步)
    tasks = []
    for rid in query_live_sub_list():
        tasks.append(check_user_live(rid))
    try:
        await asyncio.gather(*tasks)
        log.logger.debug(f"{__name__}: 计划任务: live_check, 直播间检查完成")
    except Exception as e:
        log.logger.error(f"{__name__}: dynamic_check ERROR, {e}")

    '''
    # 检查所有在订阅表里面的直播间(使用异步会触发B站风控导致无法读取信息, 改为使用同步)
    for rid in query_live_sub_list():
        try:
            await check_user_live(rid)
        except Exception as e:
            log.logger.error(f"{__name__}: dynamic_check ERROR, {e}")
            continue
    log.logger.debug(f"{__name__}: 计划任务: live_check, 直播间检查完成")
    '''


@on_command('check_live_status', aliases='谁在播', only_to_me=False, permission=permission.GROUP)
async def check_live_status(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        await session.send('本命令不支持在私聊中使用QAQ')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令, 已中止命令执行')
        return
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    try:
        # 查这个组订阅的直播间房号
        __sub_list = await query_group_live_sub_list(group_id=group_id)
        if not __sub_list:
            await session.send('本群组还没有订阅任何直播间QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询了群组直播间状态')
            return
        __is_living = ''
        __no_living = ''
        for sub_id in __sub_list:
            # 这个直播间的up名称
            __live_info = await get_live_info(sub_id)
            __up_uid = __live_info['uid']
            __up_info = await get_user_info(__up_uid)
            __up_name = __up_info['name']
            # 这个直播间状态
            status = await get_live_info(sub_id)
            # 根据对应状态放入相应列表
            if status['status'] in [0, 2]:
                __no_living += f'\n【{__up_name}】'
            elif status['status'] == 1:
                __is_living += f'\n【{__up_name}】'
        await session.send(f'本群订阅的直播间里\n\n直播中: {__is_living}\n\n未开播: {__no_living}')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询了群组直播间状态')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询群组直播间状态时发生了错误: {e}')
