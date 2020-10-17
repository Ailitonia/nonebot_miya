import re
from omega_miya.plugins.Group_manage.group_permissions import *
from datetime import datetime, timedelta
from nonebot import CommandSession, CommandGroup, permission, log
from nonebot.command.argfilter import validators, controllers
from omega_miya.plugins.member_status_vocations.status_manage import \
    set_my_status_in_db, query_my_status, set_my_vocation_in_db, \
    query_my_vocation, query_who_not_busy, query_which_skill_not_busy, query_who_in_vocation

__plugin_name__ = '请假'
__plugin_usage__ = r'''【工作状态与请假】

使用这个命令可以设置/查询自己的工作状态
以及设置自己的假期

用法: 
【不输入参数可进入向导模式】

/设置状态 [状态]  *只能设置空闲或工作, 请假请用/请假命令

/我的状态

/请假 [时间] [理由(可选)]

/我的假期

/谁有空 [技能名称(可选)]

/谁在休假
'''

status = CommandGroup('Status')


@status.command('set_my_status', aliases='设置状态', only_to_me=False, permission=permission.GROUP)
async def set_my_status(session: CommandSession):
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
    __user_qq = session.event.user_id
    __status = session.get('status', prompt='请输入你想设置的状态: \n可选"空闲"、"工作"',
                           arg_filters=[controllers.handle_cancellation(session),
                                        validators.not_empty('输入不能为空'),
                                        validators.match_regex(r'^(空闲|工作)$', '没有这个状态, 请重新输入~',
                                                               fullmatch=True)])
    if __status == '空闲':
        __status = 0
    elif __status == '工作':
        __status = 2
    try:
        __result = await set_my_status_in_db(user_qq=__user_qq, user_status=__status)
        if __result:
            await session.send(f'为你设置了状态: 【{session.state["status"]}】')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 为自己更新了状态')
        else:
            await session.send(f'添加失败, 发生了意外的错误QAQ\n您可能不在用户列表中, 请联系管理员处理')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 设置状态失败, 用户不在用户列表中')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 试图使用命令set_my_status时发生了错误: {e}')


@set_my_status.args_parser
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
            if len(splited_arg) == 1 and splited_arg[0] in ['空闲', '工作']:
                session.state['status'] = splited_arg[0]
                return
            else:
                session.finish('输入的格式好像不对呢, 请确认后重新输入命令吧~')

    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


@status.command('get_my_status', aliases='我的状态', only_to_me=False, permission=permission.GROUP)
async def get_my_status(session: CommandSession):
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
        __user_qq = session.event.user_id
        __result = await query_my_status(__user_qq)
        if __result != 'error':
            await session.send(f'你现在的状态是: 【{__result}】')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 查询了自己的状态')
        else:
            await session.send('你似乎还没有设置过状态或者请过假呢!\n请使用【/设置状态】或【/请假】来更新你的状态吧~')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 查询了自己的状态, 其未设置状态')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令get_my_status时发生了错误: {e}')


@status.command('vocation', aliases='请假', only_to_me=False, permission=permission.GROUP)
async def vocation(session: CommandSession):
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
    __user_qq = session.event.user_id
    __time = session.get('time', prompt='请输入你想请假的时间: \n仅支持数字+周/天/小时/分/分钟/秒',
                         arg_filters=[controllers.handle_cancellation(session),
                                      validators.not_empty('输入不能为空'),
                                      validators.match_regex(r'^\d+(周|天|小时|分|分钟|秒)$',
                                                             '仅支持数字+周/天/小时/分/分钟/秒, 请重新输入~',
                                                             fullmatch=True)])
    __reason = session.get('reason', prompt='请输入你的请假理由: \n不想告诉我理由的话就输入无理由吧~',
                           arg_filters=[controllers.handle_cancellation(session)])
    __add_time = timedelta()
    if re.match(r'^\d+周$', __time):
        __time = int(re.sub(r'周$', '', __time))
        __add_time = timedelta(weeks=__time)
    elif re.match(r'^\d+天$', __time):
        __time = int(re.sub(r'天$', '', __time))
        __add_time = timedelta(days=__time)
    elif re.match(r'^\d+小时$', __time):
        __time = int(re.sub(r'小时$', '', __time))
        __add_time = timedelta(hours=__time)
    elif re.match(r'^\d+(分|分钟)$', __time):
        __time = int(re.sub(r'(分|分钟)$', '', __time))
        __add_time = timedelta(minutes=__time)
    elif re.match(r'^\d+秒$', __time):
        __time = int(re.sub(r'秒$', '', __time))
        __add_time = timedelta(seconds=__time)
    __vocation_time = datetime.now() + __add_time
    try:
        __result = await set_my_vocation_in_db(user_qq=__user_qq, vocation_times=__vocation_time, reason=__reason)
        if __result:
            await session.send(f'请假成功！\n你的假期将持续到: \n【{__vocation_time.strftime("%Y-%m-%d %H:%M:%S")}】')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 请假成功')
        else:
            await session.send('请假失败, 发生了意外的错误QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 请假失败, 用户不在用户列表中')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 试图使用命令vocation时发生了错误: {e}')


@vocation.args_parser
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
            if len(splited_arg) == 1 and re.match(r'^\d+(周|天|小时|分|分钟|秒)$', splited_arg[0]):
                session.state['time'] = splited_arg[0]
                session.state['reason'] = None
                return
            elif len(splited_arg) == 2 and re.match(r'^\d+(周|天|小时|分|分钟|秒)$', splited_arg[0]):
                session.state['time'] = splited_arg[0]
                session.state['reason'] = splited_arg[1]
                return
            else:
                session.finish('输入的格式好像不对呢, 请确认后重新输入命令吧~')
                return

    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


@status.command('get_my_vocation', aliases='我的假期', only_to_me=False, permission=permission.GROUP)
async def get_my_vocation(session: CommandSession):
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
    __user_qq = session.event.user_id
    try:
        __result = await query_my_vocation(__user_qq)
        if __result != 'error' and __result != 'not_in_vocation':
            await session.send(f'你的假期将持续到: 【{__result}】')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 查询假期成功')
        elif __result != 'error' and __result == 'not_in_vocation':
            await session.send('你似乎并不在假期中呢~需要现在请假吗？')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 查询假期成功, 用户不在假期中')
        else:
            await session.send('似乎发生了点错误QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 查询假期失败, query_my_vocation错误')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 试图使用命令get_my_vocation时发生了错误: {e}')


@status.command('who_not_busy', aliases='谁有空', only_to_me=False, permission=permission.GROUP)
async def who_not_busy(session: CommandSession):
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
    __which_skill = session.get('skill')
    try:
        # 没有指定技能, 查所有人
        if not __which_skill:
            __user_qq = session.event.user_id
            __result = await query_who_not_busy(group_id)
            msg = ''
            if 'error' not in __result.keys() and __result.items():
                for item in __result.items():
                    msg += f'\n【{item[0]}{item[1]}】'
                await session.send(f'现在有空的人: \n{msg}')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询空闲成功')
            elif 'error' not in __result.keys() and not __result.items():
                await session.send(f'现在似乎没人有空呢QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询空闲成功')
            elif 'error' in __result.keys():
                await session.send('似乎发生了点错误QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询空闲失败, query_who_not_busy错误')
        # 指定了技能, 查对应技能
        elif __which_skill:
            __result = await query_which_skill_not_busy(__which_skill, group_id)
            if 'error' not in __result and __result:
                msg = ''
                for item in __result:
                    msg += f'\n【{item}】'
                await session.send(f'现在有空的{__which_skill}人: \n{msg}')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询空闲成功')
            elif 'error' not in __result and not __result:
                await session.send(f'现在似乎没人有空呢QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询空闲成功')
            elif 'error' in __result:
                await session.send('似乎发生了点错误QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询空闲失败, query_who_not_busy错误')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令who_not_busy时发生了错误: {e}')


@who_not_busy.args_parser
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
            if len(splited_arg) == 1:
                session.state['skill'] = splited_arg[0]
                return
            else:
                session.finish('输入的格式好像不对呢, 请确认后重新输入命令吧~')
                return

    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        session.state['skill'] = None
        return


@status.command('who_in_vocation', aliases='谁在休假', only_to_me=False, permission=permission.GROUP)
async def who_in_vocation(session: CommandSession):
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
    __user_qq = session.event.user_id
    try:
        __result = await query_who_in_vocation(group_id)
        msg = ''
        if 'error' not in __result.keys() and __result.items():
            for item in __result.items():
                msg += f'\n【{item[0]}/休假到: {item[1]}】'
            await session.send(f'现在在休假的的人: \n{msg}')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询假期成功')
        elif 'error' not in __result.keys() and not __result.items():
            await session.send(f'现在似乎没没有人休假呢~')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询假期成功')
        elif 'error' in __result.keys():
            await session.send('似乎发生了点错误QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询假期失败, query_who_in_vocation错误')
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {__user_qq} 试图使用命令who_in_vocation时发生了错误: {e}')
