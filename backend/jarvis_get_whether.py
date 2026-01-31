import os
import logging
import aiohttp
from dotenv import load_dotenv
from livekit.agents import function_tool
from backend.Jarvis_google_search import google_search

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def detect_city_by_ip() -> str:
    try:
        logger.info("IP के ज़रिए शहर detect करने की कोशिश की जा रही है")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://ipapi.co/json/") as response:
                if response.status == 200:
                    ip_info = await response.json()
                    city = ip_info.get("city")
                    if city:
                        logger.info(f"IP से शहर Detect किया गया: {city}")
                        return city
                else:
                    logger.warning(f"Failed to detect city: {response.status}")
        
        logger.warning("City detect करने में विफल, default 'Delhi' इस्तेमाल किया जा रहा है।")
        return "Delhi"
    except Exception as e:
        logger.error(f"IP से city detect करने में error आया: {e}")
        return "Delhi"


async def get_coordinates(city_name: str, api_key: str) -> tuple[float, float, str] | None:
    """
    Get latitude, longitude and formatted name for a city using OpenWeather Geocoding API.
    Returns (lat, lon, formatted_name) or None if not found.
    """
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city_name,
        "limit": 1,
        "appid": api_key
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        location = data[0]
                        lat = location.get("lat")
                        lon = location.get("lon")
                        name = location.get("name")
                        state = location.get("state", "")
                        country = location.get("country", "")
                        formatted_name = f"{name}, {state}, {country}".replace(", ,", ",")
                        return lat, lon, formatted_name
                else:
                     logger.warning(f"Geocoding failed for {city_name}: {response.status}")
    except Exception as e:
        logger.error(f"Error in geocoding {city_name}: {e}")
    return None

@function_tool
async def get_weather(city: str = "") -> str:
    
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("OpenWeather API key missing है।")
        return "Environment variables में OpenWeather API key नहीं मिली।"

    if not city:
        city = await detect_city_by_ip()

    logger.info(f"City के लिए weather fetch किया जा रहा है (Geocoding): {city}")
    
    # 1. Try Geocoding first
    coords = await get_coordinates(city, api_key)
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "appid": api_key,
        "units": "metric"
    }

    if coords:
        lat, lon, formatted_name = coords
        logger.info(f"Geocoding success: {formatted_name} ({lat}, {lon})")
        params["lat"] = lat
        params["lon"] = lon
        city_display_name = formatted_name
    else:
        logger.warning(f"Geocoding failed for '{city}'. Falling back to direct city query.")
        params["q"] = city
        city_display_name = city

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"OpenWeather API error: {response.status} - {text}")
                    
                    if response.status == 404:
                         logger.info(f"City '{city}' not found in OpenWeather. Falling back to Google Search.")
                         return await google_search(f"current weather in {city}")

                    return f"Error: Failed to fetch weather for {city}. (Status: {response.status})"

                data = await response.json()
                # Use name from API if direct query, else geocoded name
                if not coords:
                    city_display_name = data.get("name", city)

                weather = data["weather"][0]["description"].title()
                temperature = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                temp_min = data["main"]["temp_min"]
                temp_max = data["main"]["temp_max"]
                humidity = data["main"]["humidity"]
                pressure = data["main"]["pressure"]
                wind_speed = data["wind"]["speed"]
                visibility = data.get("visibility", "N/A")

                result = (f"Weather in {city_display_name}:\n"
                          f"- Condition: {weather}\n"
                          f"- Temperature: {temperature}°C (Feels like: {feels_like}°C)\n"
                          f"- Min/Max Temp: {temp_min}°C / {temp_max}°C\n"
                          f"- Humidity: {humidity}%\n"
                          f"- Pressure: {pressure} hPa\n"
                          f"- Visibility: {visibility} meters\n"
                          f"- Wind Speed: {wind_speed} m/s")

                logger.info(f"Weather result: \n{result}")
                return result

    except Exception as e:
        logger.exception(f"Weather fetch करते समय exception आया: {e}")
        return "Weather fetch करते समय एक error आया"

