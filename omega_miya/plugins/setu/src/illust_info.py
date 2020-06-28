import requests
from datetime import datetime
from omega_miya.database import *
from omega_miya.plugins.setu.config import API_KEY, illust_data_url


def add_illust_info_to_db(pid, uid, title, author, tags, url) -> bool:
    if NONEBOT_DBSESSION.query(Pixiv.pid).filter(Pixiv.pid == pid).first():
        return False
    else:
        __new_illust = Pixiv(pid=pid, uid=uid, title=title, author=author,
                             tags=tags, url=url, created_at=datetime.now())
        NONEBOT_DBSESSION.add(__new_illust)
        NONEBOT_DBSESSION.commit()
        return True


# 获取作品完整信息（pixiv api 获取 json）
async def get_illust_data(is_r18, tag=None) -> list:
    url = illust_data_url
    payload = {'apikey': API_KEY, 'r18': is_r18, 'keyword': tag, 'num': 3, 'size1200': 'true'}
    res_illust = requests.get(url=url, params=payload)
    res_illust_json = res_illust.json()
    if res_illust_json['code'] != 0:
        return []
    illust_link_list = []
    for item in res_illust_json['data']:
        add_illust_info_to_db(pid=item['pid'], uid=item['uid'], title=item['title'],
                              author=item['author'], tags=str(item['tags']), url=item['url'])
        illust_link_list.append({'pid': item['pid'], 'url': item['url']})
    return illust_link_list
