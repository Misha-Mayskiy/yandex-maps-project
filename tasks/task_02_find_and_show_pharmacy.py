import sys
from io import BytesIO
import requests
from PIL import Image

from utils.config import (
    GEOCODER_API_KEY, STATIC_MAPS_API_KEY, GEOSEARCH_API_KEY,
    GEOCODER_API_SERVER, STATIC_MAPS_API_SERVER, GEOSEARCH_API_SERVER
)
from utils.geo_utils import haversine_distance


def geocode_address(address_to_find):
    """
    Gets coordinates (lon, lat) for a given address using Yandex Geocoder.
    Returns tuple (float, float) or None on error.
    """
    geocoder_params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": address_to_find,
        "format": "json"
    }
    print(f"1. Ищем адрес: '{address_to_find}'...")
    try:
        response = requests.get(GEOCODER_API_SERVER, params=geocoder_params)
        response.raise_for_status()
        json_response = response.json()

        feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]
        if not feature_member:
            print(f"   Ошибка: Адрес '{address_to_find}' не найден.")
            return None

        toponym = feature_member[0]["GeoObject"]
        coords_str = toponym["Point"]["pos"]
        longitude, latitude = map(float, coords_str.split())
        print(f"   Координаты найдены: ({longitude:.6f}, {latitude:.6f})")
        return (longitude, latitude)

    except requests.exceptions.RequestException as e:
        print(f"   Ошибка сети при запросе к Геокодеру: {e}")
        return None
    except Exception as e:
        print(f"   Непредвиденная ошибка при геокодировании: {e}")
        return None


def find_nearest_organization(coords_lonlat, text_query, org_type="biz"):
    """
    Finds the nearest organization matching the query near given coordinates.
    Returns a dictionary with organization details or None on error.
    """
    search_params = {
        "apikey": GEOSEARCH_API_KEY,
        "text": text_query,
        "lang": "ru_RU",
        "ll": f"{coords_lonlat[0]},{coords_lonlat[1]}",
        "type": org_type,
        "results": 1  # We only need the nearest one
    }
    print(f"2. Ищем ближайший объект '{text_query}'...")
    try:
        response = requests.get(GEOSEARCH_API_SERVER, params=search_params)
        response.raise_for_status()
        json_response = response.json()

        if not json_response.get("features"):
            print(f"   Ошибка: Организации типа '{text_query}' не найдены рядом.")
            return None

        organization = json_response["features"][0]
        org_meta = organization["properties"].get("CompanyMetaData", {})
        org_name = org_meta.get("name", "Название не найдено")
        org_address = org_meta.get("address", "Адрес не найден")
        org_hours_info = org_meta.get("Hours", {})
        # Try to get text representation, otherwise state it's unavailable
        org_hours = org_hours_info.get("text",
                                       "Нет данных о часах работы") if org_hours_info else "Нет данных о часах работы"

        point = organization["geometry"]["coordinates"]
        org_lon, org_lat = float(point[0]), float(point[1])

        print(f"   Найдена организация: {org_name}")
        return {
            "name": org_name,
            "address": org_address,
            "hours": org_hours,
            "coords": (org_lon, org_lat)
        }

    except requests.exceptions.RequestException as e:
        print(f"   Ошибка сети при запросе к Geosearch API: {e}")
        return None
    except Exception as e:
        print(f"   Непредвиденная ошибка при поиске организации: {e}")
        return None


def get_static_map_with_points(points_data):
    """
    Gets a map image from StaticMapsAPI centered to fit all points.
    Args:
        points_data (list): A list of tuples, where each tuple is
                           (longitude, latitude, style_marker)
                           e.g., [(37.6, 55.7, 'pm2blm'), (37.5, 55.8, 'pm2rdm')]
    Returns:
        PIL.Image object or None on error.
    """
    if not points_data:
        return None

    # Construct the 'pt' parameters string
    pt_params = []
    for lon, lat, style in points_data:
        pt_params.append(f"{lon:.6f},{lat:.6f},{style}")

    static_api_params = {
        "l": "map",
        "apikey": STATIC_MAPS_API_KEY,
        "pt": "~".join(pt_params)  # Use ~ as separator for multiple points
        # No ll or spn needed - API will auto-adjust
    }

    print("4. Запрос карты из Static API с метками...")
    try:
        response = requests.get(STATIC_MAPS_API_SERVER, params=static_api_params)
        # print(f"   URL запроса: {response.url}") # Uncomment for debugging
        response.raise_for_status()

        image_stream = BytesIO(response.content)
        opened_image = Image.open(image_stream)
        print("   Карта получена.")
        return opened_image

    except requests.exceptions.RequestException as e:
        print(f"   Ошибка сети при запросе к StaticMapsAPI: {e}")
        return None
    except Exception as e:
        print(f"   Непредвиденная ошибка при получении карты: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Ошибка: Не указан адрес для поиска.")
        print(f"Пример запуска: python {sys.argv[0]} Москва, ул. Тверская, 1")
        sys.exit(1)

    # Get address from command line
    address_to_find = " ".join(sys.argv[1:])

    # 1. Geocode the initial address
    start_coords = geocode_address(address_to_find)
    if start_coords is None:
        sys.exit(1)

    # 2. Find the nearest pharmacy
    pharmacy_info = find_nearest_organization(start_coords, "аптека")
    if pharmacy_info is None:
        sys.exit(1)

    # 3. Calculate distance
    print("3. Расчет расстояния...")
    distance_km = haversine_distance(start_coords, pharmacy_info["coords"])
    distance_m = distance_km * 1000
    print(f"   Расстояние: {distance_m:.1f} м (~{distance_km:.2f} км)")

    # 4. Prepare points for the map
    # Point 1: Start address (blue marker)
    # Point 2: Pharmacy (red marker)
    map_points = [
        (start_coords[0], start_coords[1], "pm2blm"),  # blue
        (pharmacy_info["coords"][0], pharmacy_info["coords"][1], "pm2rdm")  # red
    ]

    # 5. Get and show the map
    map_image = get_static_map_with_points(map_points)
    if map_image:
        print("5. Показ карты...")
        map_image.show()
    else:
        print("   Не удалось получить изображение карты.")

    # 6. Print the snippet
    print("\n" + "-" * 40)
    print("Информация о ближайшей аптеке:")
    print(f"  Название:  {pharmacy_info['name']}")
    print(f"  Адрес:     {pharmacy_info['address']}")
    print(f"  Часы работы: {pharmacy_info['hours']}")
    print(f"  Расстояние: {distance_m:.1f} м")
    print("-" * 40)

    print("Программа завершена.")
