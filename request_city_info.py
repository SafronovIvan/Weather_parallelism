import os
from dotenv import load_dotenv
import aiohttp
import asyncio
from typing import List
from constant import weather_codes_ru, geo_url, weather_url

# Загружаем переменные из .env в окружение - Не нужно для текущего набора сайтов
#load_dotenv()
#API_KEY = os.getenv("WEATHER_API_KEY") 
#print("Ключ успешно загружен:",  API_KEY)


async def get_weather_by_cities(cities:List[str]) -> List[dict]:
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        geo_tasks = []
        # Задачи для получения координат городов по названию
        for city in cities:
            geo_tasks.append(session.get(geo_url, params={"name": city, "count": 1, "format": "json"}))
        geo_responses = await asyncio.gather(*geo_tasks)
        weather_task = []
        received_cities = []
        received_geo_responses = []
        # По полученным координатам создаём задачи для поиска погоды в выбранном городе
        for city, resp in zip(cities, geo_responses):
            if resp.status == 200: # Корректный запрос
                data = await resp.json()
                if data.get("results"):
                    received_geo_responses.append(resp)
                    received_cities.append(city)
                    result = data["results"][0]
                    lat = result["latitude"]
                    lon = result["longitude"]
                    weather_task.append(session.get(weather_url,
                                                    params={"latitude": lat, "longitude": lon,"daily": "weathercode",
                                                            "current_weather": "true", "hourly": "weathercode"}))
                    
        weather_responses = await asyncio.gather(*weather_task)

        final = [] # Преобразование полученной информации в словарь
        for resp_weather, resp_geo, city in zip(weather_responses, received_geo_responses, received_cities):
            if resp_weather.status == 200 and resp_geo.status == 200:
                data_weather = await resp_weather.json()
                data_geo = await resp_geo.json()
                
                city_dict = {}
                city_dict["name"] = [city, data_geo["results"][0]["name"]]
                city_dict["lat"] = data_geo["results"][0]["latitude"]
                city_dict["lon"] = data_geo["results"][0]["longitude"]
                city_dict["windspeed"] = data_weather["current_weather"]["windspeed"]
                city_dict["winddirection"] = data_weather["current_weather"]["winddirection"]
                city_dict["current_weather"] = data_weather["current_weather"]["temperature"]
                code = data_weather["current_weather"]["weathercode"]
                city_dict["weathercode"] = weather_codes_ru.get(code, "Неизвестный код погоды")
                hourly_weather = data_weather["hourly"]["time"]
                daily_weather = data_weather["daily"]["time"]
                city_dict["hourly_weather"] = {}
                city_dict["daily_weather"] = {}
                # Прогноз погоды
                for time, code in zip(hourly_weather, data_weather["hourly"]["weathercode"]):
                    city_dict["hourly_weather"][time] = weather_codes_ru.get(code, "Неизвестный код погоды")
                for date, code in zip(daily_weather, data_weather["daily"]["weathercode"]):
                    city_dict["daily_weather"][date] = weather_codes_ru.get(code, "Неизвестный код погоды")
                final.append(city_dict)
        return final
                
if __name__ == "__main__":
    for i in asyncio.run(get_weather_by_cities(["Saint Petersburg", "London"])):
        print(i, "\n")