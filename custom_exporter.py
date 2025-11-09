from prometheus_client import start_http_server, Gauge, Info, REGISTRY
import requests
import time
import traceback
import pandas as pd
import requests_cache
from retry_requests import retry
import openmeteo_requests
import numpy as np
from openmeteo_requests import Client


exporter_info = Info('exporter_info', 'Custom Exporter Info')


weather_temp = Gauge('weather_temperature_celsius', 'Температура в Астане', ['city', 'country'])
weather_wind = Gauge('weather_windspeed_kmh', 'Скорость ветра в Астане', ['city', 'country'])
weather_api_status = Gauge('weather_api_status', 'Weather API status (1=up, 0=down)')

crypto_btc_usd = Gauge("crypto_btc_usd", "Цена Bitcoin в USD")
crypto_eth_usd = Gauge("crypto_eth_usd", "Цена Ethereum в USD")
# github_commits = Gauge('github_repo_commits', 'Количество коммитов в публичном repo')

mars_temp_avg = Gauge("mars_temperature_avg", "Средняя температура на Марсе (°C)")
mars_wind_avg = Gauge("mars_wind_speed_avg", "Средняя скорость ветра на Марсе (m/s)")
mars_pressure_avg = Gauge("mars_pressure_avg", "Среднее давление на Марсе (Pa)")

air_pm10 = Gauge("air_pm10", "PM10 concentration", ["city"])
air_pm2_5 = Gauge("air_pm2_5", "PM2.5 concentration", ["city"])

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def fetch_current_weather():
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                'latitude': 51.1694,
                'longitude': 71.4491,
                'current_weather': 'true',
                'timezone': 'Asia/Almaty'
            },
            timeout=10
        )
        data = r.json()
        current = data.get('current_weather', {})

        weather_temp.labels(city='Astana', country='Kazakhstan').set(current.get('temperature', 0))
        weather_wind.labels(city='Astana', country='Kazakhstan').set(current.get('windspeed', 0))
        weather_api_status.set(1)

    except Exception as e:
        print(f"[Current Weather] Ошибка: {e}")
        traceback.print_exc()
        weather_temp.labels(city='Astana', country='Kazakhstan').set(0)
        weather_wind.labels(city='Astana', country='Kazakhstan').set(0)
        weather_api_status.set(0)



import numpy as np
import pandas as pd

def fetch_air_quality():
    try:
        params = {
            "latitude": 51.1694,
            "longitude": 71.4491,
            "hourly": ["pm10", "pm2_5"],
            "timezone": "auto",
            "forecast_days": 1
        }

        responses = openmeteo.weather_api(
            "https://air-quality-api.open-meteo.com/v1/air-quality", 
            params=params
        )
        response = responses[0]
        hourly = response.Hourly()

        pm10_values = np.array(hourly.Variables(0).ValuesAsNumpy())
        pm2_5_values = np.array(hourly.Variables(1).ValuesAsNumpy())
        time_values = hourly.Time()
        if not isinstance(time_values, (list, np.ndarray, pd.Series)):
            time_values = [time_values]
        times = pd.to_datetime(time_values, unit="s", utc=True)
        now = pd.Timestamp.utcnow()

        # Находим индекс ближайшего к текущему часу
        deltas = np.abs((times - now).total_seconds())
        idx = deltas.argmin()

        # Ставим метрики
        air_pm10.labels(city='Astana').set(round(float(pm10_values[idx]), 3))
        air_pm2_5.labels(city='Astana').set(round(float(pm2_5_values[idx]), 3))

        print(f"[Air Quality] {times[idx].strftime('%Y-%m-%d %H:%M:%S')} UTC - PM10: {pm10_values[idx]}, PM2.5: {pm2_5_values[idx]}")

    except Exception as e:
        print(f"[Air Quality] Ошибка: {e}")
        air_pm10.labels(city='Astana').set(0)
        air_pm2_5.labels(city='Astana').set(0)



# EXCHANGE_API_KEY = "41fc42a9bb75aa8ef905da4bd9515cbc"

# def fetch_exchange_rates():
#     try:
#         # GET запрос к live endpoint
#         url = f"https://api.exchangerate.host/live?access_key={EXCHANGE_API_KEY}&symbols=KZT,EUR&base=USD"
#         response = requests.get(url, timeout=10)
#         data = response.json()

#         # проверяем успех
#         if not data.get("success", False):
#             print(f"[Exchange] Ошибка API: {data}")
#             usd_kzt.set(0)
#             eur_kzt.set(0)
#             return

#         # извлекаем quotes
#         quotes = data.get("quotes", {})

#         usd_kzt.set(quotes.get("USDKZT", 0))
#         eur_kzt.set(quotes.get("USDEUR", 0))

#         print(f"USD/KZT: {usd_kzt._value.get()}, USD/EUR: {eur_kzt._value.get()}")

#     except Exception as e:
#         print(f"[Exchange] Ошибка: {e}")
#         traceback.print_exc()
#         usd_kzt.set(0)
#         eur_kzt.set(0)




# def fetch_github_commits():
#     try:
#         repo = "askhat00/ShopSphere-Analytics" 
#         data = requests.get(f"https://api.github.com/repos/{repo}/commits", timeout=20).json()
#         github_commits.set(len(data) if isinstance(data, list) else 0)
#     except Exception as e:
#         print(f"[GitHub] Ошибка: {e}")
#         traceback.print_exc()
#         github_commits.set(0)


def fetch_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        btc_price = data["bitcoin"]["usd"]
        eth_price = data["ethereum"]["usd"]

        crypto_btc_usd.set(btc_price)
        crypto_eth_usd.set(eth_price)

        print(f"[Crypto] BTC: {btc_price} USD, ETH: {eth_price} USD")

    except Exception as e:
        print(f"[Crypto] Ошибка: {e}")
        traceback.print_exc()
        crypto_btc_usd.set(0)
        crypto_eth_usd.set(0)


def fetch_mars_weather():
    try:
        url = "https://api.nasa.gov/insight_weather/?api_key=qWL6rKRMCGYFcbWAQTBtKlanaqZYeQ9DhHPYhI4u&feedtype=json&ver=1.0"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        sol_keys = data.get("sol_keys", [])
        if not sol_keys:
            print("[Mars Weather] Нет доступных Sol")
            return

        last_sol = sol_keys[-1] 
        sol_data = data[last_sol]

        if "AT" not in sol_data or "HWS" not in sol_data or "PRE" not in sol_data:
            print(f"[Mars Weather] Sol {last_sol} не содержит всех нужных данных")
            return

        mars_temp_avg.set(sol_data["AT"]["av"])
        mars_wind_avg.set(sol_data["HWS"]["av"])
        mars_pressure_avg.set(sol_data["PRE"]["av"])

        print(f"[Mars Weather] Sol {last_sol}: Temp {sol_data['AT']['av']}°C, "
              f"Wind {sol_data['HWS']['av']} m/s, Pressure {sol_data['PRE']['av']} Pa")

    except Exception as e:
        print(f"[Mars Weather] Ошибка: {e}")
        traceback.print_exc()



if __name__ == '__main__':
    exporter_info.info({'version':'1.0','author':'Student','sources':'weather,crypto,github,air'})

    start_http_server(8000)
    print("Custom Exporter запущен на порту 8000")

    while True:
        try:
            fetch_current_weather()
            # fetch_github_commits()
            fetch_air_quality()
            fetch_crypto_prices()
            fetch_mars_weather()

        except KeyboardInterrupt:
            print("Завершение работы пользователем...")
            break
        except Exception as e:
            print(f"[Main Loop] Ошибка: {e}")
            traceback.print_exc()
        time.sleep(20) 
