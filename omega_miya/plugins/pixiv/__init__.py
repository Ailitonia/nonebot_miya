import re
import aiohttp
from omega_miya.plugins.Group_manage.group_permissions import *
from aiocqhttp import MessageSegment
from nonebot import on_command, CommandSession, permission, log
'''
from omega_miya.plugins.pixiv.config import pixiv_src_path
from omega_miya.plugins.pixiv.src.illust_info import get_illust_info, illust_r18_check
from omega_miya.plugins.pixiv.src.dl_illust import *
from omega_miya.plugins.pixiv.src.pic_2_base64 import *
from omega_miya.plugins.pixiv.src.weekly_daily_ranking import \
    get_rand_daily_ranking, get_rand_weekly_ranking, get_rand_monthly_ranking
'''


__plugin_name__ = 'Pixiv助手'
__plugin_usage__ = r'''【Pixiv助手】

使用这个命令可以查看Pixiv插画, 以及随机日榜、周榜、及月榜

用法: 
/pixiv [PID]
/pixiv 日榜
/pixiv 周榜
/pixiv 月榜'''

API_KEY = '123456abc'
RANK_API_URL = 'https://api.example.com'
SEARCH_API_URL = 'https://api.example.com'
# !!!这里使用了另外一个下载p站图片的私人api,请用下方不使用web api的版本的源码替换!!!


async def fetch(url: str, paras: dict) -> dict:
    timeout_count = 0
    while timeout_count < 3:
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                async with session.get(url=url, params=paras, headers=headers, timeout=timeout) as resp:
                    json = await resp.json()
            return json
        except Exception as e:
            log.logger.warning(f'{__name__}: fetch ERROR: {e}. '
                               f'Occurred in try {timeout_count + 1} using paras: {paras}')
        finally:
            timeout_count += 1
    else:
        log.logger.warning(f'{__name__}: fetch ERROR: Timeout {timeout_count}, using paras: {paras}')
        return {'error': 'error'}


# on_command 装饰器将函数声明为一个命令处理器
# 这里 pid 为命令的名字
@on_command('pixiv', only_to_me=False, permission=permission.EVERYBODY)
async def pixiv(session: CommandSession):
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
    # 从会话状态（session.state）中获取pid, 如果当前不存在, 则询问用户
    pid = session.get('pixiv', prompt='你是想看周榜, 还是日榜, 还是作品呢？想看特定作品的话请输入PixivID~')
    if pid == 'error':
        await session.send('似乎不能访问Pixiv呢QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取Pixiv资源被失败, 网络错误')
        return
    try:
        await session.send('稍等, 正在加载图片资源~')
        # 获取illust信息
        __payload = {'key': API_KEY, 'pid': pid}
        illustinfo = await fetch(url=SEARCH_API_URL, paras=__payload)
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')
        return
    try:
        # 检查图片状态
        if 'error' in illustinfo.keys():
            await session.send('加载失败, 网络超时或没有这张图QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取Pixiv资源被失败, 网络超时或 {pid} 不存在')
            return
        else:
            # 检查R18
            if illustinfo['is_r18']:
                await session.send('不准开车车！！')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取Pixiv资源被中止, {pid} 为R-18资源')
                return
            # 正常情况
            else:
                img_seg = MessageSegment.image(illustinfo['pic_b64'])
                # 发送图片
                await session.send(img_seg)
                # 发送图片信息
                await session.send(illustinfo['illust_info'])
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功获取Pixiv资源: {pid}')
    # 有问题的话大概率都是网络问题, 不是也要推锅给网络OvO
    except Exception as e:
        await session.send('发生了未知的错误QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')

    '''不使用web api的版本
    if pid == 'error':
        await session.send('似乎不能访问Pixiv呢QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取Pixiv资源被失败, 网络错误')
        return
    try:
        # 获取illust信息
        illustinfo = await get_illust_info(pid)
        if illustinfo['status'] == 'error':
            await session.send('似乎不能访问Pixiv呢QAQ')
            log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取Pixiv资源被失败, 网络错误')
            return
    except Exception as e:
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')
        return
    try:
        # 检查图片状态
        if not illustinfo['status']:
            await session.send('没有这张图, 你是不是手滑输错了？')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取Pixiv资源被失败, {pid} 不存在')
            return
        else:
            # 检查R18
            if illustinfo['is_r18']:
                await session.send('不准开车车！！')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取Pixiv资源被中止, {pid} 为R-18资源')
                return
            # 正常情况
            else:
                await session.send('稍等, 正在下载图片~')
                # 下载图片
                dl_illust(pid, illustinfo['regular_url'])
                # 发送base64图片
                illust_b64 = pic_2_base64(illust_full_path + str(pid) + '.jpg')
                img_seg = MessageSegment.image(illust_b64)
                # 发送图片
                await session.send(img_seg)
                # 发送图片信息
                await session.send(illustinfo['illust_info'])
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功获取Pixiv资源: {pid}')
    # 有问题的话大概率都是网络问题, 不是也要推锅给网络OvO
    except Exception as e:
        await session.send('发生了未知的错误QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')
    '''


# weather.args_parser 装饰器将函数声明为 pid 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@pixiv.args_parser
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
            # 第一次运行参数不为空, 意味着用户直接将PID跟在命令名后面, 作为参数传入
            try:
                if stripped_arg == '周榜':
                    __payload = {'key': API_KEY, 'rank_mode': 'weekly'}
                    __res = await fetch(url=RANK_API_URL, paras=__payload)
                    if 'error' in __res.keys():
                        session.state['pixiv'] = 'error'
                    else:
                        session.state['pixiv'] = (await fetch(url=RANK_API_URL, paras=__payload))['pid']
                elif stripped_arg == '日榜':
                    __payload = {'key': API_KEY, 'rank_mode': 'daily'}
                    __res = await fetch(url=RANK_API_URL, paras=__payload)
                    if 'error' in __res.keys():
                        session.state['pixiv'] = 'error'
                    else:
                        session.state['pixiv'] = (await fetch(url=RANK_API_URL, paras=__payload))['pid']
                elif stripped_arg == '月榜':
                    __payload = {'key': API_KEY, 'rank_mode': 'monthly'}
                    __res = await fetch(url=RANK_API_URL, paras=__payload)
                    if 'error' in __res.keys():
                        session.state['pixiv'] = 'error'
                    else:
                        session.state['pixiv'] = (await fetch(url=RANK_API_URL, paras=__payload))['pid']
                elif re.match(r'^\d+$', stripped_arg):
                    session.state['pixiv'] = stripped_arg
                else:
                    session.finish('你输入的命令好像不对呢……请输入"月榜"、"周榜"、"日榜"或者PixivID试试吧~')
            except Exception as e:
                log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')
                session.finish()

        return

    if not stripped_arg:
        # 用户没有发送有效的PID（而是发送了空白字符）, 则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('你还没告诉我你想看什么呢~')

    # 如果当前正在向用户询问更多信息, 且用户输入有效, 则放入会话状态
    if stripped_arg == '周榜':
        try:
            __payload = {'key': API_KEY, 'rank_mode': 'weekly'}
            __res = await fetch(url=RANK_API_URL, paras=__payload)
            if 'error' in __res.keys():
                session.state[session.current_key] = 'error'
            else:
                session.state[session.current_key] = (await fetch(url=RANK_API_URL, paras=__payload))['pid']
        except Exception as e:
            log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')
            session.finish()

    elif stripped_arg == '月榜':
        try:
            __payload = {'key': API_KEY, 'rank_mode': 'monthly'}
            __res = await fetch(url=RANK_API_URL, paras=__payload)
            if 'error' in __res.keys():
                session.state[session.current_key] = 'error'
            else:
                session.state[session.current_key] = (await fetch(url=RANK_API_URL, paras=__payload))['pid']
        except Exception as e:
            log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')
            session.finish()

    elif stripped_arg == '日榜':
        try:
            __payload = {'key': API_KEY, 'rank_mode': 'daily'}
            __res = await fetch(url=RANK_API_URL, paras=__payload)
            if 'error' in __res.keys():
                session.state[session.current_key] = 'error'
            else:
                session.state[session.current_key] = (await fetch(url=RANK_API_URL, paras=__payload))['pid']
        except Exception as e:
            log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令pixiv时发生了错误: {e}')
            session.finish()

    elif re.match(r'^\d+$', stripped_arg):
        session.state[session.current_key] = stripped_arg
    else:
        session.finish('你输入的命令好像不对呢……请输入"月榜"、"周榜"、"日榜"或者PixivID试试吧~')
