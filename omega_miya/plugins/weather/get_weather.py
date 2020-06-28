import requests


async def get_weather_of_city(city: str) -> str:
    # 调用和风天气的api
    # 实时天气api
    url_weather = 'https://free-api.heweather.net/s6/weather/now'
    # 生活质量数据api
    # url_lifestyle = 'https://free-api.heweather.net/s6/weather/lifestyle'
    payload = {'location': city, 'key': '81bf208844f048dc91ba946b353e5bd9'}
    res_weather = requests.get(url_weather, params=payload)
    # res_lifestyle = requests.get(url_lifestyle, params=payload)
    # 判断返回状态
    if res_weather.json()['HeWeather6'][0]['status'] == 'ok':
        return f'现在{city}天气' + res_weather.json()['HeWeather6'][0]['now']['cond_txt'] + \
               '，气温' + res_weather.json()['HeWeather6'][0]['now']['tmp'] + '摄氏度，' + \
               res_weather.json()['HeWeather6'][0]['now']['wind_dir'] + '，风力' + \
               res_weather.json()['HeWeather6'][0]['now']['wind_sc'] + '级。'
    else:
        return f'error'
