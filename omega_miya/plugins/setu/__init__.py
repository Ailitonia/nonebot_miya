from omega_miya.plugins.Group_manage.group_permissions import *
from aiocqhttp import MessageSegment
from nonebot import on_command, CommandSession, permission
from omega_miya.plugins.setu.config import setu_src_path
from omega_miya.plugins.setu.src.illust_info import get_illust_data
from omega_miya.plugins.setu.src.dl_illust import *
from omega_miya.plugins.setu.src.pic_2_base64 import *


__plugin_name__ = '来点涩图'
__plugin_usage__ = r'''【来点涩图】

用法：
/来点涩图'''


# on_command 装饰器将函数声明为一个命令处理器
# 这里 pid 为命令的名字
@on_command('setu', aliases='来点涩图', only_to_me=False, permission=permission.GROUP)
async def setu(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 从会话状态（session.state）中获取pid，如果当前不存在，则询问用户
    is_r18 = session.get('is_r18', prompt='想看R18？')
    tag = session.get('tag', prompt='什么tag？')
    try:
        if is_r18 == 0:
            # 获取illust信息
            illust_links = await get_illust_data(is_r18=is_r18, tag=tag)
            # 检查图片状态
            if not illust_links:
                await session.send('找不到涩图QAQ')
            else:
                await session.send('稍等，正在下载图片~')
                # 下载图片
                for item in illust_links:
                    dl_illust(item['pid'], item['url'])
                    # 发送base64图片
                    illust_b64 = pic_2_base64(illust_full_path + str(item['pid']) + '.jpg')
                    img_seg = MessageSegment.image(illust_b64)
                    # 发送图片
                    await session.send(img_seg)
        elif is_r18 == 1:
            # 获取illust信息
            illust_links = await get_illust_data(is_r18=is_r18, tag=tag)
            # 检查图片状态
            if not illust_links:
                await session.send('找不到涩图QAQ')
            else:
                await session.send('群里就发链接哦~')
                for item in illust_links:
                    await session.send(item['url'])
    except:
        # 有问题的话大概率都是网络问题，不是也要推锅给网络OvO
        await session.send('似乎出现了网络问题呢QAQ')


# weather.args_parser 装饰器将函数声明为 pid 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@setu.args_parser
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
            if len(splited_arg) == 1 and splited_arg[0] == 'r18':
                session.state['is_r18'] = 1
                session.state['tag'] = None
            elif len(splited_arg) == 1 and splited_arg[0] != 'r18':
                session.state['is_r18'] = 0
                session.state['tag'] = splited_arg[0]
            elif len(splited_arg) == 2 and splited_arg[0] == 'r18':
                session.state['is_r18'] = 1
                session.state['tag'] = splited_arg[1]
            elif len(splited_arg) == 2 and splited_arg[0] != 'r18':
                session.state['is_r18'] = 0
                session.state['tag'] = splited_arg[0]
            else:
                session.state['is_r18'] = 0
        else:
            session.state['is_r18'] = 0
            session.state['tag'] = None
        return
