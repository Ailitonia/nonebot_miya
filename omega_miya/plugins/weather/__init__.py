from nonebot import on_command, CommandSession
from omega_miya.plugins.Group_manage.group_permissions import *
from .get_weather import get_weather_of_city

__plugin_name__ = '天气'
__plugin_usage__ = r'''【天气】
命令别名：weather/天气/天气预报

使用这个命令可以查询某个城市的实时天气

用法：
/天气 [城市名称]'''


# on_command 装饰器将函数声明为一个命令处理器
# 这里 weather 为命令的名字，同时允许使用别名「天气」「天气预报」
@on_command('weather', aliases=('天气', '天气预报'), only_to_me=False)
async def weather(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 从会话状态（session.state）中获取城市名称（city），如果当前不存在，则询问用户
    city = session.get('city', prompt='你想知道哪个城市的天气呢？')
    # 获取城市的天气预报
    weather_report = await get_weather_of_city(city)
    # 向用户发送天气预报
    if weather_report == 'error':
        await session.send('没有这个城市，你是不是手滑输错了？')
    # 返回正常天气
    else:
        await session.send(weather_report)


# weather.args_parser 装饰器将函数声明为 weather 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@weather.args_parser
async def _(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空，意味着用户直接将城市名跟在命令名后面，作为参数传入
            # 例如用户可能发送了：天气 南京
            session.state['city'] = stripped_arg
        return

    if not stripped_arg:
        # 用户没有发送有效的城市名称（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('你还没告诉我你想知道哪个城市的天气呢~')

    # 如果当前正在向用户询问更多信息（例如本例中的要查询的城市），且用户输入有效，则放入会话状态
    session.state[session.current_key] = stripped_arg
