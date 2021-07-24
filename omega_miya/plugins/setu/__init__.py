import asyncio
from omega_miya.plugins.Group_manage.group_permissions import *
from aiocqhttp import MessageSegment
from nonebot import on_command, CommandSession, permission, log
from omega_miya.plugins.pixiv import API_KEY, SEARCH_API_URL
# from omega_miya.plugins.setu.config import setu_src_path
from omega_miya.plugins.setu.src.illust_info import get_illust_data, fetch, \
    add_illust_info_to_db, get_t_illust_data_from_db, get_illust_db_stat
# from omega_miya.plugins.setu.src.dl_illust import *
from omega_miya.plugins.setu.src.pic_2_base64 import blur_illust


__plugin_name__ = '来点涩图'
__plugin_usage__ = r'''【来点涩图】

用法: 
/来点涩图 [tag]'''


# 本插件依赖pixiv插件部分模块, 请保证pixiv插件与本插件同时使用


# on_command 装饰器将函数声明为一个命令处理器
# 这里 pid 为命令的名字
@on_command('setu', aliases='来点涩图', only_to_me=False, permission=permission.EVERYBODY)
async def setu(session: CommandSession):
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
    # 从会话状态（session.state）中获取pid, 如果当前不存在, 则询问用户
    is_r18 = session.get('is_r18', prompt='想看R18？')
    tag = session.get('tag', prompt='什么tag？')
    try:
        if is_r18 == 0:
            try:
                # 获取illust信息
                illust_links = await get_illust_data(is_r18=is_r18, tag=tag)
            except Exception as e:
                await session.send('获取资源列表失败QAQ, 请稍后再试~')
                log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                   f'获取setu资源失败: api error: {e}')
                return
            # 检查图片状态
            if not illust_links:
                await session.send('找不到涩图QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                f'获取setu资源失败: 无资源或get_illust_data错误')
                return
            else:
                await session.send('稍等, 正在下载图片~')
                # 下载图片
                tasks = []
                add_db_task_res = []
                for item in illust_links:
                    # 添加下载图片异步任务
                    tasks.append(fetch(url=SEARCH_API_URL, paras={'key': API_KEY, 'pid': item['pid']}))
                    # 获取图片信息并写入数据库
                    try:
                        add_db_task_res.append(await add_illust_info_to_db(pid=item['pid']))
                    except Exception as e:
                        log.logger.warning(f"{__name__}: 写入数据库时发生错误, DBSESSION ERROR: {e}, pid: {item['pid']}.")
                if False in add_db_task_res:
                    log.logger.warning(f'{__name__}: 写入数据库时有失败项, 错误信息见日志.')
                # 异步下载图片
                try:
                    illustinfo = await asyncio.gather(*tasks)
                except Exception as e:
                    await session.send('下载图片中出现了意外的错误QAQ, 请稍后再试~')
                    log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                       f'获取setu资源失败, pixiv api error: {e}')
                    return
                # 检查图片状态
                fault_count = 0
                for item in illustinfo:
                    if 'error' in item.keys():
                        fault_count += 1
                        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取setu资源失败, 图片不存在')
                    else:
                        img_seg = MessageSegment.image(item['pic_b64'])
                        # 发送图片
                        await session.send(img_seg)
                        await asyncio.sleep(1)
                if fault_count == len(illustinfo):
                    await session.send('似乎出现了网络问题, 所有的图片都下载失败了QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 已获取setu资源, 失败: {fault_count}')
        elif is_r18 == 1:
            # 获取illust信息
            illust_links = await get_illust_data(is_r18=is_r18, tag=tag)
            # 检查图片状态
            if not illust_links:
                await session.send('找不到涩图QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取setu资源失败')
                return
            else:
                await session.send('群里就发链接哦~')
                for item in illust_links:
                    try:
                        await add_illust_info_to_db(pid=item['pid'])
                    except Exception as e:
                        log.logger.warning(f'{__name__}: 写入数据库时发生错误: {e}.')
                    await session.send(item['url'])
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功获取setu资源')
        # 测试本地数据库
        elif is_r18 == -2:
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 使用了本地数据库--2')
            illust_res = get_t_illust_data_from_db(*tag)
            r18 = illust_res['r18']
            pid_list = []
            for item in illust_res['item']:
                pid_list.append(item)
            log.logger.info(f'{__name__}: 查询到本地数据: tag: {tag}, r18: {r18}, pid_list: {pid_list}')
            # 检查图片状态
            if not pid_list:
                await session.send('找不到涩图QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                f'获取setu资源失败: 无资源或get_illust_data错误')
                return
            else:
                await session.send('稍等, 正在下载图片~')
                # 下载图片
                tasks = []
                for item in pid_list:
                    tasks.append(fetch(url=SEARCH_API_URL, paras={'key': API_KEY, 'pid': item}))
                try:
                    illustinfo = await asyncio.gather(*tasks)
                except Exception as e:
                    await session.send('下载图片中出现了意外的错误QAQ, 请稍后再试~')
                    log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} '
                                       f'获取setu资源失败, pixiv api error: {e}')
                    return
                # 检查图片状态
                fault_count = 0
                for item in illustinfo:
                    if 'error' in item.keys():
                        fault_count += 1
                        log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取setu资源失败, 图片不存在')
                    else:
                        # r18内容需要对图片做模糊处理
                        if r18 in [1, 2]:
                            img_seg = MessageSegment.image(blur_illust(b64image=item['pic_b64']))
                        else:
                            img_seg = MessageSegment.image(item['pic_b64'])
                        # 发送图片
                        await session.send(img_seg)
                        await asyncio.sleep(1)
                if fault_count == len(illustinfo):
                    await session.send('似乎出现了网络问题, 所有的图片都下载失败了QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 已获取setu资源, 失败: {fault_count}')
        # 测试获取数据
        elif is_r18 == -9:
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 使用导入测试--9')
            # 获取illust信息
            illust_links = await get_illust_data(is_r18=2, num=10)
            # 检查图片状态
            if not illust_links:
                await session.send('找不到涩图QAQ')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 获取setu资源失败')
                return
            else:
                await session.send('开始获取图片信息~')
                success_count = 0
                for item in illust_links:
                    try:
                        is_success = await add_illust_info_to_db(pid=item['pid'])
                        if is_success:
                            success_count += 1
                    except Exception as e:
                        log.logger.warning(f'{__name__}: 写入数据库时发生错误: {e}.')
                await session.send(f'任务执行完成, 成功{success_count}个, 总计{len(illust_links)}个~')
                log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 导入任务执行完成, '
                                f'成功{success_count}个, 总计{len(illust_links)}个')
        # 获取统计信息
        elif is_r18 == -10:
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 执行统计信息--10')
            # 获取统计信息
            stat_data = get_illust_db_stat()
            await session.send(f"本地数据库统计:\n\nTotal: {stat_data['total']}\nR18: {stat_data['r18']}")
            log.logger.info(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 成功获取了本地数据库信息')

    except Exception as e:
        # 有问题的话大概率都是网络问题, 不是也要推锅给网络OvO
        await session.send('似乎出现了网络问题呢QAQ')
        log.logger.warning(f'{__name__}: 群组: {group_id}, 用户: {session.event.user_id} 试图使用命令setu时发生了错误: {e}')


# weather.args_parser 装饰器将函数声明为 pid 命令的参数解析器
# 命令解析器用于将用户输入的参数解析成命令真正需要的数据
@setu.args_parser
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
            splited_arg = stripped_arg.split()
            # 第一次运行参数不为空
            if len(splited_arg) == 1 and splited_arg[0] == 'r18':
                session.state['is_r18'] = 1
                session.state['tag'] = None
            # 用于测试获取数据
            elif len(splited_arg) == 1 and splited_arg[0] == 'import':
                session.state['is_r18'] = -9
                session.state['tag'] = None
            # 用于查询统计信息
            elif len(splited_arg) == 1 and splited_arg[0] == '统计信息':
                session.state['is_r18'] = -10
                session.state['tag'] = None
            elif len(splited_arg) == 1 and splited_arg[0] != 'r18':
                session.state['is_r18'] = 0
                session.state['tag'] = splited_arg[0]
            elif len(splited_arg) == 2 and splited_arg[0] == 'r18':
                session.state['is_r18'] = 1
                session.state['tag'] = splited_arg[1]
            # 本地数据库数据
            elif len(splited_arg) == 2 and splited_arg[0] != 'r18':
                session.state['is_r18'] = -2
                session.state['tag'] = list(splited_arg)
            elif len(splited_arg) > 2:
                session.state['is_r18'] = -2
                session.state['tag'] = list(splited_arg)
            else:
                session.state['is_r18'] = 0
                session.state['tag'] = None
        else:
            session.state['is_r18'] = 0
            session.state['tag'] = None
        return


@on_command('importsetu', aliases='导入涩图', only_to_me=True, permission=permission.SUPERUSER)
async def importsetu(session: CommandSession):
    import os
    import re

    # 文件操作
    try:

        import_pid_file = os.path.join(os.path.dirname(__file__), 'src', 'import_pid.txt')
        if not os.path.exists(import_pid_file):
            await session.send('错误: 导入列表不存在QAQ')
            log.logger.error(f'{__name__}: 导入列表不存在')
            return

        pid_list = []

        with open(import_pid_file) as f:
            lines = f.readlines()
            for line in lines:
                if not re.match(r'^[0-9]+$', line):
                    log.logger.warning(f'{__name__}: 导入列表中有非数字字符: {line}')
                    continue
                pid_list.append(int(line))
    except Exception as e:
        await session.send('导入涩图资源时读取导入文件发生错误QAQ')
        log.logger.error(f'{__name__}: 导入涩图资源时读取导入文件发生错误: {e}')
        return
    await session.send('已读取导入文件列表, 开始获取作品信息~')

    # 对列表去重
    dupl_pid = set()
    for pid in pid_list:
        dupl_pid.add(pid)
    pid_list = list(dupl_pid)

    # 数据库操作
    try:
        all_count = len(pid_list)
        success_count = 0
        # 全部一起并发api撑不住, 做适当切分
        # 每个切片数量
        seg_n = 10
        pid_seg_list = []
        for i in range(0, all_count, seg_n):
            pid_seg_list.append(pid_list[i:i+seg_n])
        # 每个切片打包一个任务
        seg_len = len(pid_seg_list)
        process_rate = 0
        for seg_list in pid_seg_list:
            tasks = []
            for pid in seg_list:
                tasks.append(add_illust_info_to_db(pid=pid))
            # 进行异步处理
            success_res = await asyncio.gather(*tasks)
            # 对结果进行计数
            for item in success_res:
                if item:
                    success_count += 1
            # 显示进度
            process_rate += 1
            if process_rate % 10 == 0:
                await session.send(f'导入操作中，已完成: {process_rate}/{seg_len}')
    except Exception as e:
        await session.send('导入涩图资源时写入数据库发生错误QAQ')
        log.logger.error(f'{__name__}: 导入涩图资源时写入数据库发生错误, DBSESSION ERROR: {e}')
        return
    await session.send(f'导入操作已完成, 成功: {success_count}, 总计: {all_count}')
    log.logger.error(f'{__name__}: 导入操作已完成, 成功: {success_count}, 总计: {all_count}')
