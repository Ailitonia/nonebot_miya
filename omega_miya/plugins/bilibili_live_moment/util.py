from nonebot import log
from datetime import datetime
from omega_miya.database import *


# 非重复向直播记录绑定表中添加(更新)直播间别名记录
async def add_live_alias_to_db(room_id: int, up_name: str, nickname: str) -> bool:
    exist_room_id = []
    for __res in NONEBOT_DBSESSION.query(Livemomentinfo.room_id). \
            order_by(Livemomentinfo.id). \
            all():
        exist_room_id.append(__res[0])
    if room_id in exist_room_id:
        # up名称有变动则更新表中up名称
        try:
            exist_up_name = []
            for item in NONEBOT_DBSESSION.query(Livemomentinfo.name).filter(Livemomentinfo.room_id == room_id).all():
                exist_up_name.append(item[0])
            if up_name not in exist_up_name:
                __exist_infos = NONEBOT_DBSESSION.query(Livemomentinfo).filter(Livemomentinfo.room_id == room_id).all()
                for __exist_info in __exist_infos:
                    __exist_info.name = up_name
                    __exist_info.updated_at = datetime.now()
                    NONEBOT_DBSESSION.commit()
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_live_alias_to_db ERROR: {e}')
            return False
        # 有新的别名则同样在表新增条目
        try:
            exist_nickname = []
            for item in NONEBOT_DBSESSION.query(Livemomentinfo.nickname).filter(Livemomentinfo.room_id == room_id).all():
                exist_nickname.append(item[0])
            if nickname not in exist_nickname:
                __new_alias = Livemomentinfo(room_id=room_id, name=up_name, nickname=nickname,
                                             created_at=datetime.now())
                NONEBOT_DBSESSION.add(__new_alias)
                NONEBOT_DBSESSION.commit()
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_live_alias_to_db ERROR: {e}')
            return False
        return True
    else:
        try:
            # 没有房间id的向表中添加新条目
            __new_alias = Livemomentinfo(room_id=room_id, name=up_name, nickname=nickname, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_alias)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_live_alias_to_db ERROR: {e}')
            return False


# 返回所有绑定信息的列表
def query_live_alias_list() -> list:
    __result = []
    try:
        for __res in NONEBOT_DBSESSION.query(Livemomentinfo.name, Livemomentinfo.nickname, Livemomentinfo.room_id). \
                order_by(Livemomentinfo.name). \
                all():
            __result.append({'name': __res[0], 'nickname': __res[1], 'room_id': __res[2]})
        return __result
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: query_live_alias_list ERROR: {e}')
        return []


# 从绑定表获取房间号绑定信息的列表
def query_alias_rid_list(nickname: str) -> int:
    try:
        rid = NONEBOT_DBSESSION.query(Livemomentinfo.room_id). \
            filter(Livemomentinfo.nickname == nickname).first()[0]
        if not rid:
            rid = -1
        return rid
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: query_alias_rid_list ERROR: {e}')
        return -1


# 向记录表中写入直播事件记录
async def add_note_to_db(room_id: int, live_title: str, description: str, record_by: int, record_group: int,
                         live_start_time, note_real_time, note_time) -> bool:
    try:
        __new_note = Livemoment(rid=room_id, live_title=live_title, live_start_time=live_start_time,
                                note_real_time=note_real_time, note_time=note_time, description=description,
                                record_by=record_by, record_group=record_group, created_at=datetime.now())
        NONEBOT_DBSESSION.add(__new_note)
        NONEBOT_DBSESSION.commit()
        return True
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_note_to_db ERROR: {e}')
        return False


# 返回所有记录信息
def query_all_notes_list() -> list:
    __result = []
    try:
        for __res in NONEBOT_DBSESSION.query(Livemoment). \
                order_by(Livemoment.id). \
                all():
            '''
            index = {0: 'rid', 1: 'live_title', 2: 'live_start_time', 3: 'note_real_time', 4: 'note_time',
                     5: 'description', 6: 'created_at', 7: 'updated_at'}

            __result.append({'rid': __res.rid, 'live_title': __res.live_title,
                             'live_start_time': __res.live_start_time, 'note_real_time': __res.note_real_time,
                             'note_time': __res.note_time, 'description': __res.description,
                             'created_at': __res.created_at, 'updated_at': __res.updated_at})
            '''
            __result.append({0: __res.rid, 1: __res.live_title, 2: __res.live_start_time, 3: __res.note_real_time,
                             4: __res.note_time, 5: __res.description, 6: __res.created_at, 7: __res.updated_at})
        return __result
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: query_all_notes ERROR: {e}')
        return []
