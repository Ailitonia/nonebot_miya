import re
import aiohttp
import base64
from bs4 import BeautifulSoup
from io import BytesIO
from aiocqhttp import MessageSegment
from omega_miya.plugins.Group_manage.group_permissions import *
from nonebot import on_command, CommandSession, permission, log
from nonebot.command.argfilter import validators, controllers


__plugin_name__ = '识图助手'
__plugin_usage__ = r'''【识图助手】

使用SauceNAO API识别各类图片、插画

用法: 
/识图'''

API_KEY = '123456abc'
# saucenao的apikey自行去申请
API_URL = 'https://saucenao.com/search.php'
API_URL_ASCII2D = 'https://ascii2d.net/search/url/'


# on_command 装饰器将函数声明为一个命令处理器
# 这里 pid 为命令的名字
@on_command('searchimage', aliases='识图', only_to_me=False, permission=permission.EVERYBODY)
async def searchimage(session: CommandSession):
    # 图片转base64
    async def pic_2_base64(url: str) -> str:
        async def get_image(pic_url: str):
            timeout_count = 0
            while timeout_count < 3:
                try:
                    timeout = aiohttp.ClientTimeout(total=2)
                    async with aiohttp.ClientSession(timeout=timeout) as __session:
                        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                 'Chrome/83.0.4103.116 Safari/537.36'}
                        async with __session.get(url=pic_url, headers=headers, timeout=timeout) as resp:
                            image = await resp.read()
                    return image
                except Exception as __err:
                    log.logger.warning(f'{__name__}: pic_2_base64: get_image ERROR: {__err}. '
                                       f'Occurred in try {timeout_count + 1} using paras: {pic_url}')
                finally:
                    timeout_count += 1
            else:
                log.logger.warning(f'{__name__}: pic_2_base64: '
                                   f'get_image ERROR: Timeout {timeout_count}, using paras: {pic_url}')
                return None

        origin_image_f = BytesIO()
        try:
            origin_image_f.write(await get_image(pic_url=url))
        except Exception as err:
            log.logger.warning(f'{__name__}: pic_2_base64 ERROR: {err}')
            return ''
        b64 = base64.b64encode(origin_image_f.getvalue())
        b64 = str(b64, encoding='utf-8')
        b64 = 'base64://' + b64
        origin_image_f.close()
        return b64

    # 获取识别结果 Saucenao模块
    async def get_identify_result(url: str) -> list:
        async def get_result(__url: str, paras: dict) -> dict:
            timeout_count = 0
            while timeout_count < 3:
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as __session:
                        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                 'Chrome/83.0.4103.116 Safari/537.36'}
                        async with __session.get(url=__url, params=paras, headers=headers, timeout=timeout) as resp:
                            json = await resp.json()
                    return json
                except Exception as err:
                    log.logger.warning(f'{__name__}: get_identify_result ERROR: {err}. '
                                       f'Occurred in try {timeout_count + 1} using paras: {paras}')
                finally:
                    timeout_count += 1
            else:
                log.logger.warning(f'{__name__}: get_identify_result ERROR: '
                                   f'Timeout {timeout_count}, using paras: {paras}')
                return {'header': {'status': 1}, 'results': []}

        __payload = {'output_type': 2,
                     'api_key': API_KEY,
                     'testmode': 1,
                     'numres': 6,
                     'db': 999,
                     'url': url}
        __result_json = await get_result(__url=API_URL, paras=__payload)
        if __result_json['header']['status'] != 0:
            log.logger.warning(f"{__name__}: get_identify_result ERROR: "
                               f"status code: {__result_json['header']['status']}, Sever or Client error")
            return []
        __result = []
        for __item in __result_json['results']:
            try:
                if int(float(__item['header']['similarity'])) < 60:
                    continue
                else:
                    __result.append({'similarity': __item['header']['similarity'],
                                     'thumbnail': __item['header']['thumbnail'],
                                     'index_name': __item['header']['index_name'],
                                     'ext_urls': __item['data']['ext_urls']})
            except Exception as res_err:
                log.logger.warning(f"{__name__}: get_identify_result ERROR: {res_err}, can not resolve results")
                continue
        return __result

    # 获取识别结果 Saucenao模块
    async def get_ascii2d_identify_result(url: str) -> list:
        async def get_ascii2d_redirects(__url: str) -> dict:
            timeout_count = 0
            while timeout_count < 3:
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as __session:
                        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                 'Chrome/83.0.4103.116 Safari/537.36',
                                   'accept-language': 'zh-CN,zh;q=0.9'}
                        async with __session.get(url=__url, headers=headers, timeout=timeout,
                                                 allow_redirects=False) as resp:
                            res_headers = resp.headers
                            res_dict = {'error': False, 'body': dict(res_headers)}
                    return res_dict
                except Exception as err:
                    log.logger.warning(f'{__name__}: get_ascii2d_redirects ERROR: {err}. '
                                       f'Occurred in try {timeout_count + 1} using url: {__url}')
                finally:
                    timeout_count += 1
            else:
                log.logger.warning(f'{__name__}: get_ascii2d_redirects ERROR: '
                                   f'Timeout {timeout_count}, using url: {__url}')
                return {'error': True, 'body': None}

        async def get_ascii2d_result(__url: str) -> str:
            timeout_count = 0
            while timeout_count < 3:
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as __session:
                        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                 'Chrome/83.0.4103.116 Safari/537.36',
                                   'accept-language': 'zh-CN,zh;q=0.9'}
                        async with __session.get(url=__url, headers=headers, timeout=timeout) as resp:
                            res_headers = await resp.text()
                    return res_headers
                except Exception as err:
                    log.logger.warning(f'{__name__}: get_ascii2d_result ERROR: {err}. '
                                       f'Occurred in try {timeout_count + 1} using url: {__url}')
                finally:
                    timeout_count += 1
            else:
                log.logger.warning(f'{__name__}: get_ascii2d_result ERROR: '
                                   f'Timeout {timeout_count}, using url: {__url}')
                return ''

        search_url = f'{API_URL_ASCII2D}{url}'
        __result_json = await get_ascii2d_redirects(__url=search_url)
        if not __result_json['error']:
            ascii2d_color_url = __result_json['body']['Location']
            ascii2d_bovw_url = re.sub(
                r'https://ascii2d\.net/search/color/', r'https://ascii2d.net/search/bovw/', ascii2d_color_url)
        else:
            log.logger.warning(f'{__name__}: get_ascii2d_identify_result ERROR: 获取识别结果url发生错误, 错误信息详见日志.')
            return []

        color_res = await get_ascii2d_result(ascii2d_color_url)
        bovw_res = await get_ascii2d_result(ascii2d_bovw_url)

        pre_bs_list = []
        if color_res:
            pre_bs_list.append(color_res)
        if bovw_res:
            pre_bs_list.append(bovw_res)
        if not pre_bs_list:
            log.logger.warning(f'{__name__}: get_ascii2d_identify_result ERROR: 获取识别结果异常, 错误信息详见日志.')
            return []

        __result = []

        for result in pre_bs_list:
            try:
                gallery_soup = BeautifulSoup(result, 'lxml')
                # 模式
                search_mode = gallery_soup.find('h5', {'class': 'p-t-1 text-xs-center'}).get_text(strip=True)
                # 每一个搜索结果
                row = gallery_soup.find_all('div', {'class': 'row item-box'})
            except Exception as page_err:
                log.logger.warning(f'{__name__}: get_ascii2d_identify_result ERROR: {page_err}, 解析结果页时发生错误.')
                continue
            # ascii2d搜索偏差过大,pixiv及twitter结果只取第一个
            pixiv_count = 0
            twitter_count = 0
            for row_item in row:
                # 对每个搜索结果进行解析
                try:
                    detail = row_item.find('div', {'class': 'detail-box gray-link'})
                    is_null = detail.get_text(strip=True)
                    if not is_null:
                        continue
                    # 来源部分,ascii2d网页css调整大概率导致此处解析失败,调试重点关注
                    source_type = detail.find('h6').find('small').get_text(strip=True)
                    if source_type == 'pixiv':
                        if pixiv_count > 0:
                            break
                        else:
                            pixiv_count += 1
                    elif source_type == 'twitter':
                        if twitter_count > 0:
                            break
                        else:
                            twitter_count += 1
                    else:
                        continue
                    source = detail.find('h6').get_text('/', strip=True)
                    source_url = detail.find('h6').find('a', {'title': None, 'style': None}).get('href')
                    # 预览图部分,ascii2d网页css调整大概率导致此处解析失败,调试重点关注
                    preview_img_url = row_item. \
                        find('div', {'class': 'col-xs-12 col-sm-12 col-md-4 col-xl-4 text-xs-center image-box'}). \
                        find('img').get('src')
                    __result.append({'similarity': 'null',
                                     'thumbnail': f'https://ascii2d.net{preview_img_url}',
                                     'index_name': f'ascii2d - {search_mode} - {source}',
                                     'ext_urls': source_url})
                except Exception as row_err:
                    log.logger.warning(f'{__name__}: get_ascii2d_identify_result ERROR: {row_err}, 解搜索结果条目时发生错误.')
                    continue

        return __result

    # 命令主要部分
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令')
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    image_msg = f'请发送你想要识别的图片: '
    session.get('image', prompt=image_msg,
                arg_filters=[controllers.handle_cancellation(session),
                             validators.not_empty('输入不能为空~'),
                             validators.match_regex(r'^(\[CQ\:image\,file\=)', '你发送的似乎不是图片呢, 请重新发送~',
                                                    fullmatch=False)])
    if session.current_key == 'image':
        # aiocqhttp 可直接获取url
        try:
            session.state['image_url'] = session.current_arg_images[0]
        except Exception as e:
            log.logger.debug(f'{__name__}: Searchimage: {e}. 在Mirai框架中运行')
            # mirai无法直接获取图片url
            # 针对mirai-native的cqhttp插件的cq码适配
            if session_type == 'group':
                imageid = re.sub(r'^(\[CQ:image,file={)', '', session.current_arg)
                imageid = re.sub(r'(}\.mirai\.mnimg])$', '', imageid)
                imageid = re.sub(r'-', '', imageid)
                imageurl = f'https://gchat.qpic.cn/gchatpic_new/0/0-0-{imageid}/0?term=2'
                session.state['image_url'] = imageurl
            elif session_type == 'private':
                imageid = re.sub(r'^(\[CQ:image,file=/)', '', session.current_arg)
                imageid = re.sub(r'(\.mnimg])$', '', imageid)
                imageurl = f'https://gchat.qpic.cn/gchatpic_new/0/{imageid}/0?term=2'
                session.state['image_url'] = imageurl
    image_url = session.state['image_url']
    try:
        await session.send('获取识别结果中, 请稍后~')
        identify_result = await get_identify_result(url=image_url)
        identify_ascii2d_result = await get_ascii2d_identify_result(url=image_url)
        # 合并搜索结果
        identify_result.extend(identify_ascii2d_result)
        if identify_result:
            for item in identify_result:
                try:
                    if type(item['ext_urls']) == list:
                        ext_urls = ''
                        for urls in item['ext_urls']:
                            ext_urls += f'{urls}\n'
                        ext_urls = ext_urls.strip()
                    else:
                        ext_urls = item['ext_urls']
                        ext_urls = ext_urls.strip()
                    img_b64 = await pic_2_base64(item['thumbnail'])
                    if img_b64 == '':
                        msg = f"识别结果: {item['index_name']}\n\n相似度: {item['similarity']}\n资源链接: {ext_urls}"
                        await session.send(msg)
                    else:
                        img_seg = MessageSegment.image(img_b64)
                        msg = f"识别结果: {item['index_name']}\n\n相似度: {item['similarity']}\n资源链接: {ext_urls}\n{img_seg}"
                        await session.send(msg)
                except Exception as e:
                    log.logger.warning(f'{__name__}: 处理和发送识别结果时发生了错误: {e}')
                    continue
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 使用searchimage成功搜索了一张图片')
            return
        else:
            await session.send('没有找到相似度足够高的图片QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 使用了searchimage, 但没有找到相似的图片')
            return
    except Exception as e:
        await session.send('识图失败, 发生了意外的错误QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令searchimage时发生了错误: {e}')
        return


# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@searchimage.args_parser
async def _(session: CommandSession):
    # 检查是否允许在群组内运行
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            return
    elif session_type == 'private':
        pass
    else:
        return
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()

    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            session.finish('该命令不支持参数QAQ')
        else:
            return

    if not stripped_arg:
        # 用户没有发送有效的参数, 则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('你似乎发送了一个空消息呢, 请重新输入~')
    return
