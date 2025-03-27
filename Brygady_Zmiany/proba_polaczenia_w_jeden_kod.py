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

            # Sprawdź, czy plik źródłowy istnieje
            if os.path.exists(source_file_path):
                # Skopiuj plik do folderu docelowego
                shutil.copy(source_file_path, destination_folder_path)
                print(f"Skopiowano: {source_file_path} do {destination_folder_path}")
            else:
                print(f"Plik nie istnieje: {source_file_path}")

# Ustal ścieżkę do pliku trips.txt
trips_file_path = "trips.txt"
process_trips_file(trips_file_path)    

# Funkcja sortująca linie według arrival_time
def sort_lines_by_arrival_time(folder_path):
    print(f"Przetwarzanie folderu: {folder_path}")
    
    # Utwórz ścieżkę do pliku GOTOWE.txt
    output_file_path = os.path.join(folder_path, 'GOTOWE.txt')
    
    # Lista do przechowywania linijek
    lines = []

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
                            lines.append(line)  # Dodaj linijki do listy
            except Exception as e:
                print(f"Błąd przy otwieraniu pliku {file_path}: {e}")

    if not lines:
        print(f"Brak linijek w folderze: {folder_path}")
        return

    # Sprawdzenie poprawności danych przed sortowaniem
    valid_lines = []
    for line in lines:
        parts = line.split('\t')
        if len(parts) > 3:  # Upewnij się, że jest wystarczająco dużo elementów
            valid_lines.append(line)
        else:
            print(f"Linia niepoprawna (za mało elementów): {line}")

    # Sortowanie linijek według arrival_time
    try:
        valid_lines.sort(key=lambda x: x.split('\t')[3])  # index 3 to arrival_time
    except Exception as e:
        print(f"Błąd przy sortowaniu: {e}")
        return

    # Zapisz posortowane linijki do pliku GOTOWE.txt
    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            # Dodaj nagłówek
            output_file.write("route_id\tservice_id\ttrip_id\tarrival_time\tdeparture_time\tstop_headsign\tstop_name\n")
            # Dodaj linię z kreskami
            output_file.write("-------------------------------------------------------------------------------\n")
            
            last_trip_id = None  # Zmienna do przechowywania ostatniego trip_id
            for line in valid_lines:
                current_trip_id = line.split('\t')[2]  # index 2 to trip_id
                if last_trip_id is not None and current_trip_id != last_trip_id:
                    output_file.write('\n')  # Dodaj pustą linię między różnymi trip_id
                output_file.write(line + '\n')
                last_trip_id = current_trip_id  # Aktualizuj ostatnie trip_id
        print(f"Zapisano do {output_file_path}")
    except Exception as e:
        print(f"Błąd przy zapisywaniu do pliku {output_file_path}: {e}")

# Funkcja do przetwarzania folderów
def process_folders(base_path):
    print(f"Przechodzenie przez folder: {base_path}")
    
    # Przechodzimy przez wszystkie foldery w folderze bazowym
    for foldername in os.listdir(base_path):
        folder_path = os.path.join(base_path, foldername)
        if os.path.isdir(folder_path):  # Tylko foldery
            sort_lines_by_arrival_time(folder_path)

if __name__ == "__main__":
    base_paths = [
        "WYNIKI/Gotowe_brygady/1",
        "WYNIKI/Gotowe_brygady/2",
        "WYNIKI/Gotowe_brygady/3",
        "WYNIKI/Gotowe_brygady/4"
    ]
    
    for base_path in base_paths:
        if os.path.exists(base_path):
            process_folders(base_path)
        else:
            print(f"Ścieżka nie istnieje: {base_path}")

    # Zapisz nazwy folderów w folderach "1", "2", "3" i "4" do pliku "Numeracja brygad.txt"
    with open(os.path.join('WYNIKI', 'Numeracja brygad.txt'), 'w', encoding='utf-8') as brygady_file:
        for base_path in base_paths:
            if os.path.exists(base_path):
                # Odczytaj nazwy folderów wewnątrz folderów "1", "2", "3", "4"
                for folder in os.listdir(base_path):
                    if os.path.isdir(os.path.join(base_path, folder)):
                        brygady_file.write(f'{folder}\t\n')
                brygady_file.write('\n')  # Dodaj pustą linię po każdym zestawie folderów

input("Naciśnij Enter, aby zakończyć...")
