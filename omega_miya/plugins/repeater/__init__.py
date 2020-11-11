import nonebot
import re
from aiocqhttp import Event
from omega_miya.plugins.Group_manage.group_permissions import *


bot = nonebot.get_bot()

last_msg = {}
last_repeat_msg = {}
repeat_count = {}


@bot.on_message('group')
async def repeater(event: Event):
    global last_msg, last_repeat_msg, repeat_count

    group_id = event.group_id

    try:
        last_msg[group_id]
    except KeyError:
        last_msg[group_id] = ''
    try:
        last_repeat_msg[group_id]
    except KeyError:
        last_repeat_msg[group_id] = ''

    if not has_notice_permissions(group_id):
        return
    msg = str(event.message)
    msg = fr'{msg}'
    if re.match(r'^/', msg):
        return

    if msg != last_msg[group_id] or msg == last_repeat_msg[group_id]:
        last_msg[group_id] = msg
        repeat_count[group_id] = 0
        return
    else:
        repeat_count[group_id] += 1
        last_repeat_msg[group_id] = ''
        if repeat_count[group_id] >= 2:
            await bot.send_group_msg(group_id=group_id, message=msg)
            repeat_count[group_id] = 0
            last_msg[group_id] = ''
            last_repeat_msg[group_id] = msg
