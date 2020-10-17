import asyncio
import nonebot
import re
from omega_miya.plugins.Group_manage.group_permissions import *
from omega_miya.plugins.pixivsion_monitor.config import API_KEY, API_URL, TAG_BLOCK_LIST
from omega_miya.plugins.pixivsion_monitor.utils import fetch, \
    add_pixivsion_sub_to_db, add_pixivsion_article_to_db, illust_image_2_base64,\
    clean_group_pixivsion_sub_in_db, get_pixivsion_article_id_list, query_group_whick_sub_pixivsion
from nonebot import on_command, CommandSession, permission, MessageSegment, log
from nonebot.command.argfilter import validators, controllers

__plugin_name__ = 'Pixivision订阅'
__plugin_usage__ = r'''【Pixivision订阅】

推送最新的Pixivision特辑！

/Pixivision [订阅|取消订阅] *群管理员可用
'''


@on_command('pixivision_sub', aliases=('Pixivision', 'pixivision'), only_to_me=False,
            permission=permission.SUPERUSER | permission.GROUP_ADMIN)
async def pixivision_sub(session: CommandSession):
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
    mode = session.get('mode', prompt='Pixivision\n【订阅】or【取消订阅】？',
                       arg_filters=[controllers.handle_cancellation(session),
                                    validators.not_empty('输入不能为空'),
                                    validators.match_regex(r'^(订阅|取消订阅)$', '指令不对哦, 请重新输入~',
                                                           fullmatch=True)])
    if mode == '订阅':
        __is_success = await add_pixivsion_sub_to_db(group_id=group_id)
        if not __is_success:
            await session.send('发生了意料之外的错误QAQ')
            log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                               f'试图订阅pixivision时发生了错误, 向数据库写入群组订阅失败.')
            return
        await session.send(f'已订阅Pixivision！')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 订阅了pixivision.')
    elif mode == '取消订阅':
        __is_success = await clean_group_pixivsion_sub_in_db(group_id=group_id)
        if not __is_success:
            await session.send('发生了意料之外的错误QAQ')
            log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                               f'试图取消订阅pixivision时发生了错误, 向数据库写入群组订阅失败.')
            return
        await session.send(f'已取消Pixivision订阅！')
        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 取消了pixivision订阅.')


@pixivision_sub.args_parser
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
            if len(splited_arg) == 1 and re.match(r'^(订阅|取消订阅)$', splited_arg[0]):
                session.state['mode'] = splited_arg[0]
                return
            else:
                session.finish('输入的格式好像不对呢, 请确认后重新输入命令吧~')
    # 用户没有发送有效的参数（而是发送了空白字符）, 返回向导
    if not stripped_arg:
        return


bot = nonebot.get_bot()


@nonebot.scheduler.scheduled_job(
    'cron',
    # year=None,
    # month=None,
    # day=None,
    # week=None,
    # day_of_week=None,
    hour='*/1',
    # minute='*/1',
    # second=None,
    # start_date=None,
    # end_date=None,
    # timezone=None,
    coalesce=True,
    misfire_grace_time=300
)
async def pixivsion_check():
    async def check_pixivsion_article():
        __res = await fetch(url=API_URL, paras={'key': API_KEY, 'mode': 'illustration'})
        return __res

    async def get_pixivsion_article_info(aid: int):
        __res = await fetch(url=API_URL, paras={'key': API_KEY, 'mode': 'article', 'aid': aid})
        return __res

    async def new_pixivsion_article(aid: int, tags: list):
        log.logger.info(f'{__name__}: get new pixivision article: {aid}')
        article_info = await get_pixivsion_article_info(aid=aid)
        if not article_info['error']:
            try:
                title = str(article_info['body']['article']['article_title'])
                description = str(article_info['body']['article']['article_description'])
                url = f'https://www.pixivision.net/zh/a/{aid}'
                illusts_list = []
                for illust in article_info['body']['article']['illusts_list']:
                    illusts_list.append(int(illust['illusts_id']))
                add_pixivsion_article_to_db(aid=aid, title=title, description=description,
                                            tags=str(tags), illust_id=str(illusts_list), url=url)
                __res = {
                    'title': title,
                    'description': description,
                    'url': url,
                    'image:': article_info['body']['article']['article_eyecatch_image'],
                    'illusts_list': illusts_list
                }
                return __res
            except Exception as err:
                log.logger.warning(f'{__name__}: new_pixivision_article ERROR: {err}')
                return None
        else:
            log.logger.warning(f'{__name__}: new_pixivision_article ERROR: {aid}, '
                               f'API server ERROR: {article_info}')
            return None

    # 初始化tag黑名单
    block_tag_id = []
    block_tag_name = []
    for block_tag in TAG_BLOCK_LIST:
        block_tag_id.append(block_tag['id'])
        block_tag_name.append(block_tag['name'])

    # 提取数据库中已有article的id列表
    article_id_list = get_pixivsion_article_id_list()

    # 获取最新一页pixivision的article
    new_article_id_tag = []
    pixivsion_article = await check_pixivsion_article()
    if not pixivsion_article['error']:
        try:
            for article in pixivsion_article['body']['illustration']:
                article_tags_id = []
                article_tags_name = []
                for __tag in article['tags']:
                    article_tags_id.append(int(__tag['tag_id']))
                    article_tags_name.append(str(__tag['tag_name']))
                # 跳过黑名单tag的article
                if list(set(article_tags_id) & set(block_tag_id)) or list(set(article_tags_name) & set(block_tag_name)):
                    continue
                # 检查新的article
                if int(article['id']) not in article_id_list:
                    log.logger.info(f"{__name__}: 检查到新的Pixivision article: {article['id']}")
                    new_article_id_tag.append({'aid': int(article['id']), 'tags': article_tags_name})
        except Exception as e:
            log.logger.error(f'{__name__}: an error occured in checking pixivision: {e}')
            return
    else:
        log.logger.warning(f'{__name__}: checking pixivision timeout or other error')
        return

    # 获取订阅群组列表, 设置需要通知的群组
    sub_group = query_group_whick_sub_pixivsion()
    all_noitce_groups = query_all_notice_groups()
    notice_group = list(set(all_noitce_groups) & set(sub_group))

    if not new_article_id_tag:
        log.logger.info(f"{__name__}: Pixivision检查完成, 没有新的article")
        return
    # 处理新的aritcle
    new_article_list = []
    for item in new_article_id_tag:
        if not item:
            continue
        new_article_list.append(await new_pixivsion_article(aid=item['aid'], tags=item['tags']))
    if not notice_group:
        log.logger.info(f"{__name__}: Pixivision检查完成, 有新的article, 没有群组订阅Pixivision")
        return
    for article in new_article_list:
        try:
            notice_msg = '新的Pixivision特辑！'
            intro_msg = f"《{article['title']}》\n\n{article['description']}\n{article['url']}"
            for group in notice_group:
                try:
                    await bot.send_group_msg(group_id=group, message=notice_msg)
                    await bot.send_group_msg(group_id=group, message=intro_msg)
                except Exception as e:
                    log.logger.warning(f"{__name__}: article简介信息发送失败: {e}, Group: {group}")
                    continue
            tasks = []
            for pid in article['illusts_list']:
                tasks.append(illust_image_2_base64(pid=pid))
            images_b64 = await asyncio.gather(*tasks)
            image_error = 0
            for b64 in images_b64:
                if not b64:
                    image_error += 1
                    continue
                else:
                    img_seg = MessageSegment.image(b64)
                # 发送图片
                for group in notice_group:
                    try:
                        await bot.send_group_msg(group_id=group, message=img_seg)
                    except Exception as e:
                        log.logger.warning(f"{__name__}: 图片内容发送失败: {e}, Group: {group}")
                        continue
                await asyncio.sleep(1)
        except Exception as e:
            log.logger.error(f"{__name__}: article信息解析失败: {e}, article: {str(article)}")
            continue
        log.logger.info(f"{__name__}: article图片已发送, 失败: {image_error}")
    log.logger.info(f"{__name__}: Pixivision检查完成, 有新的article, 已发送消息")
