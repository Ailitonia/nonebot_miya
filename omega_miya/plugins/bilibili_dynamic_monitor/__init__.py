import asyncio
import re
from omega_miya.plugins.bilibili_dynamic_monitor.get_dynamic_info import *
from omega_miya.plugins.bilibili_dynamic_monitor.util import pic_2_base64
from omega_miya.plugins.Group_manage.group_permissions import *
import nonebot
from nonebot import on_command, CommandSession, permission, MessageSegment, log
from nonebot.command.argfilter import validators, controllers

__plugin_name__ = 'B站动态订阅'
__plugin_usage__ = r'''【B站动态订阅】

随时更新up动态

/清空(重置)动态订阅 *群管理员可用

/订阅动态 *群管理员可用

/查看动态订阅'''

bot = nonebot.get_bot()


@on_command('clear_dy_sub', aliases=('清空动态订阅', '重置动态订阅'), only_to_me=False,
            permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def clear_dy_sub(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if group_id not in query_all_command_groups():
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
    try:
        __is_success = await clean_group_dy_sub_in_db(group_id=group_id)
        if not __is_success:
            await session.send('发生了意料之外的错误OvO')
            log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图清空群组动态订阅时发生了错误, '
                               f'数据库操作失败, 错误信息见日志.')
            return
        await session.send('已清空本群组动态订阅OvO')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 已成功清空群组动态订阅')
    except Exception as e:
        await session.send('发生了未知的错误QAQ')
        log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图清空群组动态订阅时发生了错误, '
                         f'error info: {e}.')


@on_command('new_dy_sub', aliases='订阅动态', only_to_me=False,
            permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def new_dy_sub(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if group_id not in query_all_command_groups():
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
    __sub_id = session.get('sub_id', prompt='请输入想要订阅的UP的UID: ',
                           arg_filters=[controllers.handle_cancellation(session),
                                        validators.not_empty('输入不能为空'),
                                        validators.match_regex(r'^\d+$', 'UID格式不对哦, 请重新输入~',
                                                               fullmatch=True)])
    # 获取UP的信息
    __up_info = await get_user_info(__sub_id)
    if __up_info['status'] == 'error':
        await session.send('似乎并没有这个UP呀QAQ')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 添加动态订阅失败, '
                        f'没有找到该UID: {__sub_id} 对应的UP')
        return
    else:
        __up_name = __up_info['name']
        __sub_check = session.get('check', prompt=f'即将订阅【{__up_name}】的动态！\n确认吗？\n\n【是/否】',
                                  arg_filters=[controllers.handle_cancellation(session),
                                               validators.not_empty('输入不能为空'),
                                               validators.match_regex(r'^[是否]$', '输入不对哦, 请重新输入~',
                                                                      fullmatch=True)])
        if __sub_check == '否':
            await session.send('那就不订阅好了QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 已取消添加动态订阅, 操作中止')
            return
        elif __sub_check == '是':
            try:
                # 首先更新动态订阅信息
                is_sub_dy_success = await add_dy_sub_to_db(sub_id=__sub_id, up_name=__up_name)
                if not is_sub_dy_success:
                    await session.send('发生了意料之外的错误QAQ')
                    log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                       f'试图添加: {__sub_id} 动态订阅时发生了错误, 更新订阅信息失败.')
                    return
                # 然后添加群组订阅
                is_add_group_sub_success = await add_group_dy_sub_to_db(sub_id=__sub_id, group_id=group_id)
                if not is_add_group_sub_success:
                    await session.send('发生了意料之外的错误QAQ')
                    log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                       f'试图添加: {__sub_id} 动态订阅时发生了错误, 向数据库写入群组订阅失败.')
                    return
                # 添加动态订阅时需要刷新该up的动态到数据库中
                __dy_info = await get_dynamic_info(__sub_id)
                for num in range(len(__dy_info)):
                    dy_id = __dy_info[num]['id']
                    dy_type = __dy_info[num]['type']
                    content = __dy_info[num]['content']
                    # 想数据库中写入动态信息
                    is_add_dy_info_success = \
                        await add_dy_info_to_db(user_id=__sub_id, dynamic_id=dy_id,
                                                dynamic_type=dy_type, content=content)
                    if not is_add_dy_info_success:
                        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                           f'试图添加: {__sub_id} 动态订阅时发生了错误, 向数据库写入动态{dy_id}信息失败, 已跳过.')
                await session.send(f'已成功的订阅【{__up_name}】的动态！')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                f'已成功添加: {__up_name} 的动态订阅')
            except Exception as e:
                await session.send('发生了未知的错误QAQ')
                log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                 f'试图添加: {__sub_id} 动态订阅时发生了错误, error info: {e}.')


@new_dy_sub.args_parser
async def _(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if group_id not in query_all_command_groups():
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
            if len(splited_arg) == 1 and re.match(r'^\d+$', splited_arg[0]):
                session.state['sub_id'] = splited_arg[0]
                return
            else:
                session.finish('输入的格式好像不对呢, 请确认后重新输入命令吧~')
    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


@on_command('query_group_dy_sub', aliases=('查看动态订阅', '查询动态订阅'), only_to_me=False, permission=permission.GROUP)
async def query_group_sub(session: CommandSession):
    group_id = session.event.group_id
    session_type = session.event.detail_type
    if session_type == 'group':
        if group_id not in query_all_command_groups():
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
    try:
        __group_sub_list = await query_group_dy_sub_list(group_id=group_id)
        if not __group_sub_list:
            await session.send('本群组还没有订阅任何动态QAQ')
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询了群组动态订阅')
            return
        msg = ''
        for __sub_id in __group_sub_list:
            __up_info = await get_user_info(__sub_id)
            __up_name = __up_info['name']
            msg += f'\n【{__up_name}】'
        await session.send(f'本群已订阅了以下UP的动态: \n{msg}')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询了群组动态订阅')
    except Exception as e:
        log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 查询群组动态订阅时发生了错误, '
                         f'error info: {e}.')


@nonebot.scheduler.scheduled_job(
    'cron',
    # year=None,
    # month=None,
    # day=None,
    # week=None,
    # day_of_week=None,
    # hour=None,
    minute='*/1',
    # second=None,
    # start_date=None,
    # end_date=None,
    # timezone=None,
    coalesce=True,
    misfire_grace_time=30
)
async def dynamic_check():
    async def check_user_dynamic(dy_uid):
        try:
            # 查询动态并返回动态类型及内容
            dynamic_info = await get_dynamic_info(dy_uid)
            log.logger.debug(f"{__name__}: 计划任务: dynamic_check, 已获取用户动态: {dy_uid}")
            # 获取订阅了该UP动态的所有群
            group_which_sub_dy = await query_group_whick_sub_dy(dy_uid)
            user_dy_id_list = query_up_dy_id_list(user_id=dy_uid)
            log.logger.debug(f"{__name__}: 计划任务: dynamic_check, 已获取动态订阅群组信息: {dy_uid}")
        except Exception as err:
            log.logger.error(f'{__name__}: 检查B站用户: {dy_uid} 动态时发生了错误, error info: {err}')
            return
        for num in range(len(dynamic_info)):
            try:
                # 如果有新的动态
                log.logger.debug(f"{__name__}: 计划任务: dynamic_check, 检查动态: {dynamic_info[num]['id']}")
                if dynamic_info[num]['id'] not in user_dy_id_list:
                    log.logger.info(f"{__name__}: 已检查到B站用户: {dynamic_info[num]['name']} 的新动态: "
                                    f"{dynamic_info[num]['id']}")
                    # 转发的动态
                    if dynamic_info[num]['type'] == 1:
                        # 原动态type=2, 带图片
                        if dynamic_info[num]['origin']['type'] == 2:
                            # 处理图片序列
                            pic_segs = ''
                            for pic_url in dynamic_info[num]['origin']['origin_pics']:
                                pic_b64 = await pic_2_base64(pic_url)
                                pic_segs += f'{MessageSegment.image(pic_b64)}\n'
                            msg = '{}转发了{}的动态！\n\n“{}”\n{}\n{}\n@{}: {}\n{}'.format(
                                dynamic_info[num]['name'], dynamic_info[num]['origin']['name'],
                                dynamic_info[num]['content'], dynamic_info[num]['url'], '=' * 16,
                                dynamic_info[num]['origin']['name'], dynamic_info[num]['origin']['content'],
                                pic_segs
                            )
                        # 原动态为其他类型, 无图
                        else:
                            msg = '{}转发了{}的动态！\n\n“{}”\n{}\n{}\n@{}: {}'.format(
                                dynamic_info[num]['name'], dynamic_info[num]['origin']['name'],
                                dynamic_info[num]['content'], dynamic_info[num]['url'], '=' * 16,
                                dynamic_info[num]['origin']['name'], dynamic_info[num]['origin']['content']
                            )
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    # 原创的动态（有图片）
                    elif dynamic_info[num]['type'] == 2:
                        # 处理图片序列
                        pic_segs = ''
                        for pic_url in dynamic_info[num]['pic_urls']:
                            pic_b64 = await pic_2_base64(pic_url)
                            pic_segs += f'{MessageSegment.image(pic_b64)}\n'
                        msg = '{}发布了新动态！\n\n“{}”\n{}\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['content'],
                            dynamic_info[num]['url'], pic_segs)
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    # 原创的动态（无图片）
                    elif dynamic_info[num]['type'] == 4:
                        msg = '{}发布了新动态！\n\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['content'], dynamic_info[num]['url'])
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    # 视频
                    elif dynamic_info[num]['type'] == 8:
                        msg = '{}发布了新的视频！\n\n《{}》\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['origin'],
                            dynamic_info[num]['content'], dynamic_info[num]['url'])
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    # 小视频
                    elif dynamic_info[num]['type'] == 16:
                        msg = '{}发布了新的小视频动态！\n\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['content'], dynamic_info[num]['url'])
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    # 番剧
                    elif dynamic_info[num]['type'] in [32, 512]:
                        msg = '{}发布了新的番剧！\n\n《{}》\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['origin'], dynamic_info[num]['url'])
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    # 文章
                    elif dynamic_info[num]['type'] == 64:
                        msg = '{}发布了新的文章！\n\n《{}》\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['origin'],
                            dynamic_info[num]['content'], dynamic_info[num]['url'])
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    # 音频
                    elif dynamic_info[num]['type'] == 256:
                        msg = '{}发布了新的音乐！\n\n《{}》\n“{}”\n{}'.format(
                            dynamic_info[num]['name'], dynamic_info[num]['origin'],
                            dynamic_info[num]['content'], dynamic_info[num]['url'])
                        for group_id in list(set(all_noitce_groups) & set(group_which_sub_dy)):
                            try:
                                await bot.send_group_msg(group_id=group_id, message=msg)
                                log.logger.info(f"{__name__}: 已成功向群组: {group_id} 发送新动态通知: {dynamic_info[num]['id']}")
                            except Exception as err:
                                log.logger.warning(f"{__name__}: 向群组: {group_id} "
                                                   f"发送新动态通知: {dynamic_info[num]['id']} 失败, error info: {err}.")
                                continue
                    elif dynamic_info[num]['type'] == -1:
                        log.logger.warning(f"未知的动态类型: {dynamic_info[num]['id']}")
                    # 更新动态内容到数据库
                    dy_id = dynamic_info[num]['id']
                    dy_type = dynamic_info[num]['type']
                    content = dynamic_info[num]['content']
                    # 向数据库中写入动态信息
                    is_success = await \
                        add_dy_info_to_db(user_id=dy_uid, dynamic_id=dy_id, dynamic_type=dy_type, content=content)
                    if is_success:
                        log.logger.info(f"{__name__}: 已成功向数据库写入动态信息: {dynamic_info[num]['id']}")
                    else:
                        log.logger.warning(f"{__name__}: 向数据库写入动态信息: {dynamic_info[num]['id']} 失败")
            except Exception as err:
                log.logger.error(f'{__name__}: 解析新动态: {dy_uid} 的时发生了错误, error info: {err}')

    log.logger.debug(f"{__name__}: 计划任务: dynamic_check, 开始检查动态")
    all_noitce_groups = query_all_notice_groups()
    # 检查订阅表中所有的up
    tasks = []
    for uid in query_dy_sub_list():
        tasks.append(check_user_dynamic(dy_uid=uid))
    try:
        await asyncio.gather(*tasks)
        log.logger.debug(f"{__name__}: 计划任务: dynamic_check, 已完成")
    except Exception as e:
        log.logger.error(f"{__name__}: error info: {e}.")
