import re
from omega_miya.plugins.Group_manage.group_permissions import *
from nonebot.command.argfilter import validators, controllers
from nonebot import on_command, CommandSession, permission, MessageSegment, log
from omega_miya.plugins.sticker_maker.src.util import sticker_maker_main, pic_2_base64

__plugin_name__ = '表情包助手'
__plugin_usage__ = r'''【表情包助手】

快速制作表情包

用法: 
直接使用命令进入向导模式

/表情包
'''


# on_command 装饰器将函数声明为一个命令处理器
# 这里 pid 为命令的名字
@on_command('stickermacker', aliases='表情包', only_to_me=False, permission=permission.EVERYBODY)
async def stickermacker(session: CommandSession):
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

    # 定义模板名称、类型, 处理模板正则
    sticker_temp = {
        '默认': {'name': 'default', 'type': 'default', 'text_part': 1, 'help_msg': '该模板不支持gif'},
        '白底': {'name': 'whitebg', 'type': 'default', 'text_part': 1, 'help_msg': '该模板不支持gif'},
        '小天使': {'name': 'littleangel', 'type': 'default', 'text_part': 1, 'help_msg': '该模板不支持gif'},
        '有内鬼': {'name': 'traitor', 'type': 'static', 'text_part': 1, 'help_msg': '该模板字数限制100（x）'},
        '王境泽': {'name': 'wangjingze', 'type': 'gif', 'text_part': 4, 'help_msg': '请检查文本分段'},
        '为所欲为': {'name': 'sorry', 'type': 'gif', 'text_part': 9, 'help_msg': '请检查文本分段'}
    }
    name_msg = ''
    name_re = r'^(Placeholder'
    for item in sticker_temp.keys():
        name_msg += f'\n【{item}】'
        name_re += fr'|{item}'
    name_re += r')$'

    temp_msg = f'请输入你想要制作的表情包模板: {name_msg}'

    # 从会话状态（session.state）中获取模板名称, 如果当前不存在, 则询问用户
    get_sticker_temp = session.get('sticker_temp', prompt=temp_msg,
                                   arg_filters=[controllers.handle_cancellation(session),
                                                validators.not_empty('输入不能为空~'),
                                                validators.match_regex(fr'{name_re}', '没有这个模板, 请重新输入~',
                                                                       fullmatch=True)])

    if get_sticker_temp == 'Placeholder':
        get_sticker_temp = 'default'

    # 获取模板名称、类型
    sticker_temp_name = sticker_temp[get_sticker_temp]['name']
    sticker_temp_type = sticker_temp[get_sticker_temp]['type']
    sticker_temp_text_part = sticker_temp[get_sticker_temp]['text_part']

    # 判断该模板表情图片来源
    if sticker_temp_type in ['static', 'gif']:
        sticker_image_url = 'null'
    else:
        image_msg = f'请发送你想要制作的表情包的图片: '
        session.get('sticker_image', prompt=image_msg,
                    arg_filters=[controllers.handle_cancellation(session),
                                 validators.not_empty('输入不能为空~'),
                                 validators.match_regex(r'^(\[CQ\:image\,file\=)', '你发送的似乎不是图片呢, 请重新发送~',
                                                        fullmatch=False)])
        if session.current_key == 'sticker_image':
            # aiocqhttp 可直接获取url
            try:
                session.state['sticker_image_url'] = session.current_arg_images[0]
            except Exception as e:
                log.logger.debug(f'{__name__}: stickermacker: {e}. 在Mirai框架中运行')
                # mirai无法直接获取图片url
                # 针对mirai-native的cqhttp插件的cq码适配
                if session_type == 'group':
                    imageid = re.sub(r'^(\[CQ:image,file={)', '', session.current_arg)
                    imageid = re.sub(r'(}\.mirai\.mnimg])$', '', imageid)
                    imageid = re.sub(r'-', '', imageid)
                    imageurl = f'https://gchat.qpic.cn/gchatpic_new/0/0-0-{imageid}/0?term=2'
                    session.state['sticker_image_url'] = imageurl
                elif session_type == 'private':
                    imageid = re.sub(r'^(\[CQ:image,file=/)', '', session.current_arg)
                    imageid = re.sub(r'(\.mnimg])$', '', imageid)
                    imageurl = f'https://gchat.qpic.cn/gchatpic_new/0/{imageid}/0?term=2'
                    session.state['sticker_image_url'] = imageurl
        sticker_image_url = session.state['sticker_image_url']

    # 获取制作表情包所需文字
    if sticker_temp_text_part > 1:
        text_msg = f'请输入你想要制作的表情包的文字: \n当前模板文本分段数:【{sticker_temp_text_part}】' \
                   f'\n\n注意: 请用【#】号分割文本不同段落，不同模板适用的文字字数及段落数有所区别'
    else:
        text_msg = f'请输入你想要制作的表情包的文字: \n注意: 不同模板适用的文字字数有所区别'
    sticker_text = session.get('sticker_text', prompt=text_msg,
                               arg_filters=[controllers.handle_cancellation(session),
                                            validators.not_empty('输入不能为空~')])

    if len(sticker_text.strip().split('#')) != sticker_temp_text_part:
        eg_msg = r'我就是饿死#死外边 从这里跳下去#也不会吃你们一点东西#真香'
        await session.send(f"表情制作失败QAQ, 文本分段数错误\n当前模板文本分段数:【{sticker_temp_text_part}】\n\n示例: \n{eg_msg}")
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 制作表情时失败, 文本分段数错误.')
        return

    try:
        sticker_path = await sticker_maker_main(url=sticker_image_url, temp=sticker_temp_name, text=sticker_text,
                                                sticker_temp_type=sticker_temp_type)
        if not sticker_path:
            await session.send(f"表情制作失败QAQ, 请注意模板要求\n小提示:{sticker_temp[get_sticker_temp]['help_msg']}")
            log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 制作表情时失败.')
            return

        '''
        # 发送base64图片
        sticker_b64 = await pic_2_base64(sticker_path)
        sticker_seg = MessageSegment.image(sticker_b64)
        '''

        # 直接用文件构造消息段
        sticker_seg = MessageSegment.image(f'file:///{sticker_path}')

        # 发送图片
        await session.send(sticker_seg)
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功制作了一个表情')
    except Exception as e:
        await session.send('表情制作失败, 发生了意外的错误QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令stickermacker时发生了错误: {e}')
        return


# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@stickermacker.args_parser
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
            session.finish('该命令不支持参数~')
        else:
            return

    if not stripped_arg:
        # 用户没有发送有效的参数, 则提示重新输入
        # 这里 session.pause() 将会发送消息并暂停当前会话（该行后面的代码不会被运行）
        session.pause('你似乎发送了一个空消息呢, 请重新输入~')
    return
