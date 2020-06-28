import nonebot
from aiocqhttp import Event
from omega_miya.plugins.Group_manage.group_permissions import *

bot = nonebot.get_bot()

last_msg = ''
repeat_count = 0


@bot.on_message('group')
async def repeater(event: Event):
    global last_msg, repeat_count
    group_id = event.group_id
    if group_id not in query_all_command_groups():
        return
    msg = str(event.message)
    if msg != last_msg:
        last_msg = msg
        repeat_count = 0
        return
    else:
        repeat_count += 1
        if repeat_count >= 2:
            await bot.send_group_msg(group_id=group_id, message=msg)
            repeat_count = 0
            last_msg = ''
