from nonebot import permission, CommandSession, CommandGroup
from nonebot.command.argfilter import validators, controllers
from omega_miya.plugins.Group_manage.group_manage import \
    add_member_to_db, add_group_to_db, add_member_group_to_db, reset_member_status_to_db, \
    query_group_permissions_in_db, reset_group_permissions_to_db, set_group_permissions_to_db

__plugin_name__ = '群信息管理'
__plugin_usage__ = r'''【群信息管理】

管理员专用
！！请不要轻易使用【/重置成员状态】命令！！
！！请不要轻易使用【/重置群组权限】命令！！

用法：

/刷新(更新)用户信息 *只有超管能使用

/刷新(更新)群组信息 *只有超管能使用

/刷新(更新)群组成员列表 *只有超管能使用

/重置成员状态 *只有超管能使用

/查询群组权限 *只有超管能使用

/设置群组权限 [权限组] *只有超管能使用

/重置群组权限 *只有超管能使用
'''

manage = CommandGroup('Manage')


@manage.command('refresh_member', aliases=('刷新用户信息', '更新用户信息'),
                only_to_me=False, permission=permission.SUPERUSER)
async def refresh_member(session: CommandSession):
    try:
        __group_user_list = await session.bot.get_group_member_list(group_id=session.event.group_id)
    except:
        session.finish('请在群组内使用该命令！')
        return
    for user_info in __group_user_list:
        await add_member_to_db(user_qq=user_info['user_id'], user_nickname=user_info['nickname'])
    await session.send('用户信息已更新~')


@manage.command('refresh_group', aliases=('刷新群组信息', '更新群组信息'),
                only_to_me=False, permission=permission.SUPERUSER)
async def refresh_group(session: CommandSession):
    try:
        __group_info = await session.bot.get_group_info(group_id=session.event.group_id)
    except:
        session.finish('请在群组内使用该命令！')
        return
    await add_group_to_db(group_id=__group_info['group_id'], group_name=__group_info['group_name'])
    await session.send('群组信息已更新~')


@manage.command('refresh_member_group', aliases=('刷新群组成员列表', '更新群组成员列表'),
                only_to_me=False, permission=permission.SUPERUSER)
async def refresh_member_group(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_user_list = await session.bot.get_group_member_list(group_id=__group_id)
    except:
        session.finish('请在群组内使用该命令！')
        return
    for user_info in __group_user_list:
        __user_qq = user_info['user_id']
        __user_group_info = await session.bot.get_group_member_info(group_id=__group_id, user_id=__user_qq)
        __user_group_nickmane = __user_group_info['card']
        if not __user_group_nickmane:
            __user_group_nickmane = __user_group_info['nickname']
        await add_member_group_to_db(user_qq=__user_qq, group_id=__group_id, user_group_nickmane=__user_group_nickmane)
    await session.send('群组群组成员列表已更新~')


@manage.command('reset_member_status', aliases='重置成员状态',
                only_to_me=False, permission=permission.SUPERUSER)
async def reset_member_status(session: CommandSession):
    try:
        __group_user_list = await session.bot.get_group_member_list(group_id=session.event.group_id)
    except:
        session.finish('请在群组内使用该命令！')
        return
    for user_info in __group_user_list:
        await reset_member_status_to_db(user_qq=user_info['user_id'])
    await session.send('成员状态已重置~')


@manage.command('query_group_permissions', aliases='查询群组权限',
                only_to_me=False, permission=permission.SUPERUSER)
async def query_group_permissions(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_info = await session.bot.get_group_info(group_id=__group_id)
    except:
        session.finish('请在群组内使用该命令！')
        return
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
        await session.send(f'本群组已配置如下权限：\n{msg}')


@manage.command('reset_group_permissions', aliases='重置群组权限',
                only_to_me=False, permission=permission.SUPERUSER)
async def reset_group_permissions(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_info = await session.bot.get_group_info(group_id=__group_id)
    except:
        session.finish('请在群组内使用该命令！')
        return
    await reset_group_permissions_to_db(group_id=__group_id)
    await session.send('本群组权限已重置~')


@manage.command('set_group_permissions', aliases='设置群组权限',
                only_to_me=False, permission=permission.SUPERUSER)
async def set_group_permissions(session: CommandSession):
    try:
        __group_id = session.event.group_id
        __group_info = await session.bot.get_group_info(group_id=__group_id)
    except:
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

    # 重新设置权限
    await set_group_permissions_to_db(group_id=__group_id, noitce_permissions=noitce_permissions,
                                      command_permissions=command_permissions, admin_permissions=admin_permissions)
    await session.send('已成功配置本群组权限~')


@set_group_permissions.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if 1 <= len(splited_arg) <= 3:
                # 参数长度有效，重置session.state值
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
                        session.finish('没有输入有效的权限名称，请确认后重新输入命令吧~')
                return
            else:
                session.finish('输入的格式好像不对呢，请确认后重新输入命令吧~')

    # 用户没有发送有效的参数（而是发送了空白字符），返回向导
    if not stripped_arg:
        return
