import nonebot
import re
from aiocqhttp import Event
from omega_miya.plugins.Group_manage.group_permissions import *
from .sp_event import sp_event_check


bot = nonebot.get_bot()

last_msg = {}
last_repeat_msg = {}
repeat_count = {}


@bot.on_message('group')
async def repeater(event: Event):
    group_id = event.group_id

    sp_res, sp_msg = await sp_event_check(event=event)
    if sp_res:
        await bot.send_group_msg(group_id=group_id, message=sp_msg)
        return

    global last_msg, last_repeat_msg, repeat_count

    try:
        last_msg[group_id]
    except KeyError:
        last_msg[group_id] = ''
    try:
        last_repeat_msg[group_id]
    except KeyError:
        last_repeat_msg[group_id] = ''
    """
    if not has_notice_permissions(group_id):
        return
    """
    msg = str(event.raw_message)
    msg = fr'{msg}'
    print(msg)
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
