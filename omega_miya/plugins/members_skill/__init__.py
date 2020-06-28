from nonebot import permission, CommandSession, CommandGroup
from nonebot.command.argfilter import validators, controllers
from omega_miya.plugins.Group_manage.group_permissions import *
from omega_miya.plugins.members_skill.skill_manage import add_skill_to_db, clean_user_skill_in_db, add_user_skill_in_db
from omega_miya.plugins.members_skill.skil_query import query_skill_list, query_my_skill_list

__plugin_name__ = '技能'
__plugin_usage__ = r'''【技能】

使用这个命令可以设置/查询自己的技能

用法：
【不输入参数可进入向导模式】

/添加技能 [技能名称] [技能描述] *只有超管能使用

/查询技能 或 /技能列表

/我的技能

/设置技能 [技能名称] [技能等级] *（会重置已有技能）

/新增技能 [技能名称] [技能等级] 
'''

skill = CommandGroup('Skill')


@skill.command('add_skill', aliases='添加技能', only_to_me=False, permission=permission.SUPERUSER)
async def add_skill(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 从会话状态（session.state）中获取信息，如果当前不存在，则询问用户
    skill_name = session.get('skill_name', prompt='即将向可用技能列表中添加技能，开始新增技能向导~\n请输入技能名称：',
                             arg_filters=[controllers.handle_cancellation(session),
                                          validators.not_empty('输入不能为空')])
    skill_description = session.get('skill_description', prompt='请输入技能描述：',
                                    arg_filters=[controllers.handle_cancellation(session),
                                                 validators.not_empty('输入不能为空')])
    __result = await add_skill_to_db(skill_name, skill_description)
    if __result:
        await session.send(f'已添加技能【{skill_name}】\n\n技能描述：\n{skill_description}')
    else:
        await session.send('添加失败，这个技能好像已经在技能列表中了~')


@add_skill.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if len(splited_arg) == 2:
                session.state['skill_name'] = splited_arg[0]
                session.state['skill_description'] = splited_arg[1]
                return
            else:
                session.finish('输入的格式好像不对呢，请确认后重新输入命令吧~')
                return

    # 用户没有发送有效的参数（而是发送了空白字符），返回向导
    if not stripped_arg:
        return


@skill.command('query_skill', aliases=('查询技能', '技能列表'), only_to_me=False, permission=permission.GROUP)
async def query_skill(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    __result = query_skill_list()
    msg = ''
    for __skill_name in __result:
        msg += f'\n{__skill_name}'
    await session.send(f'目前已有的技能列表如下：\n{msg}')


@skill.command('query_my_skill', aliases='我的技能', only_to_me=False, permission=permission.GROUP)
async def query_my_skill(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    __user_qq = session.event.user_id
    __result = query_my_skill_list(__user_qq)
    msg = ''
    if not __result:
        await session.send('你似乎没有掌握任何技能哦~\n请使用【/设置技能】或者【/新增技能】为自己设置技能吧~')
    else:
        skill_level = ''
        for __skill_list in __result:
            if __skill_list[0] == 1:
                skill_level = '普通'
            elif __skill_list[0] == 2:
                skill_level = '熟练'
            elif __skill_list[0] == 3:
                skill_level = '专业'
            msg += f'\n【{__skill_list[1]}/{skill_level}】'
        await session.send(f'你目前已掌握了以下技能：\n{msg}')


@skill.command('set_my_skill', aliases='设置技能', only_to_me=False, permission=permission.GROUP)
async def set_my_skill(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    __user_qq = session.event.user_id
    # 清空技能列表
    await clean_user_skill_in_db(__user_qq)
    __skill_list = query_skill_list()
    skill_name = session.get('skill_name', prompt='请输入你想设置的技能名称：',
                             arg_filters=[controllers.handle_cancellation(session),
                                          validators.not_empty('输入不能为空')])
    if skill_name not in __skill_list:
        session.finish('没有这个技能哦，请重新设置~')
    skill_level = session.get('skill_level', prompt='请输入你想设置的技能等级：\n可设置等级有"普通"、"熟练"、"专业"',
                              arg_filters=[controllers.handle_cancellation(session),
                                           validators.not_empty('输入不能为空'),
                                           validators.match_regex(r'^(普通|熟练|专业)$', '没有这个技能等级，请重新输入~',
                                                                  fullmatch=True)])
    __result = await add_user_skill_in_db(user_qq=__user_qq, skill_name=skill_name, skill_level=skill_level)
    if __result:
        await session.send(f'为你设置了技能：【{skill_name}/{skill_level}】')
    else:
        await session.send('添加失败，发生了意外的错误QAQ')


@set_my_skill.args_parser
async def _(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if len(splited_arg) == 2 and splited_arg[1] in ['普通', '熟练', '专业']:
                session.state['skill_name'] = splited_arg[0]
                session.state['skill_level'] = splited_arg[1]
                return
            else:
                session.finish('输入的格式好像不对呢，请确认后重新输入命令吧~')

    # 用户没有发送有效的参数（而是发送了空白字符），返回向导
    if not stripped_arg:
        return


@skill.command('add_my_skill', aliases='新增技能', only_to_me=False, permission=permission.GROUP)
async def add_my_skill(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    __user_qq = session.event.user_id
    __skill_list = query_skill_list()
    skill_name = session.get('skill_name', prompt='请输入你想设置的技能名称：',
                             arg_filters=[controllers.handle_cancellation(session),
                                          validators.not_empty('输入不能为空')])
    if skill_name not in __skill_list:
        session.finish('没有这个技能哦，请重新设置~')
    skill_level = session.get('skill_level', prompt='请输入你想设置的技能等级：\n可设置等级有"普通"、"熟练"、"专业"',
                              arg_filters=[controllers.handle_cancellation(session),
                                           validators.not_empty('输入不能为空'),
                                           validators.match_regex(r'^(普通|熟练|专业)$', '没有这个技能等级，请重新输入~',
                                                                  fullmatch=True)])
    __result = await add_user_skill_in_db(user_qq=__user_qq, skill_name=skill_name, skill_level=skill_level)
    if __result:
        await session.send(f'为你新增了技能：【{skill_name}/{skill_level}】')
    else:
        await session.send('添加失败，发生了意外的错误QAQ')


@add_my_skill.args_parser
async def _(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if len(splited_arg) == 2 and splited_arg[1] in ['普通', '熟练', '专业']:
                session.state['skill_name'] = splited_arg[0]
                session.state['skill_level'] = splited_arg[1]
                return
            else:
                session.finish('输入的格式好像不对呢，请确认后重新输入命令吧~')

    # 用户没有发送有效的参数（而是发送了空白字符），返回向导
    if not stripped_arg:
        return
