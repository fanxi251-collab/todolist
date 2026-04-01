import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional
from schemas import WeatherResponse
from datetime import datetime
import time


AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


def get_weather_api_key() -> str:
    api_key = os.getenv("WEATHER_API")
    if not api_key:
        raise ValueError("WEATHER_API environment variable not set")
    return api_key


def get_city_code(city_name: str) -> Optional[str]:
    city_code_map = {
        "北京": "101010100",
        "上海": "101020100",
        "广州": "101280100",
        "深圳": "101280600",
        "杭州": "101210100",
        "南京": "101190100",
        "成都": "101270100",
        "武汉": "101200100",
        "西安": "101110100",
        "重庆": "101040100",
        "天津": "101030100",
        "苏州": "101190400",
        "郑州": "101180100",
        "长沙": "101250100",
        "沈阳": "101070101",
        "青岛": "101120101",
        "大连": "101070201",
        "厦门": "101230201",
        "宁波": "101210400",
        "福州": "101230101",
        "济南": "101120601",
        "昆明": "101290100",
        "兰州": "101160101",
        "石家庄": "101090100",
        "哈尔滨": "101050101",
        "长春": "101060101",
        "南昌": "101240101",
        "贵阳": "101260101",
        "太原": "101100100",
        "合肥": "101220100",
        "南宁": "101300101",
        "海口": "101310101",
        "乌鲁木齐": "101130101",
        "银川": "101170101",
        "西宁": "101150101",
        "拉萨": "101140101",
        "呼和浩特": "101080100",
    }
    return city_code_map.get(city_name)


def fetch_weather(city: str, extensions: str = "all") -> Dict:
    api_key = get_weather_api_key()
    
    params = {
        "key": api_key,
        "city": city,
        "extensions": extensions,
        "output": "json"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = session.get(AMAP_WEATHER_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
    
    return {}


def get_current_weather(city: str) -> WeatherResponse:
    data = fetch_weather(city, "base")
    
    if data.get("status") != "1":
        raise ValueError(f"API error: {data.get('info', 'Unknown error')}")
    
    lives = data.get("lives", [])
    if not lives:
        raise ValueError(f"No weather data for city: {city}")
    
    live = lives[0]
    return WeatherResponse(
        city=live.get("city", city),
        weather=live.get("weather", ""),
        temperature=live.get("temperature", ""),
        wind=live.get("winddirection", "") + "风",
        humidity=live.get("humidity", ""),
        date=live.get("reporttime", "")
    )


def get_forecast_weather(city: str, days: int = 3) -> List[WeatherResponse]:
    data = fetch_weather(city, "all")
    
    if data.get("status") != "1":
        raise ValueError(f"API error: {data.get('info', 'Unknown error')}")
    
    forecasts = data.get("forecasts", [])
    if not forecasts:
        raise ValueError(f"No forecast data for city: {city}")
    
    forecast = forecasts[0]
    weather_list = forecast.get("casts", [])
    
    results = []
    for i, cast in enumerate(weather_list[:days]):
        results.append(WeatherResponse(
            city=city,
            weather=cast.get("dayweather", ""),
            temperature=f"{cast.get('nighttemp', '')}~{cast.get('daytemp', '')}°C",
            wind=cast.get("daywind", "") + "风",
            humidity=cast.get("daytemp", ""),
            date=cast.get("date", "")
        ))
    
    return results
