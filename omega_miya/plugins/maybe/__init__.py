from nonebot import on_command, CommandSession, permission
from .get_divination_of_thing import get_divination_of_thing
from omega_miya.plugins.Group_manage.group_permissions import *


__plugin_name__ = '求签'
__plugin_usage__ = r'''【求签】

使用这个命令可以对任何事求运势，包括且不限于吃饭、睡懒觉、DD

用法：
/求签 [所求之事]'''


# on_command 装饰器将函数声明为一个命令处理器
@on_command('maybe', aliases='求签', only_to_me=False, permission=permission.GROUP)
async def maybe(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 从会话状态（session.state）中获取事项，如果当前不存在，则询问用户
    divination = session.get('divination', prompt='你想问什么事呢？')
    # 求签者昵称
    divination_user = dict(session.event.items())['sender']['nickname']
    # 求签
    divination_result = await get_divination_of_thing(divination, divination_user)
    # 向用户发送结果
    await session.send(divination_result)


# 》args_parser 装饰器将函数声明为命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@maybe.args_parser
async def _(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
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
        # 用户没有发送有效的字符（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('你还没告诉我你想问什么事呢~')

    # 如果当前正在向用户询问更多信息（例如本例中的要查询的城市），且用户输入有效，则放入会话状态
    session.state[session.current_key] = stripped_arg
