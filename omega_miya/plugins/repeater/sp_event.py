from aiocqhttp import Event

sp_event = {
    '喵喵喵': {'enable': True, 'group_id': [1121459110], 'replyMsg': '不要喵喵喵'},
    '小母猫': {'enable': True, 'group_id': [651124267], 'replyMsg': '喵喵喵'}
}


async def sp_event_check(event: Event) -> (bool, str):
    msg = event.raw_message
    group_id = event.group_id
    if msg in sp_event.keys():
        if sp_event.get(msg).get('enable') and group_id in sp_event.get(msg).get('group_id'):
            msg = sp_event.get(msg).get('replyMsg')
            return True, msg
        else:
            return False, ''
    else:
        return False, ''
