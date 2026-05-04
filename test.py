import asyncio
import aiohttp
from typing import List

async def get_weather(cities: List[str]) -> None:
    # Сначала получаем координаты через геокодинг API
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    weather_url = "https://api.open-meteo.com/v1/forecast"
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 1. Получаем координаты для всех городов
        geo_tasks = [
            session.get(geo_url, params={"name": city, "count": 1, "format": "json"})
            for city in cities
        ]
        geo_responses = await asyncio.gather(*geo_tasks)
        
        # 2. Для каждого города получаем погоду
        weather_tasks = []
        city_names = []
        
        for city, resp in zip(cities, geo_responses):
            if resp.status == 200:
                data = await resp.json()
                if data.get("results"):
                    result = data["results"][0]
                    lat = result["latitude"]
                    lon = result["longitude"]
                    name = result["name"]
                    
                    # Запрос погоды
                    weather_tasks.append(
                        session.get(
                            weather_url,
                            params={"latitude": lat, "longitude": lon, "current_weather": "true"}
                        )
                    )
                    city_names.append(name)
                else:
                    print(f"❌ {city}: не найден")
                    weather_tasks.append(None)
                    city_names.append(None)
            else:
                print(f"❌ {city}: ошибка геокодинга {resp.status}")
                weather_tasks.append(None)
                city_names.append(None)
        
        # 3. Выполняем все запросы погоды
        weather_responses = await asyncio.gather(*[t for t in weather_tasks if t is not None])
        
        # 4. Выводим результаты
        idx = 0
        for name in city_names:
            if name is not None:
                resp = weather_responses[idx]
                if resp.status == 200:
                    data = await resp.json()
                    temp = data["current_weather"]["temperature"]
                    print(data)
                    print(f"✅ {name}: {temp}°C")
                else:
                    print(f"❌ {name}: ошибка погоды {resp.status}")
                idx += 1

if __name__ == "__main__":
    asyncio.run(get_weather(["Moscow", "Paris", "London"]))