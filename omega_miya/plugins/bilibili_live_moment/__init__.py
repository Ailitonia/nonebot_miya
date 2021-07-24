import re
import os
import xlwt
import aiohttp
from datetime import datetime
from nonebot.command.argfilter import validators, controllers
from nonebot import on_command, CommandSession, permission, log
from omega_miya.plugins.bilibili_live_moment.util import add_live_alias_to_db, query_live_alias_list, \
    query_alias_rid_list, add_note_to_db, query_all_notes_list
from omega_miya.plugins.bilibili_live_monitor.get_live_info import get_live_info, get_user_info
from omega_miya.plugins.Group_manage.group_permissions import *

__plugin_name__ = '直播记录'
__plugin_usage__ = r'''【直播事件记录】

方便地记录直播时发生的事件
记录时会自动带入当前时间, 因此在记录时请尽量保证不要拖延太久, 否则会对后期剪辑man造成巨大心理阴影哦OvO

用法: 
/新增(更新)记录直播间 <房间号> <别名> *群管理员可用

/查看(查询)记录直播间

/记录 <别名> <记录内容>

/导出直播记录'''


# 本插件依赖bilibili_live_monitor插件！！！


@on_command('bind_room_alias', aliases=('新增记录直播间', '更新记录直播间'), only_to_me=False,
            permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def bind_room_alias(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        await session.send('本命令不支持在私聊中使用QAQ')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令, 已中止命令执行')
        return
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    # 从会话状态（session.state）中获取sub_id, 如果当前不存在, 则询问用户
    __room_id = session.get('room_id', prompt='请输入直播间房间号: ',
                            arg_filters=[controllers.handle_cancellation(session),
                                         validators.not_empty('输入不能为空'),
                                         validators.match_regex(r'^\d+$', '房间号格式不对哦, 请重新输入~',
                                                                fullmatch=True)])
    __room_id = int(__room_id)
    try:
        # 获取直播间信息
        __live_info = await get_live_info(__room_id)
    except Exception as e:
        log.logger.warning(f'{__name__}: bind_room_alias: 获取直播间: {__room_id} 信息失败: {e}')
        return
    if __live_info['status'] == 'error':
        await session.send('似乎并没有这个直播间QAQ')
        log.logger.info(f'{__name__}:  bind_room_alias: 群组: {group_id}, 用户: {session.event.user_id} '
                        f'新增记录直播间失败, 没有找到该房间号: {__room_id} 对应的直播间')
        return
    else:
        try:
            __up_info = await get_user_info(__live_info['uid'])
        except Exception as e:
            log.logger.warning(f"{__name__}: bind_room_alias: 获取用户: {__live_info['uid']} 信息失败: {e}")
            return
        __up_name = __up_info['name']
        __bind_alias = session.get('alias', prompt=f'即将新增【{__up_name}】的直播间！\n请输入记录时将使用的别名: \n'
                                                   f'取消操作请输入"取消"',
                                   arg_filters=[controllers.handle_cancellation(session),
                                                validators.not_empty('输入不能为空')])
        if __bind_alias:
            # 向数据库添加新增的别名
            __is_success = await add_live_alias_to_db(room_id=__room_id,
                                                      up_name=str(__up_name), nickname=str(__bind_alias))
            if __is_success:
                await session.send(f'已成功新增【{__up_name}】的直播间信息, 记录别名为【{__bind_alias}】')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                f'已成功新增: {__up_name} 的直播间, 直播间id: {__room_id}, alias: {__bind_alias}')
            else:
                await session.send(f'新增直播间失败, 发生了意外的错误QAQ')
                log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                   f'新增直播间: {__room_id}, alias: {__bind_alias}失败, 错误信息见日志')
        else:
            log.logger.warning(f'{__name__}: bind_alias为空, 操作失败')


@bind_room_alias.args_parser
async def _(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            return
    elif session_type == 'private':
        return
    else:
        return
    # 去掉消息首尾的空白符
    stripped_arg = session.current_arg_text.strip()
    if session.is_first_run:
        # 该命令第一次运行（第一次进入命令会话）
        if stripped_arg:
            # 第一次运行参数不为空, 意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if len(splited_arg) == 2 and re.match(r'^\d+$', splited_arg[0]):
                session.state['room_id'] = splited_arg[0]
                session.state['alias'] = splited_arg[1]
                return
            else:
                session.finish('输入的格式好像不对呢,命令格式为\n【/新增记录直播间 <房间号> <别名>】\n, 请确认后重新输入命令吧~')
    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


@on_command('query_bind_room_alias', aliases=('查看记录直播间', '查询记录直播间'), only_to_me=False, permission=permission.GROUP)
async def query_bind_room_alias(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        await session.send('本命令不支持在私聊中使用QAQ')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令, 已中止命令执行')
        return
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    live_alias_list = query_live_alias_list()
    if not live_alias_list:
        await session.send('还没有记录任何直播间信息QAQ')
        log.logger.info(f'{__name__}: query_bind_room_alias: '
                        f'群组: {group_id}, 用户: {session.event.user_id} 查询了记录直播间')
        return
    msg = ''
    try:
        for item in live_alias_list:
            __name = item['name']
            __nickname = item['nickname']
            msg += f'\n【{__name}//{__nickname}】'
        await session.send(f'已记录以下直播间信息: \n（名称//别名）\n{msg}')
        log.logger.info(f'{__name__}: query_bind_room_alias: '
                        f'群组: {group_id}, 用户: {session.event.user_id} 查询了记录直播间')
    except Exception as e:
        log.logger.warning(f'{__name__}: query_bind_room_alias: '
                           f'群组: {group_id}, 用户: {session.event.user_id} 试图查询记录直播间时发生了错误: {e}')


@on_command('note_live_moment', aliases='记录', only_to_me=False, permission=permission.EVERYBODY)
async def note_live_moment(session: CommandSession):
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
    __alias = session.get('alias', prompt=f'请输入想要记录的直播间别名: ',
                          arg_filters=[controllers.handle_cancellation(session),
                                       validators.not_empty('输入不能为空')])
    __description = session.get('description', prompt=f'请输入想要记录的内容: ',
                                arg_filters=[controllers.handle_cancellation(session),
                                             validators.not_empty('输入不能为空')])
    __room_id = query_alias_rid_list(__alias)
    if __room_id == -1:
        await session.send(f'未录入信息的直播间: {__alias}, 请检查是否录入了直播间信息')
        log.logger.info(f'{__name__}: note_live_moment: '
                        f'群组: {group_id}, 用户: {session.event.user_id} 试图记录未记录信息的直播间: {__alias}')
        return
    try:
        __live_info = await get_live_info(room_id=__room_id)
    except Exception as e:
        await session.send('获取直播间信息失败, 请重试')
        log.logger.warning(f'{__name__}: note_live_moment: 获取直播间: {__room_id}信息失败: {e}')
        return
    try:
        if __live_info['status'] == 1:
            __live_title = __live_info['title']
            __live_start_time = datetime.strptime(__live_info['time'], '%Y-%m-%d %H:%M:%S')
            __note_real_time = datetime.now()
            __note_time = __note_real_time - __live_start_time
            __is_success = await add_note_to_db(room_id=__room_id, live_title=__live_title, description=__description,
                                                live_start_time=__live_start_time, note_real_time=__note_real_time,
                                                record_by=session.event.user_id, record_group=group_id,
                                                note_time=__note_time)
            if __is_success:
                await session.send(f'已成功记录【{__alias}】直播间事件。\n当前直播间已播送时间: {__note_time}')
                log.logger.info(f'{__name__}: note_live_moment: '
                                f'群组: {group_id}, 用户: {session.event.user_id} 已记录直播间: {__room_id}/{__live_title}事件')
            else:
                await session.send(f'发生了意外的错误, 记录失败QAQ, 请重新试试吧~')
                log.logger.warning(f'{__name__}: note_live_moment: '
                                   f'群组: {group_id}, 用户: {session.event.user_id} 已记录直播间: {__room_id}/{__live_title}'
                                   f'事件时发生错误')
            return
        else:
            __live_title = __live_info['title']
            __live_start_time = datetime.now()
            __note_real_time = datetime.now()
            __note_time = __note_real_time - __live_start_time
            __is_success = await add_note_to_db(room_id=__room_id, live_title=__live_title, description=__description,
                                                live_start_time=__live_start_time, note_real_time=__note_real_time,
                                                record_by=session.event.user_id, record_group=group_id,
                                                note_time=__note_time)
            if __is_success:
                await session.send(f'已成功记录【{__alias}】直播间事件。\n但当前直播间未开播, 无法记录已播出时间。')
                log.logger.info(f'{__name__}: note_live_moment: '
                                f'群组: {group_id}, 用户: {session.event.user_id} 已记录直播间: {__room_id}/{__live_title}事件')
            else:
                await session.send(f'发生了意外的错误, 记录失败QAQ, 请重新试试吧~')
                log.logger.warning(f'{__name__}: note_live_moment: '
                                   f'群组: {group_id}, 用户: {session.event.user_id} 已记录直播间: {__room_id}/{__live_title}'
                                   f'事件时发生错误')
            return
    except Exception as e:
        log.logger.warning(f'{__name__}: note_live_moment: '
                           f'群组: {group_id}, 用户: {session.event.user_id} 已记录直播间: {__room_id}事件失败: {e}')
        return


@note_live_moment.args_parser
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
            # 第一次运行参数不为空, 意味着用户直接将参数跟在命令名后面
            # 分割参数
            splited_arg = stripped_arg.split()
            if len(splited_arg) == 2:
                session.state['alias'] = splited_arg[0]
                session.state['description'] = splited_arg[1]
                return
            else:
                session.finish('输入的格式好像不对呢, 命令格式为\n【/记录 <别名> <记录内容>】\n, 请确认后重新输入命令吧~')
        else:
            session.finish('输入的格式好像不对呢, 命令格式为\n【/记录 <别名> <记录内容>】\n, 请确认后重新输入命令吧~')
    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


@on_command('query_all_notes', aliases='导出直播记录', only_to_me=False, permission=permission.EVERYBODY)
async def query_all_notes(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if not has_command_permissions(group_id):
            await session.send('本群组没有执行命令的权限呢QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id} 没有命令权限, 已中止命令执行')
            return
    elif session_type == 'private':
        await session.send('本命令不支持在私聊中使用QAQ')
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}中使用了命令, 已中止命令执行')
        return
    else:
        log.logger.info(f'{__name__}: 用户: {session.event.user_id} 在{session_type}环境中使用了命令, 已中止命令执行')
        return
    all_notes_list = query_all_notes_list()
    all_alias_list = query_live_alias_list()
    if not all_notes_list:
        await session.send('当前没有任何记录QAQ')
        log.logger.info(f'{__name__}: query_all_notes: '
                        f'群组: {group_id}, 用户: {session.event.user_id} 导出了直播记录')
        return
    await session.send(f'正在导出, 请稍后~')
    try:
        index = {0: 'room_id', 1: 'live_title', 2: 'live_start_time', 3: 'note_real_time', 4: 'note_time',
                 5: 'description', 6: 'created_at', 7: 'updated_at'}
        f = xlwt.Workbook()
        # 写入记录信息
        notes_data = f.add_sheet(u'notes_data', cell_overwrite_ok=True)
        for i in range(len(index)):
            notes_data.write(0, i, index[i])
        for row in range(len(all_notes_list)):
            for col in range(len(index)):
                notes_data.write(row+1, col, str(all_notes_list[row][col]))
        # 写入房间信息
        room_data = f.add_sheet(u'room_data', cell_overwrite_ok=True)
        room_data.write(0, 0, 'room_id')
        room_data.write(0, 1, 'name')
        room_data.write(0, 2, 'alias')
        for row in range(len(all_alias_list)):
            room_data.write(row + 1, 0, str(all_alias_list[row]['room_id']))
            room_data.write(row + 1, 1, str(all_alias_list[row]['name']))
            room_data.write(row + 1, 2, str(all_alias_list[row]['nickname']))
        save_path = os.path.join(os.path.dirname(__file__), 'export')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        export_file_name = f"{str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))}.xls"
        export_full_path = os.path.join(save_path, export_file_name)
        f.save(export_full_path)
    except Exception as e:
        log.logger.warning(f'{__name__}: query_bind_room_alias: '
                           f'群组: {group_id}, 用户: {session.event.user_id} 试图导出查询记录时发生了错误: {e}')
        return
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as clientsession:
            url = 'https://moepic.amoeloli.xyz/apiproxy/api/upload'
            data = aiohttp.FormData()
            data.add_field('upload',
                           open(export_full_path, 'rb'),
                           filename=export_file_name,
                           content_type='application/vnd.ms-excel')
            async with clientsession.post(url, data=data) as resp:
                resp_json = await resp.json()
    except Exception as e:
        await session.send(f'导出直播间记录失败了, 操作超时')
        log.logger.warning(f'{__name__}: query_bind_room_alias: '
                           f'群组: {group_id}, 用户: {session.event.user_id} 在上传查询记录时发生了错误: {e}')
        return
    try:
        if resp.status == 200 and resp_json['code'] == 0:
            d_url = f"https://moepic.amoeloli.xyz/apiproxy{resp_json['fileName']}"
            await session.send(f'已成功导出直播间记录, 点击以下链接下载: \n{d_url}')
            log.logger.info(f'{__name__}: query_all_notes: '
                            f'群组: {group_id}, 用户: {session.event.user_id} 已成功导出直播间记录')
        else:
            await session.send(f'导出直播间记录失败了, 可能是在上传记录时发生了错误QAQ')
            log.logger.warning(f'{__name__}: query_all_notes: '
                               f'群组: {group_id}, 用户: {session.event.user_id} 导出直播间记录失败, 可能是网络问题')
    except Exception as e:
        await session.send(f'导出直播间记录失败了, 操作超时')
        log.logger.warning(f'{__name__}: query_all_notes: '
                           f'群组: {group_id}, 用户: {session.event.user_id} 在获取上传结果时发生了错误: {e}')
        return
