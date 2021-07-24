import re
import random
import datetime
from nonebot import on_command, CommandSession, permission, log
from nonebot.command.argfilter import validators, controllers
from omega_miya.plugins.Group_manage.group_permissions import *

__plugin_name__ = '抽奖'
__plugin_usage__ = r'''【抽奖】

一个整合了各种抽奖机制的插件
更多功能待加入...

用法: 
/roll <x>d<y>  # 掷骰子

/抽奖 <人数>  # 从本群成员中抽取指定人数'''


@on_command('roll', only_to_me=False, permission=permission.GROUP)
async def roll(session: CommandSession):
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
    dice_num = session.get('dice_num', prompt='请输入骰子个数: ',
                           arg_filters=[controllers.handle_cancellation(session),
                                        validators.not_empty('输入不能为空'),
                                        validators.match_regex(r'^\d+$', '只能是数字哦, 请重新输入~',
                                                               fullmatch=True)])
    dice_side = session.get('dice_side', prompt='请输入骰子面数: ',
                            arg_filters=[controllers.handle_cancellation(session),
                                         validators.not_empty('输入不能为空'),
                                         validators.match_regex(r'^\d+$', '只能是数字哦, 请重新输入~',
                                                                fullmatch=True)])
    try:
        # 初始化随机种子
        random_seed = hash(str([session.event.user_id, session.event.group_id, datetime.datetime.now()]))
        random.seed(random_seed)
        # 加入一个趣味的机制
        if random.randint(1, 101) == 100:
            await session.send(f'【彩蛋】骰子之神似乎不看好你, 你掷出的骰子全部消失了')
            return
        dice_num = int(dice_num)
        dice_side = int(dice_side)
        if dice_num > 1000 or dice_side > 1000:
            await session.send(f'【错误】谁没事干扔那么多骰子啊(╯°□°）╯︵ ┻━┻')
            return
        if dice_num <= 0 or dice_side <= 0:
            await session.send(f'【错误】你掷出了不存在的骰子, 只有上帝知道结果是多少')
            return
        dice_result = 0
        for i in range(dice_num):
            this_dice_result = random.choice(range(dice_side)) + 1
            dice_result += this_dice_result
        await session.send(f'你掷出了{dice_num}个{dice_side}面骰子, 点数为【{dice_result}】')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                        f'Roll了一次{dice_num}d{dice_side}, 结果为{dice_result}')
        return
    except Exception as e:
        await session.send(f'【错误】不知道发生了什么, 你掷出的骰子全部裂开了')
        log.logger.error(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} Roll时发生了错误: {e}')
        return


@roll.args_parser
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
            if len(splited_arg) == 1 and re.match(r'^\d+d\d+$', splited_arg[0]):
                dice_info = splited_arg[0].split('d')
                session.state['dice_num'] = dice_info[0]
                session.state['dice_side'] = dice_info[1]
                return
            elif len(splited_arg) == 1 and re.match(r'^\d+D\d+$', splited_arg[0]):
                dice_info = splited_arg[0].split('D')
                session.state['dice_num'] = dice_info[0]
                session.state['dice_side'] = dice_info[1]
                return
            else:
                session.finish('输入的格式好像不对呢,命令格式为\n【/roll <x>d<y>】\n, 请确认后重新输入命令吧~')
    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


@on_command('lottery', aliases='抽奖', only_to_me=False, permission=permission.GROUP)
async def lottery(session: CommandSession):
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
    # 初始化随机种子
    random_seed = hash(str([session.event.user_id, session.event.group_id, datetime.datetime.now()]))
    random.seed(random_seed)

    people_num = session.get('people_num', prompt='请输入抽奖的人数: ',
                             arg_filters=[controllers.handle_cancellation(session),
                                          validators.not_empty('输入不能为空'),
                                          validators.match_regex(r'^\d+$', '只能是数字哦, 请重新输入~',
                                                                 fullmatch=True)])
    people_num = int(people_num)

    group_user_list = await session.bot.get_group_member_list(group_id=group_id)
    group_user_name_list = []

    for user_info in group_user_list:
        __user_qq = user_info['user_id']
        __user_group_info = await session.bot.get_group_member_info(group_id=group_id, user_id=__user_qq)
        __user_group_nickmane = __user_group_info['card']
        if not __user_group_nickmane:
            __user_group_nickmane = __user_group_info['nickname']
        group_user_name_list.append(__user_group_nickmane)

    if people_num > len(group_user_name_list):
        await session.send(f'抽奖人数大于群成员人数了QAQ, 请重新设置人数哦~')
        return

    lottery_result = random.sample(group_user_name_list, k=people_num)

    msg = ''
    for item in lottery_result:
        msg += f'\n【{item}】'
    await session.send(f'抽奖人数: 【{people_num}】\n以下是中奖名单:\n{msg}')
    log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 进行了一次抽奖')
    return


@lottery.args_parser
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
            if len(splited_arg) == 1 and re.match(r'^\d+$', splited_arg[0]):
                session.state['people_num'] = splited_arg[0]
                return
            else:
                session.finish('输入的格式好像不对呢,命令格式为\n【/抽奖 <人数>】\n, 请确认后重新输入命令吧~')
    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return
