import requests
import re
from nonebot import log
from omega_miya.plugins.pixiv.config import illust_artwork_url, illust_data_url


# 获取作品完整信息（pixiv api 获取 json）
def get_illust_data(illust_id) -> dict:
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    url_illust = illust_data_url + str(illust_id)
    res_illust = requests.get(url_illust, headers=headers)
    return dict(res_illust.json())


# 格式化tag
def std_illust_tag(res_data: dict) -> list:
    illust_tag = []
    tag_number = len(res_data['body']['tags']['tags'])
    for tag_num in range(tag_number):
        illust_tag.append(res_data['body']['tags']['tags'][tag_num]['tag'])
    return list(illust_tag)


# 检查是否R18
def illust_r18_check(res_data: dict) -> bool:
    tag_list = std_illust_tag(res_data)
    if 'R-18' in tag_list:
        return True
    else:
        return False


# 检查作品状态
def illust_status_check(res_data: dict) -> bool:
    illust_status = res_data['error']
    if not illust_status:
        return True
    else:
        return False


# 格式化作品状态、名称、作者、url等
def std_illust_info(res_data: dict) -> dict:
    illust_status = res_data['error']
    illust_author = res_data['body']['userName']
    illust_title = res_data['body']['illustTitle']
    illust_orig_url = res_data['body']['urls']['original']
    illust_regular_url = res_data['body']['urls']['regular']
    illust_description = res_data['body']['description']
    re_std_description_s1 = r'(\<br\>|\<br \/\>)'
    re_std_description_s2 = r'<[^>]+>'
    illust_description = re.sub(re_std_description_s1, '\n', illust_description)
    illust_description = re.sub(re_std_description_s2, '', illust_description)
    return dict(
        {'illust_author': illust_author, 'illust_title': illust_title,
         'illust_description': illust_description, 'illust_orig_url': illust_orig_url,
         'illust_regular_url': illust_regular_url, 'illust_status': illust_status})


# 判断作品状态，返回格式化文本
async def get_illust_info(illust_id) -> dict:
    try:
        illust_data = get_illust_data(illust_id)
    except Exception as e:
        log.logger.error(f'Pixiv: get_illust_info ERROR: {e}')
        return {'status': 'error'}
    try:
        illust_is_ok = illust_status_check(illust_data)
    except Exception as e:
        log.logger.error(f'Pixiv: get_illust_info ERROR: {e}')
        return {'status': "error"}
    # 确认作品状态正常后再进行r18检查及文本格式化操作
    if illust_is_ok:
        illust_is_r18 = illust_r18_check(illust_data)
        illust_tags = std_illust_tag(illust_data)
        illust_info = std_illust_info(illust_data)
        # 格式化tag序列
        tags = ''
        for tag_num in range(len(illust_tags)):
            tags += '#' + illust_tags[tag_num] + ' '
        msg = '「{}」/「{}」\n{}\n{}\n----------------\n{}'.format(
            illust_info['illust_title'], illust_info['illust_author'],
            tags, illust_artwork_url + illust_id, illust_info['illust_description'])
        return dict({'status': illust_is_ok, 'is_r18': illust_is_r18,
                     'illust_info': msg, 'regular_url': illust_info['illust_regular_url']})
    else:
        return dict({'status': illust_is_ok})
