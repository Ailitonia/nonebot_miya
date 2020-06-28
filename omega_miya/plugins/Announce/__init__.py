from omega_miya.plugins.Group_manage.group_permissions import *
from nonebot import on_command, CommandSession, permission
from nonebot.command.argfilter import validators, controllers


@on_command('announce', aliases=('公告', '发布公告'),
            only_to_me=True, permission=permission.SUPERUSER)
async def announce(session: CommandSession):
    __group_id = session.get('group_id', prompt='请输入你想通知的群号：',
                             arg_filters=[controllers.handle_cancellation(session),
                                          validators.not_empty('输入不能为空'),
                                          validators.match_regex(r'^\d+$', '格式不对，请重新输入~', fullmatch=True)])
    if int(__group_id) not in query_all_noitce_groups():
        session.finish('群组未配置通知权限！')
        return
    __announce_text = session.get('announce_text', prompt='请输入你想发布的公告内容：',
                                  arg_filters=[controllers.handle_cancellation(session),
                                               validators.not_empty('输入不能为空')])
    await session.bot.send_group_msg(group_id=__group_id, message=__announce_text)


@announce.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            session.finish('该命令不支持参数~')

    # 用户没有发送有效的参数（而是发送了空白字符），返回向导
    if not stripped_arg:
        return
