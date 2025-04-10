import sys
from io import BytesIO
import requests
from PIL import Image

from utils.map_utils import get_map_params
from utils.config import (
    GEOCODER_API_KEY, STATIC_MAPS_API_KEY,
    GEOCODER_API_SERVER, STATIC_MAPS_API_SERVER
)


def geocode_address(address_to_find):
    geocoder_params = {
        "apikey": GEOCODER_API_KEY,  # Используем импортированный ключ
        "geocode": address_to_find,
        "format": "json"
    }
    print(f"Ищем адрес: '{address_to_find}'...")
    try:
        # Используем импортированный URL
        response = requests.get(GEOCODER_API_SERVER, params=geocoder_params)
        response.raise_for_status()
        json_response = response.json()

        feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]
        if not feature_member:
            print(f"Ошибка: Адрес '{address_to_find}' не найден.")
            return None

        toponym = feature_member[0]["GeoObject"]
        print("Адрес найден.")
        return toponym

    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при запросе к Геокодеру: {e}")
        return None
    except (KeyError, IndexError):
        print("Ошибка: Некорректный формат ответа от Геокодера.")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка при геокодировании: {e}")
        return None


def get_static_map_image(map_params_dict, point_coords):
    point_str = f"{point_coords[0]:.6f},{point_coords[1]:.6f},pm2rdl"
    static_api_params = {
        "l": "map",
        "apikey": STATIC_MAPS_API_KEY,  # Используем импортированный ключ
        "pt": point_str
    }
    static_api_params.update(map_params_dict)

    print("Запрос карты из Static API...")
    try:
        # Используем импортированный URL
        response = requests.get(STATIC_MAPS_API_SERVER, params=static_api_params)
        print(f"URL запроса: {response.url}")
        response.raise_for_status()

        image_stream = BytesIO(response.content)
        opened_image = Image.open(image_stream)
        print("Карта получена.")
        return opened_image

    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при запросе к StaticMapsAPI: {e}")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка при получении карты: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Ошибка: Не указан адрес для поиска.")
        print(f"Пример запуска: python {sys.argv[0]} Москва, ул. Ак. Королева, 12")
        sys.exit(1)

    toponym_to_find = " ".join(sys.argv[1:])
    found_toponym = geocode_address(toponym_to_find)

    if found_toponym:
        map_params = get_map_params(found_toponym)
        if map_params:
            try:
                toponym_point_str = found_toponym["Point"]["pos"]
                toponym_longitude, toponym_lattitude = map(float, toponym_point_str.split(" "))
                point_coords_for_marker = (toponym_longitude, toponym_lattitude)
            except (KeyError, IndexError, ValueError):
                print("Ошибка: Не удалось получить точные координаты для метки из объекта.")
                sys.exit(1)

            map_image = get_static_map_image(map_params, point_coords_for_marker)

            if map_image:
                print("Показ карты...")
                map_image.show()
            else:
                print("Не удалось получить изображение карты.")
        else:
            print("Не удалось рассчитать параметры для отображения карты.")
    else:
        print("Завершение работы из-за ошибки геокодирования.")

    print("Программа завершена.")
