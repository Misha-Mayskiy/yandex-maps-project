def get_map_params(geo_object):
    try:
        point = geo_object["Point"]["pos"]
        longitude, latitude = map(float, point.split(" "))
        ll = f"{longitude:.6f},{latitude:.6f}"

        envelope = geo_object["boundedBy"]["Envelope"]
        lower_corner = envelope["lowerCorner"]
        upper_corner = envelope["upperCorner"]

        lc_lon, lc_lat = map(float, lower_corner.split(" "))
        uc_lon, uc_lat = map(float, upper_corner.split(" "))

        delta_lon = abs(uc_lon - lc_lon)
        delta_lat = abs(uc_lat - lc_lat)

        buffer_factor = 0.2
        spn_lon = delta_lon * (1 + buffer_factor)
        spn_lat = delta_lat * (1 + buffer_factor)

        min_spn = 0.002
        spn_lon = max(spn_lon, min_spn)
        spn_lat = max(spn_lat, min_spn)

        spn = f"{spn_lon:.6f},{spn_lat:.6f}"

        return {"ll": ll, "spn": spn}

    except (KeyError, IndexError, ValueError) as e:
        print(f"Ошибка при расчете параметров карты: {e}")
        print("Не удалось извлечь 'Point' или 'boundedBy' из объекта.")
        return None


if __name__ == '__main__':
    test_geo_object = {
        "Point": {"pos": "37.617635 55.755814"},
        "boundedBy": {
            "Envelope": {
                "lowerCorner": "37.609835 55.751814",
                "upperCorner": "37.625435 55.759814"
            }
        }
    }
    params = get_map_params(test_geo_object)
    if params:
        print("Рассчитанные параметры:")
        print(f"  ll = {params['ll']}")
        print(f"  spn = {params['spn']}")

    test_point_object = {
        "Point": {"pos": "30.3141 59.9386"},
        "boundedBy": {
            "Envelope": {
                "lowerCorner": "30.3141 59.9386",
                "upperCorner": "30.3141 59.9386"
            }
        }
    }
    params_point = get_map_params(test_point_object)
    if params_point:
        print("\nРассчитанные параметры для точечного объекта:")
        print(f"  ll = {params_point['ll']}")
        print(f"  spn = {params_point['spn']}")
