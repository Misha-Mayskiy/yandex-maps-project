# Yandex Maps API Python Scripts Project

This repository contains a collection of Python scripts demonstrating the use of various Yandex Maps APIs (Geocoder, Static Maps, Geosearch) to solve specific tasks.

## Project Description

Python project implementing tasks using Yandex Maps APIs: Geocoding, Static Maps rendering (with auto-scale/markers), and Geosearch for nearby places. Structured into reusable utils and specific task solutions. Educational project context.

## Project Structure

```
yandex_map_project/
├── .gitignore
├── README.md
├── LICENSE
├── requirements.txt
├── utils/              # Utility modules
│   ├── __init__.py
│   ├── config.py       # API keys and server URLs
│   ├── geo_utils.py    # Geodetic calculations (e.g., Haversine)
│   └── map_utils.py    # Map parameter calculations (ll, spn)
├── tasks/              # Scripts for specific tasks
│   ├── __init__.py
│   ├── task_01_search_and_show.py # Find object and show on map
│   └── task_02_find_and_show_pharmacy.py # Find nearest pharmacy & show
│   └── ...                        # Other task scripts
```

## Features

*   Modular structure for code reuse (utilities in `utils/`).
*   Centralized storage for API keys and URLs (in `utils/config.py`).
*   Clear separation of scripts by task (in `tasks/`).
*   Examples of using Geocoder, Static Maps, and Geosearch APIs.
*   Automatic map scaling based on object boundaries (`task_01`).
*   Automatic map positioning based on multiple points (`task_02`).
*   Calculation of distances (Haversine formula).
*   Displaying results using the Pillow library (opens in default OS image viewer).

## Prerequisites

*   Python 3.x
*   Python libraries (see `requirements.txt`)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd yandex_map_project
    ```
2.  **(Recommended)** Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## API Keys

**Important:** The API keys required for the scripts are stored in the `utils/config.py` file. This repository uses keys provided during an educational course (e.g., Yandex.Practicum). These keys have limitations and are intended for educational purposes only.

For use in your own projects, you must obtain personal API keys from the [Yandex Developer Portal](https://developer.tech.yandex.ru/) and replace the values in `utils/config.py`. In real-world applications, API keys should **not** be stored directly in code or configuration files committed to version control; use environment variables or other secure methods.

## Usage

To run a script for a specific task, navigate to the project's **root directory** (`yandex_map_project`) in your terminal and execute the command using Python's `-m` flag to run it as a module:

```bash
python -m tasks.<script_filename_without_py> [required_arguments]
```

See the "Task List" section below for specific arguments for each task.

## Adding New Tasks

1.  Create a new `.py` file inside the `tasks/` directory (e.g., `task_03_calculate_distance.py`).
2.  Write the Python code to solve the new task.
3.  Import necessary utilities and configuration from the `utils` directory:
    ```python
    from utils.map_utils import get_map_params # Example
    from utils.geo_utils import haversine_distance # Example
    from utils.config import GEOCODER_API_KEY # Example
    ```
4.  Add a description of the task and its usage instructions to the "Task List" in this `README.md` file (optional but recommended).

## Task List

*   **`task_01_search_and_show.py`**: Finds a geographical object by its address (provided as a command-line argument) using the Geocoder API. Displays the object on a Static Maps API image, automatically calculating the map scale (`spn`) to fit the object's bounds and adding a marker at its center.
    *   **Usage (ex.)** `python -m tasks.task_01_search_and_show Москва, Красная площадь`

*   **`task_02_find_and_show_pharmacy.py`**: Finds the nearest pharmacy to an address specified as a command-line argument. It first uses the Geocoder API to get the coordinates of the address, then uses the Geosearch API to find the closest pharmacy. It displays a Static Maps API image with markers for both the original address (blue) and the found pharmacy (red), automatically adjusting the view to include both points.
    *   **Usage (ex.)** `python -m tasks.task_02_find_and_show_pharmacy Москва, Ленинский проспект, 1`

*   **`task_03_find_10_pharmacies.py`**: Finds up to 10 nearest pharmacies to an address specified as a command-line argument using Geocoder and Geosearch APIs. Displays a Static Maps API image with markers for all found pharmacies. Markers are color-coded based on operating hours: green for 24/7, blue for standard hours, grey for unknown hours.
    *   **Usage (ex.):** `python -m tasks.task_03_find_10_pharmacies "Санкт-Петербург, Невский проспект, 28"`

*   **`task_04_find_district.py`**: Определяет административный район, к которому относится адрес, заданный в командной строке. Сначала получает координаты адреса, затем использует эти координаты для обратного геокодирования с параметром `kind=district`.
    *   **Usage (ex.):** `python -m tasks.task_04_find_district "Москва, улица Льва Толстого, 16"`

*   **`task_05_guess_city_game.py`**: Запускает прототип игры "Угадай город". Программа загружает карты для списка предопределенных городов, стараясь выбрать масштаб и тип карты (`sat,skl`) так, чтобы название города не было видно. Затем отображает эти карты в случайном порядке в окне Pygame. Игрок может листать карты (слайды), нажимая любую клавишу. Название города для текущего слайда выводится в консоль (в реальной игре его нужно было бы угадывать).
    *   **Usage:** `python -m tasks.task_05_guess_city_game` (No command-line arguments needed)