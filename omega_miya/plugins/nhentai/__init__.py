import re
import requests
from omega_miya.plugins.Group_manage.group_permissions import *
from nonebot import on_command, CommandSession, permission

__plugin_name__ = '开车'
__plugin_usage__ = r'''【开车】

使用这个命令可以开车

用法：
/开车 [tag]  *搜索模式，搜索对应tag
/开车 [ID]  *下载模式，ID是NH上的本子ID
'''

API_KEY = '22f2ea8a8e361a93e4517d4ed3039b2c'
API_URL = 'https://moepic.amoeloli.xyz/apiproxy/api/nhentai/'


@on_command('nhentai', aliases='开车', only_to_me=False, permission=permission.GROUP)
async def nhentai(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 从会话状态（session.state）中获取tag，如果当前不存在，则询问用户
    mode = session.get('mode', prompt='模式？')
    gallery_tag = session.get('tag', prompt='想看什么？')
    gallery_id = session.get('gid', prompt='id是什么？')
    try:
        # 下载模式
        if mode == 0:
            await session.send('稍等，正在下载中~')
            url = f'{API_URL}fetch_gallery/'
            __payload = {'key': API_KEY, 'gid': gallery_id}
            status = requests.get(url=url, params=__payload)
            if status.status_code == 200:
                __download_url = f'{API_URL}download/?fileid={gallery_id}'
                await session.send(f'下载完成~\n请访问如下链接下载文件：\n{__download_url}')
            else:
                await session.send('下载失败QAQ')
        # 搜索模式
        elif mode == 1:
            url = f'{API_URL}search/'
            __payload = {'key': API_KEY, 'tag': gallery_tag}
            __res = requests.get(url=url, params=__payload).json()
            msg = ''
            for item in __res.values():
                msg += f'\nID: {item["id"]} / {item["title"]}\n'
            await session.send(f'已为你找到了如下结果：\n{msg}\n可通过id下载哦~')
    except:
        # 有问题的话大概率都是网络问题，不是也要推锅给网络OvO
        await session.send('似乎出现了网络问题呢QAQ')


'''不使用web api的版本
@on_command('nhentai', aliases='开车', only_to_me=False, permission=permission.GROUP)
async def nhentai(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 从会话状态（session.state）中获取tag，如果当前不存在，则询问用户
    mode = session.get('mode', prompt='模式？')
    gallery_tag = session.get('tag', prompt='想看什么？')
    gallery_id = session.get('gid', prompt='id是什么？')
    try:
        # 下载模式
        if mode == 0:
            await session.send('稍等，正在下载中~')
            await fetch_gallery(gallery_id=gallery_id)
            await session.send('下载完成~')
        # 搜索模式
        elif mode == 1:
            res_list = await search_gallery_by_tag(gallery_tag)
            msg = ''
            for item in res_list:
                msg += f'\nID:{item["id"]} / {item["title"]}'
            await session.send(f'已为你找到了如下结果：\n{msg}\n\n可通过id下载哦~')
    except:
        # 有问题的话大概率都是网络问题，不是也要推锅给网络OvO
        await session.send('似乎出现了网络问题呢QAQ')
'''

# weather.args_parser 装饰器将函数声明为 pid 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@nhentai.args_parser
async def _(session: CommandSession):
    # 检查是否允许在群组内运行
    if session.event.group_id not in query_all_command_groups():
        session.finish('这个命令似乎不能在这个群里使用呢QAQ')
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
