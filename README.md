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
            ├─dd_almanac    //dd老黄历插件
            │      almanac_text.py
            │      get_almanac_for_dd.py
            │      __init__.py
            │
            ├─Group_manage    //群组自动管理插件
            │      __init__.py
            │
            ├─help    //帮助模组
            │      __init__.py
            │
            ├─maybe    //求签插件
            │      get_divination_of_thing.py
            │      __init__.py
            │
            ├─members_skill    //技能插件
            │      add_skill.py
            │      query_skill.py
            │      __init__.py
            │
            ├─member_mamage    //群成员管理插件
            │      member_mamage.py
            │      __init__.py
            │
            ├─pixiv    //pixiv插件
            │  │  config.py
            │  │  __init__.py
            │  │
            │  └─src
            │      │  dl_illust.py    //图片下载
            │      │  illust_info.py    //作品信息
            │      │  pic_2_base64.py
            │      │  weekly_daily_ranking.py    //周榜功能
            │      │  __init__.py
            │      │
            │      └─illust_pic    //图片存放文件夹
            │
            └─weather    //天气插件
                    get_weather.py
                    __init__.py
