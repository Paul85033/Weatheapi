import os
import datetime as dt
import requests
import redis
import json
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(redis_url)

URL = os.getenv("BASE_URL")
KEY = os.getenv("API_KEY")
CITY=input("Enter the city name: ")

def temp_converter(kelvin):
    celsius = kelvin - 273
    farhenheit = (celsius * 9/5) + 32
    return celsius, farhenheit

def fetch_weather_data(city):
    url = f"{URL}q={CITY}&appid={KEY}"
    response = requests.get(url).json()
    return response
    #url = BASE_URL + "appid=" + API_KEY + "&q=" + CITY

def get_cached_weather(city):
    cached_data = redis_client.get(city)
    if cached_data:
        return json.loads(cached_data)
    return None

def cache_weather_data(city, data, expire_time=7200):
    redis_client.setex(city, expire_time, json.dumps(data))

def is_rate_limited(user_id, max_requests=5, window_seconds=60):
    redis_key = f"rate_limit:{user_id}"
    request_count = redis_client.get(redis_key)
    
    if request_count:
        request_count = int(request_count)
        if request_count >= max_requests:
            return True  
        redis_client.incr(redis_key)  
    else:
        redis_client.setex(redis_key, window_seconds, 1)  
    
    return False 

USER_ID = CITY  

if is_rate_limited(USER_ID):
    print("Rate limit exceeded!")
else:
    weather_data = get_cached_weather(CITY)
    
    if not weather_data:
        weather_data = fetch_weather_data(CITY)
        cache_weather_data(CITY, weather_data)
    else:
        print("Getting data from cache")

temp_kelvin = weather_data['main']['temp']
temp_celsius, temp_fahrenheit = temp_converter(temp_kelvin)
feels_like_kelvin = weather_data['main']['feels_like']
feels_like_celsius, feels_like_fahrenheit = temp_converter(feels_like_kelvin)
wind_speed = weather_data['wind']['speed']
humidity = weather_data['main']['humidity']
description = weather_data['weather'][0]['description']
sunrise_time = dt.datetime.fromtimestamp(weather_data['sys']['sunrise'])
sunset_time = dt.datetime.fromtimestamp(weather_data['sys']['sunset'])

print(f"Temperature in {CITY}: {temp_celsius:.2f}°C, {temp_fahrenheit:.2f}°F")
print(f"Temperature in {CITY} feels like: {feels_like_celsius:.2f}°C, {feels_like_fahrenheit:.2f}°F")
print(f"Humidity in {CITY}: {humidity}%")
print(f"Wind speed in {CITY}: {wind_speed} m/s")
print(f"General Weather in {CITY}: {description}")
print(f"Sunrise in {CITY} at {sunrise_time} local time")
print(f"Sunset in {CITY} at {sunset_time} local time")
