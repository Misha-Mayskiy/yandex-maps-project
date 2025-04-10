import sys
from io import BytesIO
import requests
from PIL import Image

from utils.config import (
    GEOCODER_API_KEY, STATIC_MAPS_API_KEY, GEOSEARCH_API_KEY,
    GEOCODER_API_SERVER, STATIC_MAPS_API_SERVER, GEOSEARCH_API_SERVER
)


def geocode_address(address_to_find):
    """
    Gets coordinates (lon, lat) for a given address using Yandex Geocoder.
    Returns tuple (float, float) or None on error.
    (Slightly modified for better logging in context)
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


def find_organizations(coords_lonlat, text_query, num_results=10, org_type="biz"):
    """
    Finds organizations matching the query near given coordinates.
    Returns a list of organization feature dictionaries or empty list on error.
    """
    search_params = {
        "apikey": GEOSEARCH_API_KEY,
        "text": text_query,
        "lang": "ru_RU",
        "ll": f"{coords_lonlat[0]},{coords_lonlat[1]}",
        "type": org_type,
        "results": num_results
    }
    print(f"2. Ищем до {num_results} ближайших '{text_query}'...")
    try:
        response = requests.get(GEOSEARCH_API_SERVER, params=search_params)
        response.raise_for_status()
        json_response = response.json()

        organizations = json_response.get("features", [])
        if not organizations:
            print(f"   Ошибка: Организации типа '{text_query}' не найдены рядом.")
            return []

        print(f"   Найдено организаций: {len(organizations)}")
        return organizations  # Return the list of feature objects

    except requests.exceptions.RequestException as e:
        print(f"   Ошибка сети при запросе к Geosearch API: {e}")
        return []
    except Exception as e:
        print(f"   Непредвиденная ошибка при поиске организаций: {e}")
        return []


def get_marker_style(organization_feature):
    """
    Determines the marker style based on the organization's hours.
    Returns 'pm2gnm' (green), 'pm2blm' (blue), or 'pm2grm' (grey).
    """
    try:
        hours_info = organization_feature["properties"]["CompanyMetaData"]["Hours"]
        availabilities = hours_info.get("Availabilities", [])
        # Check if any availability indicates 24/7
        is_24_7 = any(
            avail.get("TwentyFourHours", False) and avail.get("Everyday", False)
            for avail in availabilities
        )
        if is_24_7:
            return "pm2gnm"  # Green for 24/7
        else:
            # Has hours info, but not 24/7
            return "pm2blm"  # Blue for regular hours
    except (KeyError, TypeError):
        # No 'Hours' info or it's not in the expected format
        return "pm2grm"  # Grey for unknown/no hours


def get_static_map_with_points(points_data):
    """
    Gets a map image from StaticMapsAPI centered to fit all points.
    Args:
        points_data (list): A list of tuples, where each tuple is
                           (longitude, latitude, style_marker)
    Returns:
        PIL.Image object or None on error.
    (Reused from previous task)
    """
    if not points_data:
        print("   Нет точек для отображения на карте.")
        return None

    pt_params = []
    for lon, lat, style in points_data:
        pt_params.append(f"{lon:.6f},{lat:.6f},{style}")

    static_api_params = {
        "l": "map",
        "apikey": STATIC_MAPS_API_KEY,
        "pt": "~".join(pt_params)
    }

    print("3. Запрос карты из Static API с метками...")
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
        print(
            f"Пример запуска: python -m {__package__}.{__file__.split('/')[-1].replace('.py', '')} Москва, ул. Тверская, 1")
        sys.exit(1)

    # Get address from command line
    address_to_find = " ".join(sys.argv[1:])

    # 1. Geocode the initial address
    start_coords = geocode_address(address_to_find)
    if start_coords is None:
        sys.exit(1)

    # 2. Find the nearest 10 pharmacies
    pharmacies = find_organizations(start_coords, "аптека", num_results=10)
    if not pharmacies:
        print("Не удалось найти аптеки для отображения.")
        sys.exit(1)

    # 3. Prepare points for the map
    map_points = []
    for org in pharmacies:
        try:
            org_lon, org_lat = map(float, org["geometry"]["coordinates"])
            marker_style = get_marker_style(org)
            map_points.append((org_lon, org_lat, marker_style))
        except (KeyError, IndexError, ValueError) as e:
            print(f"   Предупреждение: Не удалось обработать данные для одной из аптек: {e}")
            continue  # Skip this pharmacy if data is invalid

    # 4. Get and show the map
    if map_points:
        map_image = get_static_map_with_points(map_points)
        if map_image:
            print("4. Показ карты...")
            map_image.show()
        else:
            print("   Не удалось получить изображение карты.")
    else:
        print("   Нет корректных данных об аптеках для отображения на карте.")

    print("Программа завершена.")
