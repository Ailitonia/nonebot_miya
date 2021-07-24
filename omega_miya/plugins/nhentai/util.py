import re
from bs4 import BeautifulSoup
import json
import zipfile
import requests
import time
import os
from nonebot import log
from urllib import request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed


class NHException(Exception):
    def __init__(self, *args):
        super(NHException, self).__init__(*args)


# 下载一张图片
def fetch_image(index: int, url: str, local: str):
    print(f'Try fetching {url} to {local}')
    success = False
    i = 0
    last_error = None

    # 已经下载过了就不再下载
    if os.path.exists(local):
        return index, True

    # 单张图片尝试下载3次
    while not success and i < 3:
        try:
            request.urlretrieve(url, local)
            success = True
        except Exception as e:
            i += 1
            last_error = e
            time.sleep(3)

    # 失败的话打个print
    if not success:
        print(f'Fetching {url} Failed after 3 tries')
        print(last_error)

    # 返回图片编号和成功与否
    return index, success


# 并发执行所有下载请求
def concurrently_fetch(request_list, pool=2):
    # 提交所有任务
    tasks = []
    with ThreadPoolExecutor(pool) as executor:
        for req in request_list:
            i, url, local, file_type = req
            task = executor.submit(fetch_image, i, url, local)
            tasks.append(task)

    # 是否全部下载成功
    all_success = True
    # 哪些下载失败
    failed_list = []

    # 等待所有任务执行完毕
    for future in as_completed(tasks):
        i, success = future.result()
        if not success:
            all_success = False
            failed_list.append(i)

    # 返回下载结果
    return all_success, failed_list


# 通过关键词搜索本子id和标题
async def search_gallery_by_tag(tag: str) -> list:
    # 搜索关键词
    payload_tag = {'q': tag}
    search_url = f'https://nhentai.net/search/'
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    search_res = requests.get(search_url, params=payload_tag, headers=headers).text
    result = []
    try:
        gallery_soup = BeautifulSoup(search_res, 'lxml').find_all('div', class_='gallery')
        if len(gallery_soup) >= 10:
            for item in gallery_soup[0:10]:
                gallery_title = item.find('div', class_='caption').get_text(strip=True)
                gallery_id = re.sub(r'\D', '', item.find('a', class_='cover').get('href'))
                result.append({'id': gallery_id, 'title': gallery_title})
        else:
            for item in gallery_soup:
                gallery_title = item.find('div', class_='caption').get_text(strip=True)
                gallery_id = re.sub(r'\D', '', item.find('a', class_='cover').get('href'))
                result.append({'id': gallery_id, 'title': gallery_title})
    except Exception as e:
        log.logger.error(f'{__name__}: search_gallery_by_tag ERROR: {e}')
        return []
    return result


# 用GET方法请求某资源 返回文本
def get_html(url):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    r = requests.get(url, headers=headers)
    return r.text


# 从html文本中找到包含本子数据的那一行 即粗定位数据
def get_gallery_line_from_html(html_text: str) -> str:
    start = html_text.find('window._gallery')
    middle_text = html_text[start:]
    end = middle_text.find('\n')
    return middle_text[:end]


# 从单行JS脚本中取出JSON字符串的部分 细定位
def get_json_text_from_js_text(js_text: str) -> str:
    start_tips = 'JSON.parse'
    start = js_text.find(start_tips)
    stop = js_text.rindex('"')
    start += len(start_tips) + 2
    return js_text[start:stop]


# 从JSON字符串解析数据 转为python结构
def get_dict_from_json_text(json_text: str) -> dict:
    # 把字符串中的\u都反解析掉
    decodeable_json_text = json_text.encode('utf-8').decode('unicode_escape')
    return json.loads(decodeable_json_text)


# 获取gallery信息
def get_gallery_data_by_id(gallery_id: int) -> dict:
    try:
        html_text = get_html(f'https://nhentai.net/g/{gallery_id}/1/')
    except Exception as e:
        raise NHException(f'ERROR: {e}，访问本子页面时异常，似乎网络不行')
    try:
        js_text = get_gallery_line_from_html(html_text)
    except Exception as e:
        raise NHException(f'ERROR: {e}，解析本子信息时异常，读取信息行失败')
    try:
        json_text = get_json_text_from_js_text(js_text)
    except Exception as e:
        raise NHException(f'ERROR: {e}，解析本子信息时异常，分割JSON字符串失败')
    try:
        gallery = get_dict_from_json_text(json_text)
    except Exception as e:
        raise NHException(f'ERROR: {e}，解析本子信息时异常，解析JSON失败')
    return gallery


# 给定本子ID 下载所有图片到指定目录
async def fetch_gallery(gallery_id: int):
    # 获取gallery信息
    gallery = get_gallery_data_by_id(gallery_id)
    # 获取总页数
    total_page_count = len(gallery['images']['pages'])
    # 生成每一页对应的图片格式
    every_page_image_type = []
    for num in range(total_page_count):
        every_page_image_type.append(gallery['images']['pages'][num]['t'])
    # 本子图片的media编号
    media_id = gallery['media_id']
    # 子目录
    nhentai_plugin_path = os.path.dirname(__file__)
    sub_dir = f'{nhentai_plugin_path}/nhentai_gallery/{gallery_id}'
    # 创建子目录
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)

    # 产生请求序列
    request_list = []
    for i in range(total_page_count):
        type_index = i
        index = i + 1
        if every_page_image_type[type_index] == 'j':
            file_type = 'jpg'
        elif every_page_image_type[type_index] == 'p':
            file_type = 'png'
        else:
            file_type = 'undefined'
        url = f'https://i.nhentai.net/galleries/{media_id}/{index}.{file_type}'
        local = f'{sub_dir}/{index}.{file_type}'
        req = index, url, local, file_type
        request_list.append(req)

    # 下载所有图片
    success, failed_list = concurrently_fetch(request_list)
    if not success:
        failed_list_str = ','.join([str(x) for x in failed_list])
        raise NHException(f'图片{failed_list_str}下载失败')

    # 打包成zip
    z = zipfile.ZipFile(f'{sub_dir}/{gallery_id}.zip', 'w')
    manifest_path = f'{sub_dir}/manifest.json'
    with open(manifest_path, 'w') as f:
        f.write(json.dumps(gallery))
    z.write(manifest_path, 'manifest.json')
    for index, url, local, file_type in request_list:
        z.write(local, f'{index}.{file_type}')
    z.close()
