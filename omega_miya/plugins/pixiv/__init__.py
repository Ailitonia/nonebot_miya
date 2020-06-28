import re
from omega_miya.plugins.Group_manage.group_permissions import *
from aiocqhttp import MessageSegment
from nonebot import on_command, CommandSession, permission
from omega_miya.plugins.pixiv.config import pixiv_src_path
from omega_miya.plugins.pixiv.src.illust_info import get_illust_info, illust_r18_check
from omega_miya.plugins.pixiv.src.dl_illust import *
from omega_miya.plugins.pixiv.src.pic_2_base64 import *
from omega_miya.plugins.pixiv.src.weekly_daily_ranking import \
    get_rand_daily_ranking, get_rand_weekly_ranking, get_rand_monthly_ranking


__plugin_name__ = 'Pixiv助手'
__plugin_usage__ = r'''【Pixiv助手】

使用这个命令可以查看Pixiv插画，以及随机日榜、周榜、及月榜

用法：
/pixiv [PID]
/pixiv 日榜
/pixiv 周榜
/pixiv 月榜'''


# on_command 装饰器将函数声明为一个命令处理器
# 这里 pid 为命令的名字
@on_command('pixiv', only_to_me=False, permission=permission.GROUP)
async def pixiv(session: CommandSession):
    group_id = session.event.group_id
    if group_id not in query_all_command_groups():
        return
    # 从会话状态（session.state）中获取pid，如果当前不存在，则询问用户
    pid = session.get('pixiv', prompt='你是想看周榜，还是日榜，还是作品呢？想看特定作品的话请输入PixivID~')
    # 获取illust信息
    try:
        illustinfo = await get_illust_info(pid)
        # 检查图片状态
        if not illustinfo['status']:
            await session.send('没有这张图，你是不是手滑输错了？')
        else:
            # 检查R18
            if illustinfo['is_r18']:
                await session.send('不准开车车！！')
            # 正常情况
            else:
                await session.send('稍等，正在下载图片~')
                # 下载图片
                dl_illust(pid, illustinfo['regular_url'])
                # 发送base64图片
                illust_b64 = pic_2_base64(illust_full_path + str(pid) + '.jpg')
                img_seg = MessageSegment.image(illust_b64)
                # 发送图片
                await session.send(img_seg)
                # 发送图片信息
                await session.send(illustinfo['illust_info'])
    # 有问题的话大概率都是网络问题，不是也要推锅给网络OvO
    except:
        await session.send('似乎不能访问Pixiv呢QAQ')


# weather.args_parser 装饰器将函数声明为 pid 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@pixiv.args_parser
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
            # 第一次运行参数不为空，意味着用户直接将PID跟在命令名后面，作为参数传入
            if stripped_arg == '周榜':
                session.state['pixiv'] = get_rand_weekly_ranking()
            elif stripped_arg == '日榜':
                session.state['pixiv'] = get_rand_daily_ranking()
            elif stripped_arg == '月榜':
                session.state['pixiv'] = get_rand_monthly_ranking()
            elif re.match(r'^\d+$', stripped_arg):
                session.state['pixiv'] = stripped_arg
            else:
                session.finish('你输入的命令好像不对呢……请输入"月榜"、"周榜"、"日榜"或者PixivID试试吧~')
        return

    if not stripped_arg:
        # 用户没有发送有效的PID（而是发送了空白字符），则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('你还没告诉我你想看什么呢~')

    # 如果当前正在向用户询问更多信息，且用户输入有效，则放入会话状态
    if stripped_arg == '周榜':
        session.state[session.current_key] = get_rand_weekly_ranking()
    elif stripped_arg == '月榜':
        session.state[session.current_key] = get_rand_monthly_ranking()
    elif stripped_arg == '日榜':
        session.state[session.current_key] = get_rand_daily_ranking()
    elif re.match(r'^\d+$', stripped_arg):
        session.state[session.current_key] = stripped_arg
    else:
        session.finish('你输入的命令好像不对呢……请输入"月榜"、"周榜"、"日榜"或者PixivID试试吧~')
