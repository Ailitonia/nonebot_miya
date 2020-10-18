import zhdate
from nonebot import on_command, CommandSession, permission, log
from .get_divination_of_thing import get_divination_of_thing
from omega_miya.plugins.Group_manage.group_permissions import *


__plugin_name__ = '求签'
__plugin_usage__ = r'''【求签】

使用这个命令可以对任何事求运势, 包括且不限于吃饭、睡懒觉、DD

用法: 
/求签 [所求之事]'''


# on_command 装饰器将函数声明为一个命令处理器
@on_command('maybe', aliases='求签', only_to_me=False, permission=permission.EVERYBODY)
async def maybe(session: CommandSession):
    group_id = session.event.group_id
    user_id = session.event.user_id
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
    # 从会话状态（session.state）中获取事项, 如果当前不存在, 则询问用户
    divination = session.get('divination', prompt='你想问什么事呢？')
    try:
        # 求签者昵称
        divination_user = dict(session.event.items())['sender']['nickname']
        # 求签
        divination_result = await get_divination_of_thing(divination=divination, divination_user=user_id)
        # 向用户发送结果
        date_luna = zhdate.ZhDate.today().chinese()
        msg = f'今天是{date_luna}\n{divination_user}所求事项: 【{divination}】\n\n结果: 【{divination_result}】'
        await session.send(msg)
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令maybe时发生了错误: {e}')


# args_parser 装饰器将函数声明为命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@maybe.args_parser
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
            session.state['divination'] = stripped_arg
        return

    if not stripped_arg:
        # 用户没有发送有效的字符（而是发送了空白字符）, 则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('你还没告诉我你想问什么事呢~')

    # 如果当前正在向用户询问更多信息（例如本例中的要查询的城市）, 且用户输入有效, 则放入会话状态
    session.state[session.current_key] = stripped_arg
