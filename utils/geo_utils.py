import math


def haversine_distance(point1_lonlat, point2_lonlat):
    """
    Calculates the great-circle distance between two points
    on the earth (specified in decimal degrees) using Haversine formula.

    Args:
        point1_lonlat (tuple): (longitude, latitude) for first point in degrees.
        point2_lonlat (tuple): (longitude, latitude) for second point in degrees.

    Returns:
        float: Distance in kilometers.
    """
    lon1, lat1 = point1_lonlat
    lon2, lat2 = point2_lonlat

    R = 6371.0

    lon1_rad, lat1_rad, lon2_rad, lat2_rad = map(math.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
