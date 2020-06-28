import os
import logging
import nonebot
from datetime import datetime
from nonebot.log import logger
import config

if __name__ == '__main__':
    # 从config中加载配置
    nonebot.init(config_object=config)

    # 从插件文件夹中加载插件
    nonebot.load_plugins(
        os.path.join(os.path.dirname(__file__), 'omega_miya', 'plugins'),
        'omega_miya.plugins'
    )

    # 加载数据库模块
    nonebot.load_plugins(
        os.path.join(os.path.dirname(__file__), 'omega_miya', 'database'),
        'omega_miya.database'
    )

    # 设置文件输出的日志
    log_file_name = datetime.today().strftime('%Y-%m-%d %H-%M-%S') + '.log'
    # 检查日志文件夹
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'omega_miya', 'log')):
        os.makedirs(os.path.join(os.path.dirname(__file__), 'omega_miya', 'log'))
        logger.info('未发现日志目录，已创建')
    # 创建日志文件
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'omega_miya', 'log', log_file_name)):
        # 注意windowds下是没有node的，只能用open方法创建文件
        try:
            os.mknod(os.path.join(os.path.dirname(__file__), 'omega_miya', 'log', log_file_name))
            logger.info(log_file_name + ': 日志文件已创建')
        except AttributeError:
            log_path = os.path.dirname(__file__) + '/omega_miya/log/' + log_file_name
            with open(log_path, 'w+') as f:
                logger.info(log_file_name + ': 日志文件已创建')
    f_handler = logging.FileHandler(
        os.path.join(os.path.dirname(__file__), 'omega_miya', 'log', log_file_name), encoding="utf-8")
    f_handler.setFormatter(
        logging.Formatter('[%(asctime)s %(name)s] %(levelname)s: %(message)s'))
    # 增加日志文件输出
    logger.addHandler(f_handler)
    # 设置输出级别
    logger.setLevel(logging.INFO)

    # 运行bot
    nonebot.run()
