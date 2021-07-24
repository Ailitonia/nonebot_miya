import re
import aiohttp
from omega_miya.plugins.Group_manage.group_permissions import *
from nonebot import on_command, CommandSession, permission, log

__plugin_name__ = '开车'
__plugin_usage__ = r'''【开车】

使用这个命令可以开车

用法: 
/开车 [tag]  *搜索模式, 搜索对应tag
/开车 [ID]  *下载模式, ID是NH上的本子ID
'''

API_KEY = '123456abc'
API_URL = 'https://example.com/api/nhentai/'


async def fetch(url: str, paras: dict):
    timeout_count = 0
    while timeout_count < 3:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
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


@on_command('nhentai', aliases='开车', only_to_me=False, permission=permission.EVERYBODY)
async def nhentai(session: CommandSession):
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
    # 从会话状态（session.state）中获取tag, 如果当前不存在, 则询问用户
    mode = session.get('mode', prompt='模式？')
    gallery_tag = session.get('tag', prompt='想看什么？')
    gallery_id = session.get('gid', prompt='id是什么？')
    try:
        # 下载模式
        if mode == 0:
            await session.send('稍等, 正在下载中~')
            url = f'{API_URL}fetch_gallery/'
            __payload = {'key': API_KEY, 'gid': gallery_id}
            status = await fetch(url=url, paras=__payload)
            if 'error' in status.keys():
                await session.send('下载失败QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 使用API下载NH资源失败')
            else:
                __download_url = f'{API_URL}download/?fileid={gallery_id}'
                await session.send(f'下载完成~\n请访问如下链接下载文件: \n{__download_url}')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功使用API下载NH资源: {gallery_id}')
        # 搜索模式
        elif mode == 1:
            url = f'{API_URL}search/'
            __payload = {'key': API_KEY, 'tag': gallery_tag}
            __res = await fetch(url=url, paras=__payload)
            msg = ''
            for item in __res.values():
                msg += f'\nID: {item["id"]} / {item["title"]}\n'
            await session.send(f'已为你找到了如下结果: \n{msg}\n可通过id下载哦~')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功使用API搜索NH资源: {gallery_tag}')
    except Exception as e:
        # 有问题的话大概率都是网络问题, 不是也要推锅给网络OvO
        await session.send('似乎出现了网络问题呢QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令nhentai时发生了错误: {e}')


'''不使用web api的版本
@on_command('nhentai', aliases='开车', only_to_me=False, permission=permission.GROUP)
async def nhentai(session: CommandSession):
    group_id = session.event.group_id
    if not has_command_permissions(group_id):
    log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
        return
    # 从会话状态（session.state）中获取tag, 如果当前不存在, 则询问用户
    mode = session.get('mode', prompt='模式？')
    gallery_tag = session.get('tag', prompt='想看什么？')
    gallery_id = session.get('gid', prompt='id是什么？')
    try:
        # 下载模式
        if mode == 0:
            await session.send('稍等, 正在下载中~')
            await fetch_gallery(gallery_id=gallery_id)
            await session.send('下载完成~')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功使用API下载NH资源: {gallery_id}')
        # 搜索模式
        elif mode == 1:
            res_list = await search_gallery_by_tag(gallery_tag)
            msg = ''
            for item in res_list:
                msg += f'\nID:{item["id"]} / {item["title"]}'
            await session.send(f'已为你找到了如下结果: \n{msg}\n\n可通过id下载哦~')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功使用API搜索NH资源: {gallery_tag}')
    except:
        # 有问题的话大概率都是网络问题, 不是也要推锅给网络OvO
        await session.send('似乎出现了网络问题呢QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令nhentai时发生了错误: {e}')
'''


# weather.args_parser 装饰器将函数声明为 pid 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@nhentai.args_parser
async def _(session: CommandSession):
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
            splited_arg = stripped_arg.split()
            # 第一次运行参数不为空
            if len(splited_arg) == 1:
                if re.match(r'^\d+$', splited_arg[0]):
                    session.state['mode'] = 0
                    session.state['tag'] = None
                    session.state['gid'] = splited_arg[0]
                else:
                    session.state['mode'] = 1
                    session.state['tag'] = splited_arg[0]
                    session.state['gid'] = None
            elif len(splited_arg) > 1:
                session.state['mode'] = 1
                session.state['tag'] = ''
                session.state['gid'] = None
                for tag in splited_arg:
                    session.state['tag'] += f'{tag} '
                session.state['tag'] = session.state['tag'].strip()
        else:
            session.state['mode'] = 1
            # 什么参数都不带就默认搜索模式+汉化tag
            session.state['tag'] = 'chinese'
            session.state['gid'] = None
        return
