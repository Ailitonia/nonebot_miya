from nonebot import permission, CommandSession, CommandGroup, log
from nonebot.command.argfilter import validators, controllers
from omega_miya.plugins.Group_manage.group_manage import \
    add_member_to_db, add_group_to_db, add_member_group_to_db, reset_member_status_to_db, \
    query_group_permissions_in_db, reset_group_permissions_to_db, set_group_permissions_to_db,\
    query_group_member_list, del_member_group_to_db

__plugin_name__ = '群信息管理'
__plugin_usage__ = r'''【群信息管理】

管理员专用
！！请不要轻易使用【/重置成员状态】命令！！
！！请不要轻易使用【/重置群组权限】命令！！

用法: 

/更新群组信息 *只有超管及群管理员能使用

/更新用户信息 *只有超管及群管理员能使用

/更新群组成员列表 *只有超管及群管理员能使用

/重置成员状态 *只有超管及群管理员能使用

/查询群组权限 *只有超管能及群管理员能使用

/设置群组权限 <权限组> *只有超管及群管理员能使用

/重置群组权限 *只有超管及群管理员能使用

说明:

当bot加入新群组时, 请管理员【首先】使用"/更新群组信息"命令为bot录入当前群组信息
之后使用"/设置群组权限"为当前群组配置命令权限
仅允许本群组接收bot推送通知, 请配置"/设置群组权限 通知"
仅允许本群组使用bot命令, 请配置"/设置群组权限 命令"
同时允许本群组使用命令与接收bot推送通知, 请配置"/设置群组权限 通知 命令"
取消本群组所有权限请使用"/重置群组权限"

若需要使用"技能""请假"命令组
请管理员在更新群组信息之后【依次】执行"/更新用户信息""/更新群组成员列表"
并在新成员加入后同样执行上述命令
'''

manage = CommandGroup('Manage')


@manage.command('refresh_member', aliases=('刷新用户信息', '更新用户信息'),
                only_to_me=False, permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def refresh_member(session: CommandSession):
    try:
        __group_user_list = await session.bot.get_group_member_list(group_id=session.event.group_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令refresh_member时发生错误: {e}, 该命令需要在群组中使用')
        session.finish('请在群组内使用该命令！')
        return
    try:
        for user_info in __group_user_list:
            __is_success = await add_member_to_db(user_qq=user_info['user_id'], user_nickname=user_info['nickname'])
            if not __is_success:
                log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用refresh_member'
                                   f'更新群组: {session.event.group_id} 时发生错误, '
                                   f"用户: {user_info['user_id']}信息写入数据库失败, 错误信息见日志.")
        await session.send('用户信息已更新~')
        log.logger.info(f'{__name__}: 用户{session.event.user_id} 使用refresh_member'
                        f'更新了群组: {session.event.group_id} 中成员的用户信息')
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令refresh_member时发生错误: {e}, 更新用户信息失败')


@manage.command('refresh_group', aliases=('刷新群组信息', '更新群组信息'),
                only_to_me=False, permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def refresh_group(session: CommandSession):
    try:
        __group_info = await session.bot.get_group_info(group_id=session.event.group_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令refresh_group时发生错误: {e}, 该命令需要在群组中使用')
        session.finish('请在群组内使用该命令！')
        return
    try:
        __is_success = await add_group_to_db(group_id=__group_info['group_id'], group_name=__group_info['group_name'])
        if not __is_success:
            await session.send('发生了意料之外的错误OvO')
            log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用refresh_group'
                               f'更新群组: {session.event.group_id} 时发生错误, 数据库操作失败, 错误信息见日志.')
            return
        await session.send('群组信息已更新~')
        log.logger.info(f'{__name__}: 用户{session.event.user_id} 使用refresh_group'
                        f'更新了群组: {session.event.group_id} 的群组信息')
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令refresh_group时发生错误: {e}, 更新群组信息失败')


@manage.command('refresh_member_group', aliases=('刷新群组成员列表', '更新群组成员列表'),
                only_to_me=False, permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def refresh_member_group(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_user_list = await session.bot.get_group_member_list(group_id=__group_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令refresh_member_group时发生错误: {e}, 该命令需要在群组中使用')
        session.finish('请在群组内使用该命令！')
        return
    # 首先清除数据库中退群成员
    try:
        __exist_member_list = []
        for user_info in __group_user_list:
            __user_qq = user_info['user_id']
            __exist_member_list.append(int(__user_qq))
        __db_member_list = query_group_member_list(group_id=__group_id)
        __del_member_list = list(set(__db_member_list).difference(set(__exist_member_list)))
        for user_qq in __del_member_list:
            __is_success = await del_member_group_to_db(user_qq=user_qq, group_id=__group_id)
            if not __is_success:
                log.logger.warning(f'{__name__}: refresh_member_group, 清除退群群组成员信息失败, 请检查日志, user_qq: {user_qq}')
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令refresh_member_group时发生错误: {e}, 清除退群群组成员失败')
        await session.send('清除退群群组成员信息失败QAQ')
        return
    try:
        for user_info in __group_user_list:
            __user_qq = user_info['user_id']
            __user_group_info = await session.bot.get_group_member_info(group_id=__group_id, user_id=__user_qq)
            __user_group_nickmane = __user_group_info['card']
            if not __user_group_nickmane:
                __user_group_nickmane = __user_group_info['nickname']
            __is_success = await add_member_group_to_db(user_qq=__user_qq, group_id=__group_id,
                                                        user_group_nickmane=__user_group_nickmane)
            if not __is_success:
                log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用refresh_member_group'
                                   f'更新群组: {session.event.group_id} 时发生错误, '
                                   f"用户: {__user_qq}信息写入数据库失败, 错误信息见日志.")
        await session.send('群组群组成员列表已更新~')
        log.logger.info(f'{__name__}: 用户{session.event.user_id} 使用refresh_member_group'
                        f'更新了群组: {session.event.group_id} 的群组成员列表')
    except Exception as e:
        await session.send('发生了意外的错误QAQ')
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令refresh_member_group时发生错误: {e}, 更新群组成员列表失败')


@manage.command('reset_member_status', aliases='重置成员状态',
                only_to_me=False, permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def reset_member_status(session: CommandSession):
    try:
        __group_user_list = await session.bot.get_group_member_list(group_id=session.event.group_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令reset_member_status时发生错误: {e}, 该命令需要在群组中使用')
        session.finish('请在群组内使用该命令！')
        return
    try:
        for user_info in __group_user_list:
            __is_success = await reset_member_status_to_db(user_qq=user_info['user_id'])
            if not __is_success:
                log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用refresh_member_group'
                                   f'更新群组: {session.event.group_id} 时发生错误, '
                                   f"用户: {user_info['user_id']}信息写入数据库失败, 错误信息见日志.")
        await session.send('成员状态已重置~')
        log.logger.info(f'{__name__}: 用户{session.event.user_id} 使用reset_member_status'
                        f'重置了群组: {session.event.group_id} 的群组成员状态')
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令reset_member_status时发生错误: {e}, 重置成员状态失败')


@manage.command('query_group_permissions', aliases='查询群组权限',
                only_to_me=False, permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def query_group_permissions(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_info = await session.bot.get_group_info(group_id=__group_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} '
                           f'使用命令query_group_permissions时发生错误: {e}, 该命令需要在群组中使用')
        session.finish('请在群组内使用该命令！')
        return
    try:
        __res = await query_group_permissions_in_db(group_id=__group_id)
        __result = []
        for item in __res.items():
            if item[1] == 1:
                __result.append(item[0])
        if not __result:
            await session.send('本群没有配置任何权限~')
        else:
            msg = ''
            for item in __result:
                msg += f'\n【{item}】'
            await session.send(f'本群组已配置如下权限: \n{msg}')
        log.logger.info(f'{__name__}: 用户{session.event.user_id} 使用query_group_permissions'
                        f'查询了群组: {session.event.group_id} 的群组权限')
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令query_group_permissions时发生错误: {e}, 查询群组权限失败')


@manage.command('reset_group_permissions', aliases='重置群组权限',
                only_to_me=False, permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def reset_group_permissions(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_info = await session.bot.get_group_info(group_id=__group_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} '
                           f'使用命令reset_group_permissions时发生错误: {e}, 该命令需要在群组中使用')
        session.finish('请在群组内使用该命令！')
        return
    try:
        __is_success = await reset_group_permissions_to_db(group_id=__group_id)
        if not __is_success:
            await session.send('发生了意料之外的错误OvO')
            log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用reset_group_permissions'
                               f'重置群组: {session.event.group_id} 时发生错误, 数据库操作失败, 错误信息见日志.')
            return
        await session.send('本群组权限已重置~')
        log.logger.info(f'{__name__}: 用户{session.event.user_id} 使用reset_group_permissions'
                        f'重置了群组: {session.event.group_id} 的群组权限')
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令reset_group_permissions时发生错误: {e}, 重置群组权限失败')


@manage.command('set_group_permissions', aliases='设置群组权限',
                only_to_me=False, permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def set_group_permissions(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_info = await session.bot.get_group_info(group_id=__group_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令set_group_permissions时发生错误: {e}, 该命令需要在群组中使用')
        session.finish('请在群组内使用该命令！')
        return

    noitce_permissions = session.get('noitce_permissions', prompt='是否配置【通知】权限？',
                                     arg_filters=[controllers.handle_cancellation(session),
                                                  validators.not_empty('输入不能为空'),
                                                  validators.match_regex(r'^(是|否)$', '请输入【是】或【否】',
                                                                         fullmatch=True)])
    command_permissions = session.get('command_permissions', prompt='是否配置【命令】权限？',
                                      arg_filters=[controllers.handle_cancellation(session),
                                                   validators.not_empty('输入不能为空'),
                                                   validators.match_regex(r'^(是|否)$', '请输入【是】或【否】',
                                                                          fullmatch=True)])
    admin_permissions = session.get('admin_permissions', prompt='是否配置【管理命令】权限？',
                                    arg_filters=[controllers.handle_cancellation(session),
                                                 validators.not_empty('输入不能为空'),
                                                 validators.match_regex(r'^(是|否)$', '请输入【是】或【否】',
                                                                        fullmatch=True)])
    # 转换权限值
    if noitce_permissions == '是':
        noitce_permissions = 1
    elif noitce_permissions == '否':
        noitce_permissions = 0

    if command_permissions == '是':
        command_permissions = 1
    elif command_permissions == '否':
        command_permissions = 0

    if admin_permissions == '是':
        admin_permissions = 1
    elif admin_permissions == '否':
        admin_permissions = 0

    try:
        # 重新设置权限
        __is_success = \
            await set_group_permissions_to_db(group_id=__group_id, noitce_permissions=noitce_permissions,
                                              command_permissions=command_permissions,
                                              admin_permissions=admin_permissions)
        if not __is_success:
            await session.send('发生了意料之外的错误OvO')
            log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用set_group_permissions'
                               f'更新群组: {session.event.group_id} 时发生错误, 数据库操作失败, 错误信息见日志.')
            return
        await session.send('已成功配置本群组权限~')
        log.logger.info(f'{__name__}: 用户{session.event.user_id} 使用set_group_permissions'
                        f'配置了群组: {session.event.group_id} 的群组权限')
    except Exception as e:
        log.logger.warning(f'{__name__}: 用户{session.event.user_id} 使用命令set_group_permissions时发生错误: {e}, 设置群组权限失败')


@set_group_permissions.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空, 意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if 1 <= len(splited_arg) <= 3:
                # 参数长度有效, 重置session.state值
                session.state['noitce_permissions'] = '否'
                session.state['command_permissions'] = '否'
                session.state['admin_permissions'] = '否'
                for item in splited_arg:
                    if item in ['通知', '命令', '管理命令']:
                        if item == '通知':
                            session.state['noitce_permissions'] = '是'
                        elif item == '命令':
                            session.state['command_permissions'] = '是'
                        elif item == '管理命令':
                            session.state['admin_permissions'] = '是'
                    else:
                        session.finish('没有输入有效的权限名称, 请确认后重新输入命令吧~')
                return
            else:
                session.finish('输入的格式好像不对呢, 请确认后重新输入命令吧~')

    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return
