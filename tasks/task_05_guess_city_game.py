import sys
import requests
import pygame
import random
import io

from utils.config import (
    GEOCODER_API_KEY, STATIC_MAPS_API_KEY,
    GEOCODER_API_SERVER, STATIC_MAPS_API_SERVER
)

CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград", "Сочи",
    "Владивосток", "Калининград", "Якутск", "Иркутск"
]
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 450
FPS = 30

MIN_ZOOM_FACTOR = 0.20  # Минимум 20% от размера
MAX_ZOOM_FACTOR = 0.45  # Максимум 45% от размера

ANCHOR_POINT_OFFSET_FACTOR = 0.15  # Смещаемся максимум на 15% от видимой области (spn)

MIN_SPN_VALUE = 0.005  # Минимальный spn
MAX_SPN_VALUE = 0.25  # Максимальный spn (позволит видеть больше)


def geocode_city(city_name):
    geocoder_params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": city_name,
        "format": "json",
        "kind": "locality",
        "results": 1
    }
    print(f"Геокодирование города: '{city_name}'...")
    try:
        response = requests.get(GEOCODER_API_SERVER, params=geocoder_params)
        response.raise_for_status()
        json_response = response.json()
        feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]
        if not feature_member:
            print(f"   Ошибка: Город '{city_name}' не найден.")
            return None
        geo_object = feature_member[0]["GeoObject"]
        print(f"   Город '{city_name}' найден.")
        return geo_object
    except requests.exceptions.RequestException as e:
        print(f"   Ошибка сети при запросе к Геокодеру: {e}")
        return None
    except Exception as e:
        print(f"   Непредвиденная ошибка при геокодировании: {e}")
        return None


def get_zoomed_map_image(geo_object):
    """
    Gets a randomly zoomed and offset map image (bytes) for a city GeoObject,
    attempting to hide the city name. Uses the basic map view.
    Leverages city boundaries to scale the random zoom and offset.
    Returns image bytes or None on error.
    """
    if not geo_object:
        return None

    try:
        envelope = geo_object["boundedBy"]["Envelope"]
        lower_corner = envelope["lowerCorner"]
        upper_corner = envelope["upperCorner"]
        lc_lon, lc_lat = map(float, lower_corner.split(" "))
        uc_lon, uc_lat = map(float, upper_corner.split(" "))

        point = geo_object["Point"]["pos"]
        center_lon, center_lat = map(float, point.split(" "))  # Needed for fallback if point object

        delta_lon = abs(uc_lon - lc_lon)
        delta_lat = abs(uc_lat - lc_lat)

        if delta_lon == 0 and delta_lat == 0:
            spn_lon = MIN_SPN_VALUE * 15  # Увеличим для точек
            spn_lat = MIN_SPN_VALUE * 15
            anchor_lon, anchor_lat = center_lon, center_lat  # Центрируемся на точке
            offset_range_factor_local = 0.0  # Не смещаемся от точки
        else:
            random_zoom_factor = random.uniform(MIN_ZOOM_FACTOR, MAX_ZOOM_FACTOR)
            spn_lon = delta_lon * random_zoom_factor
            spn_lat = delta_lat * random_zoom_factor
            offset_range_factor_local = ANCHOR_POINT_OFFSET_FACTOR  # Используем константу смещения

            spn_lon = max(MIN_SPN_VALUE, min(spn_lon, MAX_SPN_VALUE))
            spn_lat = max(MIN_SPN_VALUE, min(spn_lat, MAX_SPN_VALUE))

            anchor_points = [
                (lc_lon, lc_lat), (uc_lon, lc_lat), (uc_lon, uc_lat), (lc_lon, uc_lat),
                (lc_lon + delta_lon / 2, lc_lat), (uc_lon, lc_lat + delta_lat / 2),
                (lc_lon + delta_lon / 2, uc_lat), (lc_lon, lc_lat + delta_lat / 2)
            ]
            anchor_lon, anchor_lat = random.choice(anchor_points)

        new_spn = f"{spn_lon:.6f},{spn_lat:.6f}"

        max_offset_lon = spn_lon * offset_range_factor_local / 2.0
        max_offset_lat = spn_lat * offset_range_factor_local / 2.0

        random_offset_lon = random.uniform(-max_offset_lon, max_offset_lon)
        random_offset_lat = random.uniform(-max_offset_lat, max_offset_lat)

        new_center_lon = anchor_lon + random_offset_lon
        new_center_lat = anchor_lat + random_offset_lat
        new_ll = f"{new_center_lon:.6f},{new_center_lat:.6f}"

        map_type = "map"

        static_api_params = {
            "ll": new_ll,
            "spn": new_spn,
            "l": map_type,
            "size": f"{SCREEN_WIDTH},{SCREEN_HEIGHT}",
            "apikey": STATIC_MAPS_API_KEY
        }

        print(
            f"   Запрос карты Static API для '{geo_object.get('name', 'города')}' около точки {new_ll}, spn={new_spn}...")
        response = requests.get(STATIC_MAPS_API_SERVER, params=static_api_params)
        response.raise_for_status()
        print("   Карта получена.")
        return response.content

    except requests.exceptions.RequestException as e:
        print(f"   Ошибка сети при запросе к StaticMapsAPI: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"   Ошибка при обработке гео-данных для карты: {e}")
        return None
    except Exception as e:
        print(f"   Непредвиденная ошибка при получении карты: {e}")
        return None


if __name__ == "__main__":
    print("Подготовка игры 'Угадай город'...")

    game_slides = []
    for city in CITIES:
        geo_obj = geocode_city(city)
        if geo_obj:
            image_bytes = get_zoomed_map_image(geo_obj)
            if image_bytes:
                game_slides.append({
                    "name": city,
                    "image_bytes": image_bytes
                })
            else:
                print(f"   Не удалось получить карту для города: {city}")
        else:
            print(f"   Не удалось геокодировать город: {city}")

    if not game_slides:
        print("\nОшибка: Не удалось подготовить ни одного слайда для игры. Выход.")
        sys.exit(1)

    random.shuffle(game_slides)
    print(f"\nПодготовлено слайдов: {len(game_slides)}. Начинаем игру!")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Угадай город! (Нажмите любую клавишу для следующего)")
    clock = pygame.time.Clock()

    current_slide_index = -1
    current_image_surface = None
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                current_slide_index = (current_slide_index + 1) % len(game_slides)
                slide_data = game_slides[current_slide_index]
                try:
                    image_stream = io.BytesIO(slide_data["image_bytes"])
                    current_image_surface = pygame.image.load(image_stream).convert()
                    print(f"\nСлайд {current_slide_index + 1}/{len(game_slides)}. Какой это город?")
                except pygame.error as e:
                    print(f"Ошибка загрузки изображения для слайда {current_slide_index}: {e}")
                    current_image_surface = None

        screen.fill((0, 0, 0))
        if current_image_surface:
            screen.blit(current_image_surface, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    print("\nИгра завершена.")
    sys.exit(0)
