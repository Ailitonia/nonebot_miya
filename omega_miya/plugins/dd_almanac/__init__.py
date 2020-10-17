from nonebot import on_command, CommandSession, permission, log
from .get_almanac_for_dd import get_almanac_for_dd
from omega_miya.plugins.Group_manage.group_permissions import *


__plugin_name__ = 'DD老黄历'
__plugin_usage__ = r'''【DD老黄历】
命令别名: DD老黄历/dd老黄历

使用这个命令可以查看今日黄历（DD版）

默认查看自己的
用法: 
/DD老黄历
/DD老黄历 [昵称]'''


# on_command 装饰器将函数声明为一个命令处理器
@on_command('almanac', aliases=('DD老黄历', 'dd老黄历'), only_to_me=False, permission=permission.EVERYBODY)
async def almanac(session: CommandSession):
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
    dd_almanac = session.state['whos_almanac']
    try:
        # 看黄历
        almanac_result = await get_almanac_for_dd(user=dd_almanac)
        # 向用户发送结果
        await session.send(almanac_result)
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令almanac时发生了错误: {e}')


# args_parser 装饰器将函数声明为命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@almanac.args_parser
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
            # 第一次运行参数不为空
            session.state['whos_almanac'] = stripped_arg
        elif not stripped_arg:
            # 参数为空则把用户昵称作为默认参数
            session.state['whos_almanac'] = dict(session.event.items())['sender']['nickname']
        return
