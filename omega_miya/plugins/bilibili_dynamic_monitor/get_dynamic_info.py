import requests
import json
from omega_miya.plugins.bilibili_dynamic_monitor.config import *


# 初始化动态列表
def init_live_info(_dy_uid) -> list:
    url = DYNAMIC_API_URL
    payload = {'host_uid': _dy_uid}
    res_dynamic = requests.get(url=url, params=payload)
    dynamic_info = res_dynamic.json()
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
    res_dynamic = requests.get(url=url, params=payload)
    dynamic_info = res_dynamic.json()
    for card_num in range(len(dynamic_info['data']['cards'])):
        cards = dynamic_info['data']['cards'][card_num]
        card = json.loads(cards['card'])
        # 这是一条转发的动态
        if cards['desc']['type'] == 1:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = card['user']['uname']
            # 这是转发动态时评论的内容
            content = card['item']['content']
            # 这是被转发的原动态的发布者名称
            origin = json.loads(card['origin'])
            try:
                try:
                    try:
                        try:
                            # 转发自己的
                            origin_name = origin['user']['name']
                        except KeyError:
                            # 转发别人的
                            origin_name = origin['user']['uname']
                    except KeyError:
                        # 转发视频
                        origin_name = origin['owner']['name']
                except KeyError:
                    # 转发文章
                    origin_name = origin['author']['name']
            except KeyError:
                # 转发直播间
                origin_name = origin['uname']
            card_dic = dict({'id': dy_id, 'type': 1, 'url': url,
                             'name': name, 'content': content, 'origin': origin_name})
            _DYNAMIC_INFO[card_num] = card_dic
        # 这是一条原创的动态
        elif cards['desc']['type'] == 2:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = card['user']['name']
            # 这是动态的内容
            description = card['item']['description']
            card_dic = dict({'id': dy_id, 'type': 2, 'url': url,
                             'name': name, 'content': description, 'origin': ''})
            _DYNAMIC_INFO[card_num] = card_dic
        # 4\16\32猜不出来是啥，看起来和原创动态一摸一样，但返回的格式却长得跟转发动态一样
        # 就先当它是原创动态好了
        elif cards['desc']['type'] in [4, 16, 32]:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称，同上
            try:
                try:
                    try:
                        try:
                            name = card['user']['name']
                        except KeyError:
                            name = card['user']['uname']
                    except KeyError:
                        name = card['owner']['name']
                except KeyError:
                    name = card['author']['name']
            except KeyError:
                name = card['uname']
            # 这是转发动态时评论的内容
            content = card['item']['content']
            card_dic = dict({'id': dy_id, 'type': 2, 'url': url,
                             'name': name, 'content': content, 'origin': ''})
            _DYNAMIC_INFO[card_num] = card_dic
        # 8应该是发布视频
        elif cards['desc']['type'] == 8:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = card['owner']['name']
            # 这是视频的简介和标题
            content = card['dynamic']
            title = card['title']
            card_dic = dict({'id': dy_id, 'type': 8, 'url': url,
                             'name': name, 'content': content, 'origin': title})
            _DYNAMIC_INFO[card_num] = card_dic
        # 64应该是文章动态
        elif cards['desc']['type'] == 64:
            # 这是动态的ID
            dy_id = cards['desc']['dynamic_id']
            # 这是动态的链接
            url = DYNAMIC_URL + str(cards['desc']['dynamic_id'])
            # 这是动态发布者的名称
            name = card['author']['name']
            # 这是文章的摘要和标题
            content = card['summary']
            title = card['title']
            card_dic = dict({'id': dy_id, 'type': 64, 'url': url,
                             'name': name, 'content': content, 'origin': title})
            _DYNAMIC_INFO[card_num] = card_dic
    return _DYNAMIC_INFO
