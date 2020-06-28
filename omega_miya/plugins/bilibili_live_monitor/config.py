LIVE_API_URL = 'https://api.live.bilibili.com/room/v1/Room/get_info'
LIVE_URL = 'https://live.bilibili.com/'

# 检查间隔，单位分钟
CHECK_INTERVAL = 1

# 这里是监控列表，格式是{房间号: [名称, 别名1, 别名2, ……]}
MONITOR_LIST = {
    3012597: ['喵田弥夜Miya', 'miya', 'Miya'],
    21641569: ['黑桃影', 'echo'],
    11768825: ['子心Koishi', '子心'],
    9423956: ['喵田咪芙mifu', 'Mifu', 'mifu']
}

# 为了方便查询，倒置别名与房间号
CHECK_LIST = {}
for room in MONITOR_LIST.items():
    __room = list(room)
    for alias in __room[1]:
        CHECK_LIST[alias] = __room[0]
