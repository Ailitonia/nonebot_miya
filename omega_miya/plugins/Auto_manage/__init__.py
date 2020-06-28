from nonebot import on_request, RequestSession, on_notice, NoticeSession, get_bot
from aiocqhttp import Event
from omega_miya.plugins.Group_manage.group_permissions import *


# 加群申请
@on_request('group')
async def _(session: RequestSession):
    if not has_admin_permissions(group_id=session.event.group_id):
        return
    # 判断验证信息是否符合要求
    if session.event.comment == 'Miya好萌好可爱':
        # 验证信息正确，同意入群
        await session.approve()
        return
    # 验证信息错误，拒绝入群
    await session.reject('回答不对哦QAQ')


# 加好友申请
@on_request('friend')
async def _(session: RequestSession):
    # 判断验证信息是否符合要求
    if session.event.comment == 'Miya好萌好可爱':
        # 验证信息正确，同意加好友
        await session.approve()
        return
    # 验证信息错误，拒绝
    await session.reject('回答不对哦QAQ')


# 新增群成员
@on_notice('group_increase')
async def _(session: NoticeSession):
    if not has_noitce_permissions(group_id=session.event.group_id):
        return
    # 发送欢迎消息
    await session.send('欢迎新朋友～')

bot = get_bot()


@bot.on_message('group')
async def auto_ban(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    if not has_admin_permissions(group_id=group_id):
        return
    msg = str(event.message)
    if msg == '面对我，崽种！':
        user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        if user_info['role'] in ['owner', 'admin']:
            await bot.send_group_msg(group_id=group_id, message='狗管理别闹OvO')
        else:
            await bot.send_group_msg(group_id=group_id, message='满足你的要求OvO')
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=1 * 60)


'''
# 踢人的就算了
@bot.on_message('group')
async def auto_kick(event: Event):
    group_id = event.group_id
    user_id = event.user_id
    if event.group_id not in ALLOW_GROUP:
        return
    msg = str(event.message)
    if msg == '面对我，bot！':
        user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        if user_info['role'] in ['owner', 'admin']:
            await bot.send_group_msg(group_id=group_id, message='狗管理别闹OvO')
        else:
            await bot.send_group_msg(group_id=group_id, message='你这人好奇怪啊OvO,踢了')
            await bot.set_group_kick(group_id=group_id, user_id=user_id)
'''
