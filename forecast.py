import requests
from tabulate import tabulate
import click
from datetime import datetime


def fetch_geocode(city: str) -> tuple[float, float, str]:
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if not data.get("results"):
        raise ValueError(f"Город не найден: {city}")

    geo = data["results"][0]

    return geo["latitude"], geo["longitude"], geo["name"]

def fetch_forecast(latitude: float, longitude: float) -> dict:

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&timezone=auto"
    )

    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def parse_forecast_to_tableview(city: str, forecast: dict, rows: int = 3) -> None:

    dates = forecast["daily"]["time"]
    max_temps = forecast["daily"]["temperature_2m_max"]
    min_temps = forecast["daily"]["temperature_2m_min"]
    precips = forecast["daily"]["precipitation_sum"]

    output = []
    for i in range(rows):
        output.append([
            datetime.strptime(dates[i], "%Y-%m-%d").strftime("%d.%m.%Y"),
            f"{((max_temps[i] + min_temps[i]) / 2):.1f}",
            f"{precips[i]:.1f}"
        ])

    headers = ["Дата", "Средняя температура, °C", "Осадки, мм"]

    print(f"\nПрогноз погоды для {city}\n")
    print(tabulate(output, headers=headers, tablefmt="pretty"))


@click.command(help="Выводит прогноз погоды в указанном городе на указанное кол-во дней (максимум 7)")
@click.option("--city", required=True, type=str)
@click.option("--days", type=int)
def main(city: str, days: int):

    if days > 7 or days <= 0:
        days = 7

    try:
        lat, lon, name = fetch_geocode(city)
        forecast_obj = fetch_forecast(lat, lon)
    except ValueError as e:
        print(e)
        return None

    parse_forecast_to_tableview(name, forecast_obj, days)

if __name__ == "__main__":
    main()