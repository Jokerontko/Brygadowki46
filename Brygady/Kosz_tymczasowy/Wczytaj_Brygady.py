import os

# Funkcja do sczytywania plików w formacie CSV
def czytaj_plik(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        linie = file.readlines()
    naglowek = linie[0].strip().split(',')
    zawartosc = [line.strip().split(',') for line in linie[1:]]
    return naglowek, zawartosc

# Funkcja do pobierania odpowiednich wartości route_short_name i route_long_name
def pobierz_route_informacje(route_id, routes_dict):
    route = routes_dict.get(route_id)
    if route:
        route_short_name = route[2]  # route_short_name
        route_long_name = route[3].replace(f"-{route_short_name}", "")  # Usuwanie końcówki
        return route_short_name, route_long_name
    return None, None

# Tworzenie folderu "WYNIKI"
if not os.path.exists('WYNIKI'):
    os.makedirs('WYNIKI')

# Sczytaj dane z plików
naglowek_stops, stops = czytaj_plik('stops.txt')
naglowek_stop_times, stop_times = czytaj_plik('stop_times.txt')
naglowek_trips, trips = czytaj_plik('trips.txt')
naglowek_routes, routes = czytaj_plik('routes.txt')
naglowek_calendar, calendar = czytaj_plik('calendar.txt')
naglowek_calendar_dates, calendar_dates = czytaj_plik('calendar_dates.txt')

# Tworzymy słowniki na podstawie trip_id, stop_id oraz route_id
stop_times_dict = {row[0]: [] for row in stop_times}  # trip_id jako klucz
for row in stop_times:
    stop_times_dict[row[0]].append(row)

stops_dict = {row[0]: row for row in stops}  # stop_id jako klucz

trips_dict = {row[2]: row for row in trips}  # trip_id jako klucz

routes_dict = {row[0]: row for row in routes}  # route_id jako klucz

calendar_dict = {row[0]: row for row in calendar}  # service_id jako klucz

# Przetwarzanie danych
route_id_processed = {}  # Zestaw do śledzenia przetworzonych route_id i ich informacji
unique_route_ids = set()  # Zbiór do przechowywania unikalnych route_id

for trip_id, trip in trips_dict.items():
    route_id = trip[0]
    service_id = trip[1]

    # Pobierz odpowiednie informacje o trasie
    route_short_name, route_long_name = pobierz_route_informacje(route_id, routes_dict)

    if route_short_name is None or route_long_name is None:
        continue  # Jeśli nie znaleziono danych o trasie, pomiń ten rekord

    # Dodaj informacje o trasie do słownika
    if route_id not in route_id_processed:
        route_id_processed[route_id] = (route_short_name, route_long_name)

    # Dodaj unikalne route_id do zestawu
    unique_route_ids.add(route_id)

    # Sprawdź, czy folder dla danego service_id istnieje, jeśli nie, utwórz go
    service_folder = os.path.join('WYNIKI', service_id)
    if not os.path.exists(service_folder):
        os.makedirs(service_folder)

    # Sprawdź, czy folder dla danego route_id istnieje, jeśli nie, utwórz go
    route_folder = os.path.join(service_folder, route_id)
    if not os.path.exists(route_folder):
        os.makedirs(route_folder)

    # Tworzenie nowego pliku wynikowego w folderze o nazwie route_id
    wynikowy_plik = os.path.join(route_folder, f'{trip_id}.txt')  # Użycie trip_id jako nazwy pliku

    with open(wynikowy_plik, 'w', encoding='utf-8') as wynik_file:
        # Dodaj na samej górze "[route_short_name] {route_long_name}"
        wynik_file.write(f'[{route_short_name}] {route_long_name}\n')

        # Wypisz nagłówek i kreski
        wynik_file.write('route_id\tservice_id\ttrip_id\tarrival_time\tdeparture_time\tstop_headsign\tstop_name\n')
        wynik_file.write('-' * 70 + '\n')

        # Dla każdego stop_time powiązanego z trip_id
        for stop_time in stop_times_dict[trip_id]:
            stop_id = stop_time[3]
            arrival_time = stop_time[1]
            departure_time = stop_time[2]
            stop_headsign = stop_time[5]

            # Znajdź nazwę przystanku w pliku stops
            stop_name = stops_dict[stop_id][2]

            # Wypisz linię w formacie: route_id, service_id, trip_id, arrival_time, departure_time, stop_headsign, stop_name
            wynik_file.write(f'{route_id}\t{service_id}\t{trip_id}\t{arrival_time}\t{departure_time}\t{stop_headsign}\t{stop_name}\n')

# Sortowanie unikalnych route_id numerycznie
sorted_route_ids = sorted(unique_route_ids, key=int)

# Zapisz posortowane route_id do pliku "Numeracja brygad.txt", pomijając 2 pierwsze linijki
with open(os.path.join('WYNIKI', 'Numeracja brygad.txt'), 'w', encoding='utf-8') as brygady_file:
    for i, route_id in enumerate(sorted_route_ids):
            brygady_file.write(f'{route_id}\n')

# Zapisz wszystkie route_id i ich informacje do pliku Kierunki.txt
with open(os.path.join('WYNIKI', 'Kierunki.txt'), 'w', encoding='utf-8') as kierunki_file:
    for route_id, (route_short_name, route_long_name) in route_id_processed.items():
        kierunki_file.write(f'{route_id} \t [{route_short_name}] {route_long_name}\n')