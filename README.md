# nonebot_miya

基于nonebot的qq机器人

# 项目结构

    nonebot
    │  bot.py  //启动
    │  config.py  //配置
    │
    └─omega_miya
        │
        ├─database    //数据库模组
        │      tables.py    //数据库表类
        │      __init__.py
        │
        ├─log    //日志文件夹
        │
        └─plugins
            │  __init__.py
            │
            ├─bilibili_dynamic_monitor    //B站动态监控插件
            │      config.py
            │      get_dynamic_info.py
            │      __init__.py
            │
            ├─bilibili_live_monitor    //B站直播间监控插件
            │      config.py
            │      get_live_info.py
            │      __init__.py
            │
            ├─Announce    //通知插件
            │      __init__.py
            │
            ├─help    //帮助模组
            │      __init__.py
            │
            ├─Auto_manage    //事务自动处理管理插件
            │      __init__.py
            │
            ├─repeater    //复读机
            │      __init__.py
            │
            ├─Group_manage    //群组及群成员管理插件
            │      group_manage.py
            │      group_permissions.py
            │      __init__.py
            │
            └─Roll    //Roll
                    __init__.py
