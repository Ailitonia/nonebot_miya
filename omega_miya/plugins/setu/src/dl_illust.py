import os
import requests
from omega_miya.plugins.setu.config import illust_full_path


# get获取图片png
def get_illust_png(illust_url: str):
    # 省空间不使用原图
    # 加header，不然会403
    # headers = {'referer': 'https://www.pixiv.net/'}
    illust_regular_png = requests.get(illust_url)
    return illust_regular_png.content


# 保存图片到本地
def dl_png(sourse, illust_id):
    file_name = str(illust_id) + '.jpg'
    path = illust_full_path
    if not os.path.exists(path):
        os.mkdir(path)
    full_path = os.path.join(path, file_name)
    with open(full_path, 'wb+') as f:
        f.write(sourse)


# 方便调用
def dl_illust(illust_id, illust_url):
    if not os.path.exists(illust_full_path + str(illust_id) + '.jpg'):
        dl_png(get_illust_png(illust_url), illust_id)
    else:
        pass
