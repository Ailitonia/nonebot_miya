import nonebot
from nonebot import on_command, CommandSession, permission
from omega_miya.plugins.Group_manage.group_permissions import *


'''
使用__plugin_name__ 和 __plugin_usage__ 特殊变量设置
插件的名称和使用方法
'''


@on_command('help', aliases=['使用帮助', '帮助'], only_to_me=False, permission=permission.GROUP)
async def _(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 获取设置了名称的插件列表
    plugins = list(filter(lambda p: p.name, nonebot.get_loaded_plugins()))

    arg = session.current_arg_text.strip().lower()
    if not arg:
        # 如果用户没有发送参数，则发送功能列表
        await session.send(
            '我现在支持的功能有：\n\n' + '\n'.join(p.name for p in plugins) + '\n\n输入"/help [功能名]"即可查看对应帮助')
        return

    # 如果发了参数则发送相应命令的使用帮助
    for p in plugins:
        if p.name.lower() == arg:
            await session.send(p.usage)
