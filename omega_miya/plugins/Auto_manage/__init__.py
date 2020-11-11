from nonebot import on_request, RequestSession, on_notice, NoticeSession, get_bot, log
from aiocqhttp import Event
from omega_miya.plugins.Group_manage.group_permissions import *
from omega_miya.plugins.Auto_manage.block_list import BLOCK_GROUP


# 加群申请
@on_request('group')
async def group_increase_request(session: RequestSession):
    if not has_admin_permissions(group_id=session.event.group_id):
        return
    log.logger.info(f'{__name__}: 有新的加群申请: {session.event}')
    # 判断验证信息是否符合要求
    if session.event.comment == 'Miya好萌好可爱' and session.event.sub_type == 'add':
        # 验证信息正确, 同意入群
        await session.approve()
        log.logger.info(f'{__name__}: 群组: {session.event.group_id}, 已同意用户: {session.event.user_id} 的加群申请')
        return
    # 验证信息错误, 拒绝入群
    await session.reject('验证消息不对哦QAQ')
    log.logger.info(f'{__name__}: 群组: {session.event.group_id}, 已拒绝用户: {session.event.user_id} 的加群申请')
    return


# 处理被邀请进群
@on_request('group')
async def group_invite_request(session: RequestSession):
    group_id = session.event.group_id
    group_id = int(group_id)
    if group_id in BLOCK_GROUP:
        return
    log.logger.info(f'{__name__}: 有新的群组请求: {session.event}')
    # 判断验证信息是否符合要求
    if session.event.sub_type == 'invite':
        # 直接同意入群
        await session.approve()
        log.logger.info(f'{__name__}: 已被用户: {session.event.user_id} 邀请加入群组: {group_id}.')
        return
    log.logger.info(f'{__name__}: 已处理群组请求.')
    return


# 加好友申请
@on_request('friend')
async def new_friend(session: RequestSession):
    log.logger.info(f'{__name__}: 有新的加好友申请: {session.event}')
    # 判断验证信息是否符合要求
    if session.event.comment == 'Miya好萌好可爱':
        # 验证信息正确, 同意加好友
        await session.approve()
        log.logger.info(f'{__name__}: 已同意用户: {session.event.user_id} 的加好友申请')
        return
    # 验证信息错误, 拒绝
    await session.reject('验证消息不对哦QAQ')
    log.logger.info(f'{__name__}: 已拒绝用户: {session.event.user_id} 的加好友申请')
    return


# 新增群成员
@on_notice('group_increase')
async def new_increase(session: NoticeSession):
    group_id = session.event.group_id
    group_id = int(group_id)
    if group_id in BLOCK_GROUP:
        return
    if not has_notice_permissions(group_id=group_id):
        return
    # 发送欢迎消息
    await session.send('欢迎新朋友～\n进群请先看群公告~\n想知道我的用法请发送/help')
    log.logger.info(f'{__name__}: 群组: {session.event.group_id}, 有新用户进群')
    return

bot = get_bot()


@bot.on_message('group')
async def auto_ban(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    if not has_admin_permissions(group_id=group_id):
        return
    msg = str(event.message)
    if msg == '面对我，崽种！':
        user_info = event['sender']
        if user_info['role'] in ['owner', 'admin']:
            await bot.send_group_msg(group_id=group_id, message='狗管理别闹OvO')
        else:
            await bot.send_group_msg(group_id=group_id, message='满足你的要求OvO')
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=1 * 60,)
            log.logger.info(f'{__name__}: 群组: {group_id}, 触发关键词封禁, 已将用户: {user_id} 禁言1分钟')
