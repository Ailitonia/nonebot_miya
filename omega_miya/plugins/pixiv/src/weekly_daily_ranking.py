import requests
import random

ranking_url = 'http://www.pixiv.net/ranking.php'


def get_rand_daily_ranking() -> str:
    payload_daily = {'format': 'json', 'mode': 'daily',
                     'content': 'illust', 'p': random.choice(list(range(1, 2)))}
    res_illust = requests.get(ranking_url, params=payload_daily)
    illust_list = dict(res_illust.json())
    rand_illust_num = random.choice(range(len(illust_list['contents'])))
    illust_id = illust_list['contents'][rand_illust_num]['illust_id']
    return str(illust_id)


def get_rand_weekly_ranking() -> str:
    payload_weekly = {'format': 'json', 'mode': 'weekly',
                      'content': 'illust', 'p': random.choice(list(range(1, 3)))}
    res_illust = requests.get(ranking_url, params=payload_weekly)
    illust_list = dict(res_illust.json())
    rand_illust_num = random.choice(range(len(illust_list['contents'])))
    illust_id = illust_list['contents'][rand_illust_num]['illust_id']
    return str(illust_id)


def get_rand_monthly_ranking() -> str:
    payload_monthly = {'format': 'json', 'mode': 'monthly',
                       'content': 'illust', 'p': random.choice(list(range(1, 2)))}
    res_illust = requests.get(ranking_url, params=payload_monthly)
    illust_list = dict(res_illust.json())
    rand_illust_num = random.choice(range(len(illust_list['contents'])))
    illust_id = illust_list['contents'][rand_illust_num]['illust_id']
    return str(illust_id)
