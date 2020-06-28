DYNAMIC_API_URL = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history'
DYNAMIC_URL = 'https://t.bilibili.com/'

# 检查间隔，单位分钟
CHECK_INTERVAL = 2

# 这里是监控列表，格式是{用户UID: [名称, 别名1, 别名2, ……]}
MONITOR_LIST = {
    846180: ['喵田弥夜Miya', 'miya', 'Miya'],
    456368455: ['黑桃影', 'echo'],
    147529: ['子心Koishi', '子心']
}

# 为了方便查询，倒置别名与UID
CHECK_LIST = {}
for uid in MONITOR_LIST.items():
    __uid = list(uid)
    for alias in __uid[1]:
        CHECK_LIST[alias] = __uid[0]
