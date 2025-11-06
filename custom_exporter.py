from prometheus_client import start_http_server, Gauge, Info
import requests
import time

exporter_info = Info('exporter_info', 'Custom Exporter Info')

# Метрики погоды (Астана)
weather_temperature = Gauge(
    'weather_temperature_celsius',
    'Current temperature in Astana',
    ['city', 'country']
)

weather_windspeed = Gauge(
    'weather_windspeed_kmh',
    'Current wind speed in Astana',
    ['city', 'country']
)

weather_api_status = Gauge(
    'weather_api_status',
    'Weather API status (1=up, 0=down)'
)


def fetch_weather_data():
    """
    Получить данные о погоде Астаны через Open-Meteo API (без регистрации)
    """
    
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': 51.1694,
            'longitude': 71.4491,
            'current_weather': 'true',
            'timezone': 'Asia/Almaty'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data['current_weather']
        
        weather_temperature.labels(
            city='Astana',
            country='Kazakhstan'
        ).set(current['temperature'])
        
        weather_windspeed.labels(
            city='Astana',
            country='Kazakhstan'
        ).set(current['windspeed'])
             
        weather_api_status.set(1)        
        return True
        
    except requests.exceptions.RequestException:
        weather_api_status.set(0)
        return False


if __name__ == '__main__':
    # Установить информацию об exporter
    exporter_info.info({
        'version': '1.0',
        'author': 'Student',
        'sources': 'weather,crypto'
    })
    
    # Запустить HTTP сервер на порту 8000
    start_http_server(8000)
    
    # Бесконечный цикл сбора метрик
    while True:
        try:
            fetch_weather_data()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Ошибка при сборе метрик: {e}")  # <--- здесь нужен код!
        
        # Обновлять каждые 30 секунд
        time.sleep(30)