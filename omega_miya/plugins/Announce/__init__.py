from omega_miya.plugins.Group_manage.group_permissions import *
from nonebot import on_command, CommandSession, permission, log
from nonebot.command.argfilter import validators, controllers


@on_command('announce', aliases=('公告', '发布公告'),
            only_to_me=True, permission=permission.SUPERUSER)
async def announce(session: CommandSession):
    __group_id = session.get('group_id', prompt='请输入你想通知的群号: ',
                             arg_filters=[controllers.handle_cancellation(session),
                                          validators.not_empty('输入不能为空'),
                                          validators.match_regex(r'^\d+$', '格式不对, 请重新输入~', fullmatch=True)])
    __group_id = int(__group_id)
    if __group_id == 1:
        __announce_text = session.get('announce_text', prompt='【全局公告】请输入你想发布的公告内容: ',
                                      arg_filters=[controllers.handle_cancellation(session),
                                                   validators.not_empty('输入不能为空')])
        for group_id in query_all_notice_groups():
            try:
                await session.bot.send_group_msg(group_id=group_id, message=__announce_text)
                log.logger.info(f'{__name__}: 已向群组: {__group_id} 发送通知')
            except Exception as e:
                log.logger.error(f'{__name__}: 向群组: {__group_id} 发送通知失败, error info: {e}')
                continue
        return
    elif __group_id not in query_all_notice_groups():
        log.logger.info(f'{__name__}: 群组: {__group_id} 没有通知权限, 无法发送通知')
        await session.send('群组未配置通知权限！')
        return
    __announce_text = session.get('announce_text', prompt='请输入你想发布的公告内容: ',
                                  arg_filters=[controllers.handle_cancellation(session),
                                               validators.not_empty('输入不能为空')])
    try:
        await session.bot.send_group_msg(group_id=__group_id, message=__announce_text)
        log.logger.info(f'{__name__}: 已向群组: {__group_id} 发送通知')
    except Exception as e:
        log.logger.error(f'{__name__}: 向群组: {__group_id} 发送通知失败, error info: {e}')


@announce.args_parser
async def _(session: CommandSession):
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            session.finish('该命令不支持参数~')

    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return
