import re
import aiohttp
from nonebot import log
from datetime import datetime
from omega_miya.plugins.bilibili_live_monitor.config import *
from omega_miya.database import *


async def fetch(url: str, paras: dict) -> dict:
    timeout_count = 0
    while timeout_count < 3:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                async with session.get(url=url, params=paras, headers=headers, timeout=timeout) as resp:
                    __json = await resp.json()
            return __json
        except Exception as e:
            log.logger.warning(f'{__name__}: fetch ERROR: {e}. '
                               f'Occurred in try {timeout_count + 1} using paras: {paras}')
        finally:
            timeout_count += 1
    else:
        log.logger.warning(f'{__name__}: fetch ERROR: Timeout {timeout_count}, using paras: {paras}')
        return {'error': 'error'}


# 查询这个直播间是否在订阅表中
def is_live_sub_exist(live_id) -> bool:
    __result = NONEBOT_DBSESSION.query(Subscription.sub_id). \
        filter(Subscription.sub_type == 1). \
        filter(Subscription.sub_id == live_id). \
        first()
    if __result:
        return True
    else:
        return False


# 返回所有直播间房间号的列表
def query_live_sub_list() -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Subscription.sub_id). \
            filter(Subscription.sub_type == 1). \
            order_by(Subscription.id). \
            all():
        __result.append(__res[0])
    return __result


# 非重复向订阅表中添加(更新)直播间订阅
async def add_live_sub_to_db(sub_id, up_name) -> bool:
    sub_id = int(sub_id)
    up_name = re.sub(r'\W+', '', up_name)
    exist_live_sub = query_live_sub_list()
    if sub_id in exist_live_sub:
        # up名称有变动则更新订阅表中up名称
        if not up_name == NONEBOT_DBSESSION.query(Subscription.up_name). \
                filter(Subscription.sub_type == 1). \
                filter(Subscription.sub_id == sub_id).first()[0]:
            try:
                __exist_sub = NONEBOT_DBSESSION.query(Subscription).filter(Subscription.sub_id == sub_id).first()
                __exist_sub.up_name = up_name
                __exist_sub.updated_at = datetime.now()
                NONEBOT_DBSESSION.commit()
                return True
            except Exception as e:
                NONEBOT_DBSESSION.rollback()
                log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
                return False
        return True
    else:
        # 订阅表中添加新订阅
        try:
            __new_sub = Subscription(sub_id=sub_id, sub_type=1, up_name=up_name, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_sub)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
            return False


# 非重复为群组添加(更新)直播间订阅
async def add_group_live_sub_to_db(sub_id, group_id) -> bool:
    sub_id = int(sub_id)
    # 不在订阅表中的房间号群跳过
    if not is_live_sub_exist(sub_id):
        return False
    __exist_group_id = []
    for res in NONEBOT_DBSESSION.query(Group.group_id).order_by(Group.id).all():
        __exist_group_id.append(res[0])
    # 不在群组表中的qq群跳过
    if group_id not in __exist_group_id:
        return False
    # 查这个订阅在订阅表中的id（不是房间号）
    __sub_table_id = NONEBOT_DBSESSION.query(Subscription.id).filter(Subscription.sub_id == sub_id).first()[0]
    # 查这个群组在群组表中的id（不是群号）
    __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).first()[0]
    # 查询订阅-群组表中所有订阅的房间号, 这个人订阅-群关系已存在
    __result = []
    for __res in NONEBOT_DBSESSION.query(Subscription.sub_id). \
            join(GroupSub).join(Group). \
            filter(Subscription.id == GroupSub.sub_id). \
            filter(GroupSub.group_id == Group.id). \
            filter(Group.group_id == group_id). \
            order_by(Subscription.id).all():
        __result.append(__res[0])
    # 群组-成员表里面这个订阅-群关系已存在, 更新信息
    if sub_id in __result:
        try:
            __exist_sub = NONEBOT_DBSESSION.query(GroupSub).filter(GroupSub.sub_id == __sub_table_id).first()
            # __exist_sub.group_sub_info 更新订阅信息（暂留）
            __exist_sub.updated_at = datetime.now()
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
            return False
    # 群组-成员表里面这个订阅-群关系不存在, 更新订阅-群组关联
    else:
        # 添加新订阅
        try:
            __new_sub = GroupSub(sub_id=__sub_table_id, group_id=__group_table_id, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_sub)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
            return False


# 查询某群组订阅的所有直播间的房间号
async def query_group_live_sub_list(group_id) -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Subscription.sub_id). \
            join(GroupSub).join(Group). \
            filter(Subscription.id == GroupSub.sub_id). \
            filter(GroupSub.group_id == Group.id). \
            filter(Subscription.sub_type == 1). \
            filter(Group.group_id == group_id). \
            order_by(Subscription.id). \
            all():
        __result.append(__res[0])
    return __result


# 查询订阅了某直播间的所有群组
async def query_group_whick_sub_live(sub_id) -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Group.group_id). \
            join(GroupSub).join(Subscription). \
            filter(GroupSub.group_id == Group.id). \
            filter(Subscription.id == GroupSub.sub_id). \
            filter(Subscription.sub_type == 1). \
            filter(Subscription.sub_id == sub_id). \
            order_by(Group.id). \
            all():
        __result.append(__res[0])
    return __result


# 清空某群组的直播间订阅
async def clean_group_live_sub_in_db(group_id) -> bool:
    for __res_sub_id, __res_group_id in NONEBOT_DBSESSION.query(Subscription.sub_id, GroupSub.id). \
            join(GroupSub).join(Group). \
            filter(Subscription.id == GroupSub.sub_id). \
            filter(GroupSub.group_id == Group.id). \
            filter(Subscription.sub_type == 1). \
            filter(Group.group_id == group_id). \
            order_by(Subscription.id). \
            all():
        try:
            __group_sub = NONEBOT_DBSESSION.query(GroupSub).filter(GroupSub.id == __res_group_id).first()
            NONEBOT_DBSESSION.delete(__group_sub)
            NONEBOT_DBSESSION.commit()
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
            return False
    return True


# 初始化直播间状态
async def init_live_status(room_id) -> int:
    url = LIVE_API_URL
    payload = {'id': room_id}
    live_status = await fetch(url=url, paras=payload)
    return int(live_status['data']['live_status'])


# 初始化直播间标题
async def init_live_title(room_id) -> str:
    url = LIVE_API_URL
    payload = {'id': room_id}
    live_title = await fetch(url=url, paras=payload)
    return str(live_title['data']['title'])


# 获取直播间信息
async def get_live_info(room_id) -> dict:
    url = LIVE_API_URL
    payload = {'id': room_id}
    live_info = await fetch(url=url, paras=payload)
    if live_info['code'] != 0:
        return dict({'status': 'error'})
    return dict({'status': live_info['data']['live_status'], 'url': LIVE_URL + str(room_id),
                 'title': live_info['data']['title'], 'time': live_info['data']['live_time'],
                 'uid': live_info['data']['uid']})


# 根据用户uid获取用户信息
async def get_user_info(user_id) -> dict:
    url = USER_INFO_API_URL
    payload = {'mid': user_id}
    user_info = await fetch(url=url, paras=payload)
    if user_info['code'] != 0:
        return dict({'status': 'error'})
    return dict({'status': user_info['code'], 'name': user_info['data']['name']})
