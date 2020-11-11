import nonebot
from aiocqhttp import Event
from nonebot import log
from omega_miya.database import *
from datetime import datetime

bot = nonebot.get_bot()


@bot.on_message()
async def message_history(event: Event):
    try:
        time = event['time']
        self_id = event['self_id']
        post_type = event.type
        if post_type == 'message':
            detail_type = event.detail_type
            if detail_type == 'group':
                sub_type = event.sub_type
                group_id = event.group_id
                user_id = event.user_id
                user_name = event['sender']['card']
                if not user_name:
                    user_name = event['sender']['nickname']
            else:
                sub_type = event.sub_type
                group_id = event.group_id
                user_id = event.user_id
                user_name = event['sender']['nickname']

            raw_data = str(event.raw_message)
            msg_data = str(event.message)
            created_at = datetime.now()
        else:
            return
    except Exception as e:
        log.logger.warning(f'{__name__}: message event error: {e}, failed to read message event.')
        return

    try:
        new_event = History(time=time, self_id=self_id, post_type=post_type, detail_type=detail_type, sub_type=sub_type,
                            group_id=group_id, user_id=user_id, user_name=user_name,
                            raw_data=raw_data, msg_data=msg_data, created_at=created_at)
        NONEBOT_DBSESSION.add(new_event)
        NONEBOT_DBSESSION.commit()
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}, failed to add message event info.')


@bot.on_notice()
async def notice_history(event: Event):
    try:
        time = event['time']
        self_id = event['self_id']
        post_type = event['post_type']
        if post_type == 'notice':
            detail_type = event['notice_type']
            try:
                sub_type = event['sub_type']
            except (KeyError, TypeError):
                sub_type = None
            try:
                group_id = event['group_id']
            except (KeyError, TypeError):
                group_id = None
            try:
                user_id = event['user_id']
            except (KeyError, TypeError):
                user_id = None
            user_name = None
            raw_data = None
            created_at = datetime.now()
        else:
            return
    except Exception as e:
        log.logger.warning(f'{__name__}: notice event error: {e}, failed to read notice event.')
        return

    try:
        new_event = History(time=time, self_id=self_id, post_type=post_type, detail_type=detail_type, sub_type=sub_type,
                            group_id=group_id, user_id=user_id, user_name=user_name,
                            raw_data=raw_data, created_at=created_at)
        NONEBOT_DBSESSION.add(new_event)
        NONEBOT_DBSESSION.commit()
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}, failed to add notice event info.')
