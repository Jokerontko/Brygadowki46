import os
import shutil

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

# Tworzenie folderu "WYNIKI" i "Gotowe_brygady"
if not os.path.exists('WYNIKI'):
    os.makedirs('WYNIKI')
gotowe_brygady_folder = os.path.join("WYNIKI", "Gotowe_brygady")
os.makedirs(gotowe_brygady_folder, exist_ok=True)

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
        print(f"Brak informacji o trasie dla route_id: {route_id}")
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

    try:
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
    except Exception as e:
        print(f"Błąd przy zapisywaniu pliku {wynikowy_plik}: {e}")

# Sortowanie unikalnych route_id numerycznie
sorted_route_ids = sorted(unique_route_ids, key=int)

# Zapisz wszystkie route_id i ich informacje do pliku Kierunki.txt
with open(os.path.join('WYNIKI', 'Kierunki.txt'), 'w', encoding='utf-8') as kierunki_file:
    for route_id, (route_short_name, route_long_name) in route_id_processed.items():
        kierunki_file.write(f'{route_id}\t[{route_short_name}]\t{route_long_name}\n')

# Funkcja do przetwarzania pliku trips.txt
def process_trips_file(trips_file_path):
    with open(trips_file_path, 'r') as trips_file:
        # Odczytaj wszystkie linie
        lines = trips_file.readlines()

        # Iteruj przez każdą linię w pliku
        for line in lines[1:]:  # Pomijamy nagłówek
            # Rozdziel linijkę na elementy
            elements = line.strip().split(',')
            if len(elements) < 8:
                print(f"Nieprawidłowa linia: {line.strip()}")
                continue  # Sprawdź, czy linia jest poprawna
            
            route_id = elements[0]
            service_id = elements[1]
            trip_id = elements[2]
            block_id = elements[6]

            # Utwórz ścieżkę do pliku
            source_file_path = os.path.join('WYNIKI', service_id, route_id, f"{trip_id}.txt")
            destination_folder_path = os.path.join(gotowe_brygady_folder, service_id, block_id)

            # Utwórz folder docelowy, jeśli nie istnieje
            os.makedirs(destination_folder_path, exist_ok=True)

            # Skopiuj plik
            try:
                shutil.copy(source_file_path, destination_folder_path)
            except Exception as e:
                print(f"Błąd przy kopiowaniu pliku {source_file_path} do {destination_folder_path}: {e}")

# Procesuj plik trips.txt
process_trips_file('trips.txt')

# Funkcja do wyodrębnienia minimalnych i maksymalnych wartości arrival_time
def extract_min_max_times(folder_path):
    arrival_times = []
    
    # Przechodzimy przez wszystkie pliki w folderze
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):  # Tylko pliki tekstowe
            file_path = os.path.join(folder_path, filename)
            print(f"Otwieranie pliku: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    # Pomiń pierwsze trzy linijki
                    for _ in range(3):
                        next(file)  # Ignoruj pierwsze trzy linijki
                    for line in file:
                        line = line.strip()
                        if line:  # Sprawdź, czy linijka nie jest pusta
                            # Wyodrębnij czas przybycia (arrival_time)
                            arrival_time = line.split('\t')[3]
                            arrival_times.append(arrival_time)  # Dodaj do listy
            except Exception as e:
                print(f"Błąd przy otwieraniu pliku {file_path}: {e}")

    if not arrival_times:
        print(f"Brak czasów przybycia w folderze: {folder_path}")
        return None, None

    # Przetwórz czasy do formatu HH:MM i znajdź min i max
    processed_times = []
    for time in arrival_times:
        hours, minutes = map(int, time.split(':'))
        if hours >= 24:  # Jeśli godzina >= 24, przekształć
            hours -= 24
        processed_times.append(f"{hours:02}:{minutes:02}")

    min_time = min(processed_times)
    max_time = max(processed_times)

    return min_time, max_time

# Funkcja do tworzenia plików Godz_Rozp.txt i Godz_Zak.txt
def create_time_files(folder_path, min_time, max_time):
    min_time_file = os.path.join(folder_path, 'Godz_Rozp.txt')
    max_time_file = os.path.join(folder_path, 'Godz_Zak.txt')

    with open(min_time_file, 'w', encoding='utf-8') as file:
        file.write(min_time)
    with open(max_time_file, 'w', encoding='utf-8') as file:
        file.write(max_time)

# Iteracja przez wszystkie foldery w "Gotowe_brygady" i przetwarzanie
for service_id in os.listdir(gotowe_brygady_folder):
    service_folder_path = os.path.join(gotowe_brygady_folder, service_id)
    for route_id in os.listdir(service_folder_path):
        route_folder_path = os.path.join(service_folder_path, route_id)
        
        # Wyodrębnij najmniejsze i największe czasy
        min_time, max_time = extract_min_max_times(route_folder_path)
        if min_time is not None and max_time is not None:
            create_time_files(route_folder_path, min_time, max_time)

print("Zakończono przetwarzanie.")
input("chuj")