import json

import folium
import requests
from flask import Flask
from geopy.distance import distance
from environs import Env


SHOW_TOTAL_PLACES = 5


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


def save_map(user_location, marker_list):
    map = folium.Map(location=user_location)
    for marker in marker_list:
        folium.Marker(
            (marker["latitude"], marker["longitude"]),
            popup = (
                f"<b>{replace_spaces_with_nbsp(marker['title'])}</b><br>"
                f"Расстояние: {marker['distance']:.2} км."
            ),
            tooltip = marker["title"]
        ).add_to(map)
    map.save("index.html")


def run_webserver():
    def index():
        with open("index.html") as file:
            return file.read()

    app = Flask(__name__)
    app.add_url_rule("/", "index", index)
    app.run("0.0.0.0")



if __name__ == "__main__":
    env = Env()
    env.read_env() 

    api_key = env.str("api_key")

    coffee_shop_list = []

    user_input = input("Где вы находитесь? ").strip()
    user_lon, user_lat = fetch_coordinates(api_key, user_input)

    print("Ваши координаты:", (user_lat, user_lon))
    print()

    for coffee_shop in load_data("coffee.json"):
        coffee_shop_title = coffee_shop["Name"]
        coffee_shop_lat = coffee_shop["Latitude_WGS84"]
        coffee_shop_lon = coffee_shop["Longitude_WGS84"]
        coffee_shop_distance = distance(
            (user_lat, user_lon), (coffee_shop_lat, coffee_shop_lon)
        ).km

        coffee_shop_list.append(
            {
                'title': coffee_shop_title,
                'distance': coffee_shop_distance,
                'latitude': coffee_shop_lat,
                'longitude': coffee_shop_lon,
            }
        )

    nearest_coffee_shops = sorted(
        coffee_shop_list,
        key = lambda coffee_shop: coffee_shop["distance"]
    )[:SHOW_TOTAL_PLACES]

    save_map([user_lat, user_lon], nearest_coffee_shops)
    run_webserver()
