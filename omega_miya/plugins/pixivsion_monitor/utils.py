import aiohttp
from nonebot import log
from datetime import datetime
from omega_miya.database import *
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


async def fetch(url: str, paras: dict) -> dict:
    timeout_count = 0
    while timeout_count < 6:
        try:
            timeout = aiohttp.ClientTimeout(total=20)
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
        return {'error': True}


# 图片转base64
async def illust_image_2_base64(pid: int):
    api_key = '123456abc'
    search_api_url = 'https://api.example.com'
	# !!!这里使用了另外一个用于下载p站图片私人api!!!
    __payload = {'key': api_key, 'pid': pid}
    illustinfo = await fetch(url=search_api_url, paras=__payload)
    if 'error' in illustinfo.keys():
        log.logger.warning(f'{__name__}: illust_image_2_base64 ERROR: Timeout or other error')
        return None
    else:
        return illustinfo['pic_b64']


# 非重复向订阅表中添加(更新)群组的Pixivsion订阅
async def add_pixivsion_sub_to_db(group_id: int) -> bool:
    group_id = int(group_id)

    # 检查订阅表中pixivsion项, 没有则添加
    try:
        __sub_table_id = NONEBOT_DBSESSION.query(Subscription.id).\
            filter(Subscription.sub_id == -1).filter(Subscription.sub_type == 8).one()
    except NoResultFound:
        try:
            __new_sub = Subscription(sub_id=-1, sub_type=8, up_name='pixivsion', created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_sub)
            NONEBOT_DBSESSION.commit()
            __sub_table_id = NONEBOT_DBSESSION.query(Subscription.id).\
                filter(Subscription.sub_id == -1).filter(Subscription.sub_type == 8).one()
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_pixivsion_sub_to_db, DBSESSION ERROR, error info: {e}, '
                             f'fail to add pixivision sub')
            return False
    except Exception as e:
        log.logger.error(f'{__name__}: add_pixivsion_sub_to_db, DBSESSION ERROR, error info: {e}.')
        return False

    # 检查qq群是否在表中，查这个群组在群组表中的id(不是群号)
    try:
        __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: add_pixivsion_sub_to_db ERROR: Group NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_pixivsion_sub_to_db ERROR: {e}, in checking group')
        return False

    # 查询订阅-群组表中订阅-群关系
    try:
        # 若群组已经订阅则更新信息
        __exist_sub = NONEBOT_DBSESSION.query(GroupSub). \
            filter(GroupSub.sub_id == __sub_table_id).\
            filter(GroupSub.group_id == __group_table_id).one()
        # 更新订阅信息(暂留)
        # __exist_sub.group_sub_info
        __exist_sub.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 若群组没有订阅则新增订阅信息
        try:
            __new_sub = GroupSub(sub_id=__sub_table_id, group_id=__group_table_id, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_sub)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_pixivsion_sub_to_db, DBSESSION ERROR, error info: {e}, '
                             f'failed to add group pixivision sub.')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: add_pixivsion_sub_to_db ERROR: MultipleResultsFound, '
                         f'sub_id: {-1}, group_id: {group_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_pixivsion_sub_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 清空某群组的pixivision订阅
async def clean_group_pixivsion_sub_in_db(group_id) -> bool:
    group_id = int(group_id)

    # 检查订阅表中pixivsion项
    try:
        __sub_table_id = NONEBOT_DBSESSION.query(Subscription.id).\
            filter(Subscription.sub_id == -1).filter(Subscription.sub_type == 8).one()
    except NoResultFound:
        # 没有则说明还没有添加过pixivision的订阅
        return True
    except Exception as e:
        log.logger.error(f'{__name__}: clean_group_pixivsion_sub_in_db, DBSESSION ERROR, error info: {e}.')
        return False

    # 检查qq群是否在表中，查这个群组在群组表中的id(不是群号)
    try:
        __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: clean_group_pixivsion_sub_in_db ERROR: group NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: clean_group_pixivsion_sub_in_db ERROR: {e}, in checking group')
        return False

    # 删除订阅表中这个群组的pixivision订阅
    try:
        __group_sub = NONEBOT_DBSESSION.query(GroupSub).\
            filter(GroupSub.sub_id == __sub_table_id).\
            filter(GroupSub.group_id == __group_table_id).one()
        NONEBOT_DBSESSION.delete(__group_sub)
        NONEBOT_DBSESSION.commit()
    except NoResultFound:
        # 没有则说明还没有添加过pixivision的订阅
        return True
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: clean_group_pixivsion_sub_in_db, DBSESSION ERROR, error info: {e}.')
        return False
    return True


def add_pixivsion_article_to_db(aid: int, title: str, description: str, tags: str, illust_id: str, url: str) -> bool:
    try:
        NONEBOT_DBSESSION.query(Pixivsion.aid).filter(Pixivsion.aid == aid).one()
    except NoResultFound:
        try:
            __new_illust = Pixivsion(aid=aid, title=title, description=description,
                                     tags=tags, illust_id=illust_id, url=url, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_illust)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_pixivsion_article_to_db, DBSESSION ERROR, error info: {e}.')
            return False
    except Exception as e:
        log.logger.error(f'{__name__}: add_pixivsion_article_to_db, DBSESSION ERROR, error info: {e}.')
        return False


def get_pixivsion_article_id_list() -> list:
    aid_list = NONEBOT_DBSESSION.query(Pixivsion.aid).order_by(Pixivsion.id).all()
    __res = []
    for item in aid_list:
        __res.append(item[0])
    return __res


# 查询订阅了Pixivsion的所有群组
def query_group_whick_sub_pixivsion() -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Group.group_id). \
            join(GroupSub).join(Subscription). \
            filter(GroupSub.group_id == Group.id). \
            filter(Subscription.id == GroupSub.sub_id). \
            filter(Subscription.sub_type == 8). \
            order_by(Group.id). \
            all():
        __result.append(__res[0])
    return __result
