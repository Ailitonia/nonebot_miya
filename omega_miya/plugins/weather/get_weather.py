import aiohttp
from nonebot import log


async def fetch(url: str, paras: dict) -> dict:
    timeout_count = 0
    while timeout_count < 3:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                async with session.get(url=url, params=paras, headers=headers, timeout=timeout) as resp:
                    json = await resp.json()
            return json
        except Exception as e:
            log.logger.warning(f'Weather: fetch ERROR: {e}. Occurred in try {timeout_count + 1} using paras: {paras}')
        finally:
            timeout_count += 1
    else:
        log.logger.warning(f'Weather: fetch ERROR: Timeout {timeout_count}, using paras: {paras}')
        return {'HeWeather6': [{'status': 'error'}]}


async def get_weather_of_city(city: str) -> str:
    # 调用和风天气的api
    # 实时天气api
    url_weather = 'https://free-api.heweather.net/s6/weather/now'
    # 生活质量数据api
    # url_lifestyle = 'https://free-api.heweather.net/s6/weather/lifestyle'
    payload = {'location': city, 'key': ''}
    try:
        res_weather = await fetch(url=url_weather, paras=payload)
    except Exception as e:
        log.logger.warning(f'Weather: get_weather_of_city ERROR: {e}')
        return f'error'
    # res_lifestyle = requests.get(url_lifestyle, params=payload)
    # 判断返回状态
    if res_weather['HeWeather6'][0]['status'] == 'ok':
        return f'现在{city}天气' + res_weather['HeWeather6'][0]['now']['cond_txt'] + \
               '，气温' + res_weather['HeWeather6'][0]['now']['tmp'] + '摄氏度，' + \
               res_weather['HeWeather6'][0]['now']['wind_dir'] + '，风力' + \
               res_weather['HeWeather6'][0]['now']['wind_sc'] + '级。'
    else:
        return f'error'
