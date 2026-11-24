import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_live_weather(lat, lon):
    """
    Fetch live weather data from OpenWeather API.
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")  # ✅ Correct usage

    if not api_key:
        print("❌ Missing API key in .env file. Please add OPENWEATHER_API_KEY=<your_key>")
        return None

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"⚠️ Error: {response.status_code} - {response.text}")
            return None

        data = response.json()

        weather = {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"] * 3.6  # m/s → km/h
        }

        return weather

    except Exception as e:
        print(f"⚠️ Weather API error: {e}")
        return None
