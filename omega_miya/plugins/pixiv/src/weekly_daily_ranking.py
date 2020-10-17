import requests
import random
from nonebot import log

ranking_url = 'http://www.pixiv.net/ranking.php'


def get_rand_daily_ranking() -> str:
    payload_daily = {'format': 'json', 'mode': 'daily',
                     'content': 'illust', 'p': random.choice(list(range(1, 2)))}
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    try:
        res_illust = requests.get(ranking_url, params=payload_daily, headers=headers)
    except Exception as e:
        log.logger.error(f'Pixiv: get_rand_daily_ranking ERROR: {e}')
        return 'error'
    illust_list = dict(res_illust.json())
    rand_illust_num = random.choice(range(len(illust_list['contents'])))
    illust_id = illust_list['contents'][rand_illust_num]['illust_id']
    return str(illust_id)


def get_rand_weekly_ranking() -> str:
    payload_weekly = {'format': 'json', 'mode': 'weekly',
                      'content': 'illust', 'p': random.choice(list(range(1, 3)))}
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    try:
        res_illust = requests.get(ranking_url, params=payload_weekly, headers=headers)
    except Exception as e:
        log.logger.error(f'Pixiv: get_rand_weekly_ranking ERROR: {e}')
        return 'error'
    illust_list = dict(res_illust.json())
    rand_illust_num = random.choice(range(len(illust_list['contents'])))
    illust_id = illust_list['contents'][rand_illust_num]['illust_id']
    return str(illust_id)


def get_rand_monthly_ranking() -> str:
    payload_monthly = {'format': 'json', 'mode': 'monthly',
                       'content': 'illust', 'p': random.choice(list(range(1, 2)))}
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    try:
        res_illust = requests.get(ranking_url, params=payload_monthly, headers=headers)
    except Exception as e:
        log.logger.error(f'Pixiv: get_rand_monthly_ranking ERROR: {e}')
        return 'error'
    illust_list = dict(res_illust.json())
    rand_illust_num = random.choice(range(len(illust_list['contents'])))
    illust_id = illust_list['contents'][rand_illust_num]['illust_id']
    return str(illust_id)
