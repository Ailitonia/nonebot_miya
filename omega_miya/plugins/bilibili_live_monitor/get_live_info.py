import requests
from omega_miya.plugins.bilibili_live_monitor.config import *


# 初始化直播间状态
def init_live_status(room_id) -> int:
    url = LIVE_API_URL
    payload = {'id': room_id}
    res_live = requests.get(url, params=payload)
    live_status = dict(res_live.json())
    return int(live_status['data']['live_status'])


# 初始化直播间标题
def init_live_title(room_id) -> str:
    url = LIVE_API_URL
    payload = {'id': room_id}
    res_live = requests.get(url, params=payload)
    live_title = dict(res_live.json())
    return str(live_title['data']['title'])


# 获取直播间信息
async def get_live_info(room_id) -> dict:
    url = LIVE_API_URL
    payload = {'id': room_id}
    res_live = requests.get(url, params=payload)
    live_info = dict(res_live.json())
    return dict({'status': live_info['data']['live_status'], 'url': LIVE_URL + str(room_id),
                 'title': live_info['data']['title'], 'time': live_info['data']['live_time']})
