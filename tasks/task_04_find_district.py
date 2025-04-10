import sys
import requests

from utils.config import (
    GEOCODER_API_KEY, GEOCODER_API_SERVER
)


def get_coords_from_address(address_to_find):
    """
    Gets coordinates (lon, lat) for a given address using Yandex Geocoder.
    Returns tuple (float, float) or None on error.
    """
    geocoder_params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": address_to_find,
        "format": "json"
    }
    print(f"1. Ищем координаты адреса: '{address_to_find}'...")
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
        print(f"   Непредвиденная ошибка при геокодировании адреса: {e}")
        return None


def get_object_by_coords(coords_lonlat, kind):
    """
    Finds the name of the geographical object of a specific 'kind'
    at the given coordinates using reverse geocoding.

    Args:
        coords_lonlat (tuple): (longitude, latitude) tuple.
        kind (str): The kind of object to search for (e.g., 'district').

    Returns:
        str: The name of the found object or None on error.
    """
    reverse_geocoder_params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": f"{coords_lonlat[0]},{coords_lonlat[1]}",  # Reverse geocode format
        "format": "json",
        "kind": kind,
        "results": 1  # We only need the most relevant object of this kind
    }
    print(f"2. Ищем объект типа '{kind}' по координатам {coords_lonlat}...")
    try:
        response = requests.get(GEOCODER_API_SERVER, params=reverse_geocoder_params)
        response.raise_for_status()
        json_response = response.json()

        feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]
        if not feature_member:
            print(f"   Ошибка: Объект типа '{kind}' не найден по данным координатам.")
            return None

        # For kinds like 'district', the name is usually in the 'name' field
        # or sometimes more detailed in metaDataProperty.GeocoderMetaData.text
        geo_object = feature_member[0]["GeoObject"]
        object_name = geo_object.get("name")
        # Fallback or alternative:
        # object_name = geo_object.get("metaDataProperty", {}).get("GeocoderMetaData", {}).get("text")

        if object_name:
            print(f"   Найден объект: {object_name}")
            return object_name
        else:
            print(f"   Ошибка: Не удалось извлечь имя объекта типа '{kind}' из ответа API.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"   Ошибка сети при обратном геокодировании: {e}")
        return None
    except Exception as e:
        print(f"   Непредвиденная ошибка при обратном геокодировании: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Ошибка: Не указан адрес для поиска района.")
        print(
            f"Пример запуска: python -m {__package__}.{__file__.split('/')[-1].replace('.py', '')} Москва, ул. Тверская, 1")
        sys.exit(1)

    # Get address from command line
    address_input = " ".join(sys.argv[1:])

    # 1. Get coordinates for the input address
    coordinates = get_coords_from_address(address_input)
    if coordinates is None:
        sys.exit(1)

    # 2. Use coordinates to find the district
    district_name = get_object_by_coords(coordinates, "district")

    # 3. Print the result
    print("-" * 40)
    if district_name:
        print(f"Адрес '{address_input}' находится в районе:")
        print(f"-> {district_name}")
    else:
        print(f"Не удалось определить район для адреса '{address_input}'.")
    print("-" * 40)

    print("\nПрограмма завершена.")

# --- Что еще можно указать в параметре kind? ---
# Параметр 'kind' в Яндекс.Геокодере позволяет фильтровать тип возвращаемого
# топонима при геокодировании (прямом или обратном). Возможные значения включают:
# - house: дом
# - street: улица
# - metro: станция метро
# - district: район города
# - locality: населённый пункт (город, посёлок и т.п.)
# - area: район области (или эквивалент)
# - province: область, край, республика (или эквивалент)
# - country: страна
# - hydro: гидрографический объект (река, озеро)
# - railway: железнодорожная станция
# - route: шоссе, дорога
# - vegetation: лес, парк
# - airport: аэропорт
# - other: другое
# Полный и актуальный список лучше смотреть в официальной документации
# Яндекс.Геокодера, так как он может обновляться.
