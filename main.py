import json

import folium
import requests
from flask import Flask
from geopy.distance import distance
from environs import Env


SHOW_TOTAL_PLACES = 5
HTML_MAP_PATH = "coffee_map.html"


def load_data(filepath):
    try:
        with open(filepath, 'r', encoding='CP1251') as json_file:
            return json.load(json_file)
    except json.decoder.JSONDecodeError:
        return


def fetch_coordinates(apikey, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def replace_spaces_with_nbsp(string):
    return string.replace(" ", "&nbsp;")


def generate_human_readable_distance(distance):
    distance_message = "Расстояние: {}"
    distance_with_units = f"{distance:.2f} км"

    if distance < 1:
        distance_with_units = f"{int(distance*1000)} м"

    return distance_message.format(distance_with_units)


def generate_html_coffee_map(user_location, coffee_shops):
    coffee_map = folium.Map(location=user_location)

    folium.Marker(
        user_location, tooltip="Вы здесь", icon=folium.Icon(color="red")
    ).add_to(coffee_map)

    for coffee_shop in coffee_shops:
        distance = generate_human_readable_distance(coffee_shop['distance'])
        folium.Marker(
            (coffee_shop["latitude"], coffee_shop["longitude"]),
            popup = (
                f"<b>{replace_spaces_with_nbsp(coffee_shop['title'])}</b><br>"
                f"{replace_spaces_with_nbsp(distance)}."
            ),
            tooltip = coffee_shop["title"]
        ).add_to(coffee_map)

    return coffee_map


def map_page_handler():
        with open(HTML_MAP_PATH) as file:
            return file.read()


def run_webserver(host="0.0.0.0", port=5000):
    app = Flask(__name__)
    app.add_url_rule("/", "map_page", map_page_handler)
    app.run(host=host, port=port)


def collect_coffee_shops(user_lat, user_lon):
    coffee_shops = []
    for coffee_shop in load_data("coffee.json"):
        coffee_shop_title = coffee_shop["Name"]
        coffee_shop_lat = coffee_shop["Latitude_WGS84"]
        coffee_shop_lon = coffee_shop["Longitude_WGS84"]
        coffee_shop_distance = distance(
            (user_lat, user_lon), (coffee_shop_lat, coffee_shop_lon)
        ).km
        coffee_shops.append(
            {
                'title': coffee_shop_title,
                'distance': coffee_shop_distance,
                'latitude': coffee_shop_lat,
                'longitude': coffee_shop_lon,
            }
        )
    return coffee_shops


if __name__ == "__main__":
    env = Env()
    env.read_env() 

    api_key = env.str("COFFEE_API_KEY")

    user_location = input("Где вы находитесь? ").strip()
    user_lon, user_lat = fetch_coordinates(api_key, user_location)

    coffee_shops = collect_coffee_shops(user_lat, user_lon)
    nearest_coffee_shops = sorted(
        coffee_shops,
        key = lambda coffee_shop: coffee_shop["distance"]
    )[:SHOW_TOTAL_PLACES]

    coffee_map = generate_html_coffee_map(
        [user_lat, user_lon], nearest_coffee_shops
    )
    coffee_map.save(HTML_MAP_PATH)
    run_webserver()
