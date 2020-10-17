import aiohttp
import json
from nonebot import log
from datetime import datetime
from omega_miya.plugins.bilibili_dynamic_monitor.config import *
from omega_miya.database import *
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


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
        log.logger.warning(f'{__name__}: fetch ERROR: Exceeds the set timeout time. '
                           f'Timeout {timeout_count}, using paras: {paras}')
        return {'error': 'error'}


# 查询这个up的动态是否在订阅表中
def is_dy_sub_exist(user_id) -> bool:
    try:
        NONEBOT_DBSESSION.query(Subscription.sub_id).\
            filter(Subscription.sub_type == 2).\
            filter(Subscription.sub_id == user_id).one()
        return True
    except NoResultFound:
        log.logger.warning(f'{__name__}: is_dy_sub_exist ERROR: NoResultFound.')
        return False
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: is_dy_sub_exist ERROR: MultipleResultsFound, user_id: {user_id}.')
        return True


# 返回所有的动态的UP的uid的列表
def query_dy_sub_list() -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Subscription.sub_id). \
            filter(Subscription.sub_type == 2). \
            order_by(Subscription.id). \
            all():
        __result.append(__res[0])
    return __result


# 非重复向订阅表中添加(更新)动态订阅
async def add_dy_sub_to_db(sub_id, up_name) -> bool:
    sub_id = int(sub_id)
    up_name = str(up_name)
    # 若存在则更新订阅表中up名称
    try:
        __exist_sub = NONEBOT_DBSESSION.query(Subscription). \
            filter(Subscription.sub_type == 2). \
            filter(Subscription.sub_id == sub_id).one()
        __exist_sub.up_name = up_name
        __exist_sub.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在则添加新订阅
        try:
            __new_sub = Subscription(sub_id=sub_id, sub_type=2, up_name=up_name, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_sub)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_dy_sub_to_db, DBSESSION ERROR, error info: {e}.')
            return False
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: add_dy_sub_to_db ERROR: MultipleResultsFound, sub_id: {sub_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_dy_sub_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 非重复为群组添加(更新)动态订阅
async def add_group_dy_sub_to_db(sub_id, group_id) -> bool:
    sub_id = int(sub_id)

    # 检查订阅是否在表中，查这个订阅在订阅表中的id(不是用户uid)
    try:
        __sub_table_id = NONEBOT_DBSESSION.query(Subscription.id).\
            filter(Subscription.sub_type == 2).\
            filter(Subscription.sub_id == sub_id).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: add_group_dy_sub_to_db ERROR: Group NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_group_dy_sub_to_db ERROR: {e}, in checking sub')
        return False

    # 检查qq群是否在表中，查这个群组在群组表中的id(不是群号)
    try:
        __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: add_group_dy_sub_to_db ERROR: Group NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_group_dy_sub_to_db ERROR: {e}, in checking group')
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
            log.logger.error(f'{__name__}: add_group_dy_sub_to_db, DBSESSION ERROR, error info: {e}, '
                             f'failed to add new sub.')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: add_group_dy_sub_to_db ERROR: MultipleResultsFound, '
                         f'sub_id: {sub_id}, group_id: {group_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_group_dy_sub_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 查询某群组订阅的所有动态的UP的uid
async def query_group_dy_sub_list(group_id) -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Subscription.sub_id). \
            join(GroupSub).join(Group). \
            filter(Subscription.id == GroupSub.sub_id). \
            filter(GroupSub.group_id == Group.id). \
            filter(Subscription.sub_type == 2). \
            filter(Group.group_id == group_id). \
            order_by(Subscription.id). \
            all():
        __result.append(__res[0])
    return __result


# 查询订阅了某UP动态的所有群组
async def query_group_whick_sub_dy(sub_id) -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Group.group_id). \
            join(GroupSub).join(Subscription). \
            filter(GroupSub.group_id == Group.id). \
            filter(Subscription.id == GroupSub.sub_id). \
            filter(Subscription.sub_type == 2). \
            filter(Subscription.sub_id == sub_id). \
            order_by(Group.id). \
            all():
        __result.append(__res[0])
    return __result


# 清空某群组的动态订阅
async def clean_group_dy_sub_in_db(group_id) -> bool:
    for __res_groupsub_id in NONEBOT_DBSESSION.query(GroupSub.id).join(Subscription).join(Group).\
            filter(GroupSub.sub_id == Subscription.id).\
            filter(GroupSub.group_id == Group.id).\
            filter(Subscription.sub_type == 2).\
            filter(Group.group_id == group_id).\
            order_by(Subscription.id).all():
        try:
            __group_sub = NONEBOT_DBSESSION.query(GroupSub).filter(GroupSub.id == __res_groupsub_id).one()
            NONEBOT_DBSESSION.delete(__group_sub)
            NONEBOT_DBSESSION.commit()
        except NoResultFound:
            log.logger.warning(f'{__name__}: clean_group_dy_sub_in_db ERROR: NoResultFound, '
                               f'groupsub_id: {__res_groupsub_id}.')
            continue
        except MultipleResultsFound:
            log.logger.warning(f'{__name__}: clean_group_dy_sub_in_db ERROR: MultipleResultsFound, '
                               f'groupsub_id: {__res_groupsub_id}.')
            continue
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: clean_group_dy_sub_in_db, DBSESSION ERROR, '
                             f'error info: {e}, groupsub_id: {__res_groupsub_id}.')
            continue
    return True


# 返回某个up的所有动态id的列表
def query_up_dy_id_list(user_id) -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Bilidynamic.dynamic_id). \
            filter(Bilidynamic.uid == user_id). \
            order_by(Bilidynamic.id). \
            all():
        __result.append(__res[0])
    return __result


# 非重复向动态表中添加(更新)动态信息
async def add_dy_info_to_db(user_id, dynamic_id, dynamic_type, content) -> bool:
    user_id = int(user_id)
    dynamic_id = int(dynamic_id)
    dynamic_type = int(dynamic_type)
    content = str(content)

    try:
        NONEBOT_DBSESSION.query(Bilidynamic).filter(Bilidynamic.dynamic_id == dynamic_id).one()
        return True
    except NoResultFound:
        try:
            # 动态表中添加新动态
            __new_dy = Bilidynamic(uid=user_id, dynamic_id=dynamic_id, dynamic_type=dynamic_type,
                                   content=content, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_dy)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_dy_info_to_db, DBSESSION ERROR, error info: {e}, '
                             f'failed to add new dymanic.')
            return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_dy_info_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 初始化动态列表
async def init_dynamic_info(_dy_uid) -> list:
    url = DYNAMIC_API_URL
    payload = {'host_uid': _dy_uid}
    dynamic_info = await fetch(url=url, paras=payload)
    list_dynamic_id = []
    for card_num in range(len(dynamic_info['data']['cards'])):
        cards = dynamic_info['data']['cards'][card_num]
        list_dynamic_id.append(cards['desc']['dynamic_id'])
    return list_dynamic_id


# 查询动态并返回动态类型及内容
async def get_dynamic_info(dy_uid) -> dict:
    _DYNAMIC_INFO = {}  # 这个字典用来放最后的输出结果
    url = DYNAMIC_API_URL
    payload = {'host_uid': dy_uid}
    try:
        log.logger.debug(f"{__name__}: get_dynamic_info: 获取用户: {dy_uid} 动态")
        dynamic_info = await fetch(url=url, paras=payload)
    except Exception as e:
        log.logger.error(f'{__name__}: get_dynamic_info ERROR: {e}, dy_uid: {dy_uid}')
        raise Exception("get_dynamic_info ERROR")
    for card_num in range(len(dynamic_info['data']['cards'])):
        cards = dynamic_info['data']['cards'][card_num]
        card = json.loads(cards['card'])
        '''
        动态type对应如下: 
        1 转发
        2 消息（有图片）
        4 消息（无图片）
        8 视频投稿
        16 小视频（含playurl地址）
        32 番剧更新
        64 专栏
        256 音频
        512 番剧更新（含详细信息）
        '''
        # type=1, 这是一条转发的动态
        if cards['desc']['type'] == 1:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是转发动态时评论的内容
            content = card['item']['content']
            # 这是被转发的原动态信息
            try:
                origin_dy_uid = cards['desc']['origin']['dynamic_id']
                __payload = {'dynamic_id': origin_dy_uid}
                origin_dynamic = await fetch(url=GET_DYNAMIC_DETAIL_API_URL, paras=__payload)
                origin_card = origin_dynamic['data']['card']
                origin_name = origin_card['desc']['user_profile']['info']['uname']
                origin_pics_list = []
                if origin_card['desc']['type'] == 1:
                    origin_description = json.loads(origin_card['card'])['item']['content']
                elif origin_card['desc']['type'] == 2:
                    origin_description = json.loads(origin_card['card'])['item']['description']
                    origin_pics = json.loads(origin_card['card'])['item']['pictures']
                    for item in origin_pics:
                        try:
                            origin_pics_list.append(item['img_src'])
                        except (KeyError, TypeError):
                            continue
                elif origin_card['desc']['type'] == 4:
                    origin_description = json.loads(origin_card['card'])['item']['content']
                elif origin_card['desc']['type'] == 8:
                    origin_description = json.loads(origin_card['card'])['dynamic']
                    if not origin_description:
                        origin_description = json.loads(origin_card['card'])['title']
                elif origin_card['desc']['type'] == 16:
                    origin_description = json.loads(origin_card['card'])['item']['description']
                elif origin_card['desc']['type'] == 32:
                    origin_description = json.loads(origin_card['card'])['title']
                elif origin_card['desc']['type'] == 64:
                    origin_description = json.loads(origin_card['card'])['summary']
                elif origin_card['desc']['type'] == 256:
                    origin_description = json.loads(origin_card['card'])['intro']
                elif origin_card['desc']['type'] == 512:
                    origin_description = json.loads(origin_card['card'])['apiSeasonInfo']['title']
                else:
                    origin_description = ''
                origin = dict({'id': origin_dy_uid, 'type': origin_card['desc']['type'], 'url': '',
                               'name': origin_name, 'content': origin_description, 'origin': '',
                               'origin_pics': origin_pics_list})
            except Exception as e:
                # 原动态被删除
                origin = dict({'id': -1, 'type': -1, 'url': '',
                               'name': 'Unknow', 'content': '原动态被删除', 'origin': ''})
                log.logger.debug(f'{__name__}: '
                                 f'get_dynamic_info - type-1 origin ERROR: 原动态被删除: {dy_id}, error: {e}')
            card_dic = dict({'id': dy_id, 'type': 1, 'url': url,
                             'name': name, 'content': content, 'origin': origin})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=2, 这是一条原创的动态(有图片)
        elif cards['desc']['type'] == 2:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是动态的内容
            description = card['item']['description']
            # 这是动态图片列表
            pic_urls = []
            for pic_info in card['item']['pictures']:
                pic_urls.append(pic_info['img_src'])
            card_dic = dict({'id': dy_id, 'type': 2, 'url': url, 'pic_urls': pic_urls,
                             'name': name, 'content': description, 'origin': ''})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=4, 这是一条原创的动态(无图片)
        elif cards['desc']['type'] == 4:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是动态的内容
            description = card['item']['content']
            card_dic = dict({'id': dy_id, 'type': 4, 'url': url,
                             'name': name, 'content': description, 'origin': ''})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=8, 这是发布视频
        elif cards['desc']['type'] == 8:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是视频的简介和标题
            content = card['dynamic']
            title = card['title']
            card_dic = dict({'id': dy_id, 'type': 8, 'url': url,
                             'name': name, 'content': content, 'origin': title})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=16, 这是小视频(现在似乎已经失效？)
        elif cards['desc']['type'] == 16:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是简介
            try:
                content = card['item']['description']
            except (KeyError, TypeError):
                content = card['item']['desc']
            card_dic = dict({'id': dy_id, 'type': 16, 'url': url,
                             'name': name, 'content': content, 'origin': ''})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=32, 这是番剧更新
        elif cards['desc']['type'] == 32:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是番剧标题
            title = card['title']
            card_dic = dict({'id': dy_id, 'type': 32, 'url': url,
                             'name': name, 'content': '', 'origin': title})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=64, 这是文章动态
        elif cards['desc']['type'] == 64:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是文章的摘要和标题
            content = card['summary']
            title = card['title']
            card_dic = dict({'id': dy_id, 'type': 64, 'url': url,
                             'name': name, 'content': content, 'origin': title})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=256, 这是音频
        elif cards['desc']['type'] == 256:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是动态的内容
            description = card['intro']
            title = card['title']
            card_dic = dict({'id': dy_id, 'type': 256, 'url': url,
                             'name': name, 'content': description, 'origin': title})
            _DYNAMIC_INFO[card_num] = card_dic
        # type=512, 番剧更新（详情）
        elif cards['desc']['type'] == 512:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = cards['desc']['user_profile']['info']['uname']
            # 这是番剧标题
            title = card['apiSeasonInfo']['title']
            card_dic = dict({'id': dy_id, 'type': 512, 'url': url,
                             'name': name, 'content': '', 'origin': title})
            _DYNAMIC_INFO[card_num] = card_dic
        else:
            # 其他未知类型
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            name = 'Unknow'
            card_dic = dict({'id': dy_id, 'type': -1, 'url': url,
                             'name': name, 'content': '', 'origin': ''})
            _DYNAMIC_INFO[card_num] = card_dic
    return _DYNAMIC_INFO


# 根据用户uid获取用户信息
async def get_user_info(user_id) -> dict:
    url = USER_INFO_API_URL
    payload = {'mid': user_id}
    user_info = await fetch(url=url, paras=payload)
    if user_info['code'] != 0:
        return dict({'status': 'error'})
    return dict({'status': user_info['code'], 'name': user_info['data']['name']})
