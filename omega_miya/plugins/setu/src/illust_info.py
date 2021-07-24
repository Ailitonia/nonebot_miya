import aiohttp
import random
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import func
from nonebot import log
from omega_miya.database import *
from omega_miya.plugins.setu.config import API_KEY, illust_data_url


async def fetch(url: str, paras: dict) -> dict:
    timeout_count = 0
    while timeout_count < 3:
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                async with session.get(url=url, params=paras, headers=headers, timeout=timeout) as resp:
                    log.logger.debug('Setu: started fetch')
                    json = await resp.json()
            return json
        except Exception as e:
            log.logger.warning(f'Setu: fetch ERROR: {e}. Occurred in try {timeout_count + 1} using paras: {paras}')
        finally:
            timeout_count += 1
    else:
        log.logger.warning(f'Setu: fetch ERROR: Timeout {timeout_count}, using paras: {paras}')
        return {'error': 'error'}


async def add_illust_info_to_db(pid) -> bool:
    pid = int(pid)
    try:
        # 检测作品存在及唯一性
        if NONEBOT_DBSESSION.query(Pixiv.pid).filter(Pixiv.pid == pid).one():
            log.logger.info(f'{__name__}: add_illust_info_to_db: 作品: {pid} 已存在, 跳过.')
            return True
    except NoResultFound:
        log.logger.info(f'{__name__}: add_illust_info_to_db: 作品: {pid} 不存在, 获取作品信息.')
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: add_illust_info_to_db: 作品: {pid} 存在复数行, 已忽略.')
        return False

    # 调用pixiv作品信息api
    __API_URL = 'https://moepic.amoeloli.xyz/apiproxy/api/setu/pixiv/'
    __API_KEY = '22f2ea8a8e361a93e4517d4ed3039b2c'
    __paras = {'key': __API_KEY, 'pid': pid}
    __json = await fetch(url=__API_URL, paras=__paras)
    # fetch超时
    if __json['error'] == 'error':
        log.logger.error(f'{__name__}: add_illust_info_to_db: 获取作品: {pid} 信息超时.')
        return False
    # api错误
    elif __json['error']:
        log.logger.error(f'{__name__}: add_illust_info_to_db: 获取作品: {pid} 信息失败, api错误.')
        return False

    # 处理作品信息
    pid = int(__json['body']['pid'])
    uid = int(__json['body']['uid'])
    title = str(__json['body']['title'])
    uname = str(__json['body']['uname'])
    url = str(__json['body']['url'])
    tags = list(__json['body']['tags'])

    # 将tag写入pixiv_tag表
    for tag in tags:
        tag = str(tag)
        try:
            # 检测tag存在及唯一性
            if NONEBOT_DBSESSION.query(PixivTag.tagname).filter(PixivTag.tagname == tag).one():
                log.logger.info(f'{__name__}: add_illust_info_to_db: Tag: {tag} 已存在, 跳过.')
        except NoResultFound:
            try:
                __new_tag = PixivTag(tagname=tag, created_at=datetime.now())
                NONEBOT_DBSESSION.add(__new_tag)
                NONEBOT_DBSESSION.commit()
            except Exception as e:
                NONEBOT_DBSESSION.rollback()
                log.logger.error(f'{__name__}: DBSESSION ERROR, table PixivTag, error info: {e}.')
                return False
            log.logger.info(f'{__name__}: add_illust_info_to_db: Tag: {tag} 不存在, 已创建.')
        except MultipleResultsFound:
            log.logger.error(f'{__name__}: add_illust_info_to_db: Tag: {tag} 存在复数行, 已忽略.')

    # 将作品信息写入pixiv_illust表
    try:
        __new_illust = Pixiv(pid=pid, uid=uid, title=title, uname=uname, url=url, tags=str(tags),
                             created_at=datetime.now())
        NONEBOT_DBSESSION.add(__new_illust)
        NONEBOT_DBSESSION.commit()
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: DBSESSION ERROR, table Pixiv, error info: {e}.')
        return False

    # 写入tag_pixiv关联表
    # 获取本作品在illust表中的id
    illust_id = NONEBOT_DBSESSION.query(Pixiv.id).filter(Pixiv.pid == pid).one()[0]
    illust_id = int(illust_id)
    # 根据作品tag依次写入tag_illust表
    for illust_tag in tags:
        illust_tag = str(illust_tag)
        illust_tag_id = NONEBOT_DBSESSION.query(PixivTag.id).filter(PixivTag.tagname == illust_tag).one()[0]
        illust_tag_id = int(illust_tag_id)
        try:
            __new_tag_illust = PixivT2I(illust_id=illust_id, tag_id=illust_tag_id, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_tag_illust)
            NONEBOT_DBSESSION.commit()
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: DBSESSION ERROR, table PixivT2I, error info: {e}.')
            try:
                # 避免以后查询不到，写入失败就将illust信息一并删除
                __exist_illust = NONEBOT_DBSESSION.query(Pixiv).filter(Pixiv.pid == pid).one()
                NONEBOT_DBSESSION.delete(__exist_illust)
                NONEBOT_DBSESSION.commit()
            except Exception as e:
                # 这里还出错就没救了x
                NONEBOT_DBSESSION.rollback()
                log.logger.error(f'{__name__}: DBSESSION ERROR, table Pixiv, error info: {e}.')
            return False
    log.logger.info(f'{__name__}: add_illust_info_to_db: 作品: {pid} 作品信息已成功写入数据库.')
    return True


# 获取作品完整信息（pixiv api 获取 json）
async def get_illust_data(is_r18, num=3, tag=None) -> list:
    url = illust_data_url
    if not tag:
        payload = {'apikey': API_KEY, 'r18': is_r18, 'num': num, 'size1200': 'true'}
    else:
        payload = {'apikey': API_KEY, 'r18': is_r18, 'keyword': tag, 'num': num, 'size1200': 'true'}
    try:
        res_illust = await fetch(url=url, paras=payload)
    except Exception as e:
        log.logger.error(f'Setu: get_illust_data ERROR: {e}')
        return []
    res_illust_json = res_illust
    if res_illust_json['code'] != 0:
        return []
    illust_link_list = []
    try:
        for item in res_illust_json['data']:
            illust_link_list.append({'pid': item['pid'], 'url': item['url']})
        return illust_link_list
    except Exception as e:
        log.logger.error(f'Setu: get_illust_data ERROR: {e}')
        return []


# 获取作品完整信息（多tag模式）（本地数据库查询）
def get_t_illust_data_from_db(*tags) -> dict:
    # 限制数量
    limit_mun = 3

    # 识别r18模式
    if 'r18' in tags:
        r18 = 1
        tags = list(tags)
        tags.append('R-18')
        tags.remove('r18')
    elif 'mr18' in tags:
        r18 = 2
        tags = list(tags)
        tags.remove('mr18')
    elif 'R-18' in tags:
        r18 = 1
    else:
        r18 = 0

    illust_id_list = []

    if not tags:
        illust_id = NONEBOT_DBSESSION.query(Pixiv.pid). \
            order_by(func.random()).limit(limit_mun * 2).all()
        pid_list = []
        for pid in illust_id:
            pid_list.append(pid[0])
        illust_id_list.append(pid_list)
    else:
        for tag in tags:
            tag_pid = NONEBOT_DBSESSION.query(Pixiv.pid). \
                filter(Pixiv.id == PixivT2I.illust_id). \
                filter(PixivT2I.tag_id == PixivTag.id). \
                filter(PixivTag.tagname.ilike(f'%{tag}%')).all()
            tag_pid_list = []
            for pid in tag_pid:
                tag_pid_list.append(pid[0])
            illust_id_list.append(tag_pid_list)

    # 处理r18的tag
    # 数据库中R-18的tag_id为17
    r18_tag_pid = NONEBOT_DBSESSION.query(Pixiv.pid). \
        filter(Pixiv.id == PixivT2I.illust_id). \
        filter(PixivT2I.tag_id == 17).all()
    r18_tag_pid_list = []
    for res in r18_tag_pid:
        r18_tag_pid_list.append(res[0])

    # 处理tag交补
    # 同时满足所有tag
    result = set(illust_id_list[0]).intersection(*illust_id_list[1:])
    if r18 == 0:
        # 排除r18
        result = result.difference(set(r18_tag_pid_list))
    elif r18 == 1:
        # 只要r18
        # result = result.intersection(set(r18_tag_pid_list))
        # tag已替换处理，查询本身只会查出带R-18标签的作品
        pass
    else:
        # 混合模式
        pass
    result = list(result)

    # 限制数量
    if len(result) > limit_mun:
        result = random.sample(result, k=limit_mun)

    # 处理输出结果
    final_result = {'r18': r18, 'item': []}
    for pid in result:
        final_result['item'].append(pid)

    return final_result


# 获取本地数据库统计信息
def get_illust_db_stat() -> dict:
    illust_count = NONEBOT_DBSESSION.query(func.count(Pixiv.id)).scalar()
    r18_illust_count = NONEBOT_DBSESSION.query(func.count(PixivT2I.id)). \
        filter(PixivT2I.tag_id == PixivTag.id). \
        filter(PixivTag.tagname == 'R-18').scalar()
    result = {'total': int(illust_count), 'r18': int(r18_illust_count)}
    return result
