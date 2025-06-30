import os
import time
import csv
import re
import shutil
import datetime
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

def clear_screen():
    # Sprawdź system operacyjny
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix/Linux/macOS
        os.system('clear')

def WczytajBrygady():
    # Funkcja do sczytywania plików w formacie CSV
    clear_screen()
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
    Czyzmienic = input("Czy chcesz zmienić nazwy folderów? t/n: ")
    if Czyzmienic == "t":
        ZmienNazewnictwo()
    # Funkcja sortująca linie według arrival_time
    def sort_lines_by_arrival_time(folder_path):
        print(f"Przetwarzanie folderu: {folder_path}")
        
        # Utwórz ścieżkę do pliku GOTOWE.txt
        output_file_path = os.path.join(folder_path, 'PierwotneGotowe.txt')
        
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
                    
                    clear_screen()
    clear_screen()
                    




                    
        
        
import os
import re

def natural_sort_key(text):
    # Funkcja pomocnicza do naturalnego sortowania, dzieli tekst na część tekstową i numeryczną
    return [int(text_part) if text_part.isdigit() else text_part.lower() for text_part in re.split('([0-9]+)', text)]

def StwórzLinietxt():
    clear_screen()
    # Ścieżki do plików
    kierunki_file = 'WYNIKI/Kierunki.txt'
    gotowe_dirs = ['WYNIKI/Gotowe_brygady/1', 'WYNIKI/Gotowe_brygady/2', 'WYNIKI/Gotowe_brygady/3', 'WYNIKI/Gotowe_brygady/4']

    # Odczyt danych z pliku Kierunki.txt
    kierunki = {}
    with open(kierunki_file, 'r', encoding='utf-8') as k_file:
        for line in k_file:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                route_id = parts[0]
                numer_linii = parts[1].strip("[]")  # Usunięcie nawiasów
                kierunki[route_id] = numer_linii

    # Przeszukiwanie podfolderów
    for gotowe_dir in gotowe_dirs:
        for subdir, _, files in os.walk(gotowe_dir):
            numer_linii_set = set()  # Zestaw do unikalnych numerów linii
            for filename in files:
                if filename == 'GOTOWE.txt':
                    file_path = os.path.join(subdir, filename)

                    with open(file_path, 'r', encoding='utf-8') as g_file:
                        for line in g_file:
                            parts = line.strip().split('\t')
                            if len(parts) > 0:
                                route_id = parts[0]
                                if route_id in kierunki:
                                    numer_linii_set.add(kierunki[route_id])

            # Zapis do pliku Linie.txt w każdym podfolderze
            if numer_linii_set:
                linie_file = os.path.join(subdir, 'Linie.txt')
                # Sortowanie z użyciem funkcji natural_sort_key do obsługi liter i cyfr
                sorted_numer_linii = sorted(numer_linii_set, key=natural_sort_key)

                with open(linie_file, 'w', encoding='utf-8') as l_file:
                    for numer in sorted_numer_linii:
                        l_file.write(numer + '\n')

                # Sprawdzanie, czy istnieje plik 'rezerwa.txt' w danym folderze
                rezerwa_file = os.path.join(subdir, 'rezerwa.txt')
                if os.path.exists(rezerwa_file):
                    with open(linie_file, 'a', encoding='utf-8') as l_file:
                        l_file.write("Rez\n")

    clear_screen()





                
                
def StwórzGodzRozpGodzZak():
    clear_screen()

    # Ustalamy ścieżki do głównych folderów
    main_folders = [
        'WYNIKI/Gotowe_brygady/1',
        'WYNIKI/Gotowe_brygady/2',
        'WYNIKI/Gotowe_brygady/3',
        'WYNIKI/Gotowe_brygady/4'
    ]

    # Funkcja do przetwarzania pliku GOTOWE.txt
    def process_file(file_path):
        print(f"Przetwarzanie pliku: {file_path}")
        try:
            with open(file_path, 'r', encoding='latin-1') as file:  # Zmiana kodowania
                # Pomijamy pierwsze dwie linijki
                lines = file.readlines()[2:]

                # Odczytujemy czasy przybycia (arrival_time)
                arrival_times = []
                last_line = None  # Zmienna na przechowanie ostatniego wiersza
                for line in lines:
                    # Sprawdzamy, czy linia nie jest pusta
                    if line.strip():
                        columns = line.split('\t')
                        if len(columns) > 3:
                            arrival_times.append(columns[3])  # Czas przybycia
                        last_line = line  # Zapamiętujemy ostatnią linię

                if arrival_times:
                    # Zamieniamy czasy na format HH:MM
                    arrival_times_hh_mm = [time[:5] for time in arrival_times]
                    arrival_times_sorted = sorted(arrival_times_hh_mm)
                    min_time = arrival_times_sorted[0]
                    max_time = arrival_times_sorted[-1]

                    # Sprawdzamy, czy ostatnia linia to REZ
                    if last_line and "REZ" in last_line:
                        # Odczytujemy czasy z ostatniej linii
                        columns = last_line.split('\t')
                        max_time = columns[4]  # Przypisujemy ${Godz_Zak}
                        # Skracamy czas do formatu HH:MM (jeśli jest w formacie HH:MM:SS)
                        max_time = max_time[:5]

                    # Skracamy min_time i max_time do formatu HH:MM (jeśli mają format HH:MM:SS)
                    min_time = min_time[:5]
                    max_time = max_time[:5]

                    print(f"Najmniejszy czas przybycia: {min_time}")
                    print(f"Największy czas przybycia: {max_time}")

                    # Ustalamy ścieżki do plików Godz_Rozp.txt i Godz_Zak.txt w bieżącym folderze
                    folder_path = os.path.dirname(file_path)
                    start_file_path = os.path.join(folder_path, 'Godz_Rozp.txt')
                    end_file_path = os.path.join(folder_path, 'Godz_Zak.txt')

                    # Zapisujemy najmniejszy czas do Godz_Rozp.txt
                    with open(start_file_path, 'w', encoding='utf-8') as start_file:
                        start_file.write(min_time + '\n')

                    # Zapisujemy największy czas do Godz_Zak.txt
                    with open(end_file_path, 'w', encoding='utf-8') as end_file:
                        end_file.write(max_time + '\n')

                    print(f"Zapisano do {start_file_path} i {end_file_path}.")
                else:
                    print("Brak danych do przetworzenia w pliku.")
        except FileNotFoundError:
            print(f"Plik {file_path} nie został znaleziony.")
        except Exception as e:
            print(f"Błąd w przetwarzaniu pliku {file_path}: {e}")

    # Iterujemy przez wszystkie foldery
    for main_folder in main_folders:
        # Sprawdzamy, czy folder istnieje
        if not os.path.exists(main_folder):
            print(f"Folder {main_folder} nie istnieje.")
        else:
            print(f"Rozpoczynam przetwarzanie folderu: {main_folder}")
            # Przechodzimy przez wszystkie podfoldery
            for root, dirs, files in os.walk(main_folder):
                for file in files:
                    if file == 'GOTOWE.txt':
                        process_file(os.path.join(root, file))





                        
                        
def StwórzBrygadyBIS():
    clear_screen()
  
    # Funkcja pomocnicza do sortowania numerów
    def numer_sort(key):
        return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', key)]  # Użycie surowego stringa r''

    # Lista folderów do przetworzenia
    foldery_do_przetworzenia = ["1", "2", "3", "4"]

    # Iterujemy po folderach
    for folder_num in foldery_do_przetworzenia:
        # Ścieżka do folderu
        sciezka = os.path.abspath(f"WYNIKI/Gotowe_brygady/{folder_num}")  # Użycie absolutnej ścieżki

        # Sprawdzamy, czy ścieżka istnieje
        if not os.path.exists(sciezka):
            print(f"Podana ścieżka {sciezka} nie istnieje!")
        else:
            # Pobieranie nazw folderów
            foldery = [nazwa for nazwa in os.listdir(sciezka) if os.path.isdir(os.path.join(sciezka, nazwa))]

            # Sortowanie listy folderów numerycznie
            foldery.sort(key=numer_sort)

            # Ścieżka do pliku wyjściowego
            plik_wyjsciowy = os.path.join(sciezka, "Brygady_BIS.txt")

            # Tworzenie pliku i zapis danych
            try:
                with open(plik_wyjsciowy, "w") as plik:
                    # Zapisanie nagłówka
                    plik.write("Numer\tB/JZ\n")
                    plik.write("-------------\n")
                    
                    # Zapisanie folderów z zamienionym "_" na "/"
                    for folder in foldery:
                        folder_zmieniony = folder.replace("_", "/")  # Zmiana "_" na "/"
                        plik.write(f"{folder_zmieniony}\tX\n")
                
                # Potwierdzenie zapisania
                print(f"Plik zapisano w {plik_wyjsciowy}")
            except Exception as e:
                print(f"Wystąpił błąd podczas zapisywania pliku: {e}")
            
            # Dodatkowa informacja - lista folderów, które zostały znalezione
            print(f"Znalezione foldery w {sciezka}:")
            for folder in foldery:
                print(f"- {folder}")

            # Sprawdzanie zawartości pliku, jeżeli chcesz zobaczyć, co zostało zapisane
            with open(plik_wyjsciowy, "r") as plik:
                print("\nZawartość pliku:")
                print(plik.read())


  


  
  
  


  
  
def UtwórzGOTOWEtxt():
    clear_screen()

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

  
  
  
  
  
  
  
  
import os

def DodajRezerwe():
    clear_screen()
    # Wczytywanie wartości z klawiatury
    typ_dnia = input("Wprowadź typ dnia: ")
    brygada = input("Wprowadź brygadę: ")
    rozpoczecie = input("Wprowadź godzinę rozpoczęcia (format HH:MM): ")
    zakonczenie = input("Wprowadź godzinę zakończenia (format HH:MM): ")

    # Funkcja do dodania sekund, jeśli ich brak
    def dodaj_sekundy(czas):
        if len(czas.split(":")) == 2:  # Jeśli czas ma tylko godzinę i minutę
            return f"{czas}:00"  # Dodajemy sekundy
        return czas  # Jeśli już są sekundy, zwracamy czas bez zmian

    # Używamy funkcji do dodania sekund do rozpoczecie i zakonczenie
    rozpoczecie = dodaj_sekundy(rozpoczecie)
    zakonczenie = dodaj_sekundy(zakonczenie)

    # Tworzenie ścieżki do folderu
    sciezka_folder = os.path.join("WYNIKI", "Gotowe_brygady", typ_dnia, brygada)

    # Sprawdzanie, czy folder istnieje, jeśli nie - tworzymy go
    if not os.path.exists(sciezka_folder):
        try:
            os.makedirs(sciezka_folder)
            print(f"Utworzono folder: {sciezka_folder}")
        except Exception as e:
            print(f"Nie udało się utworzyć folderu: {e}")
            return  # Kończymy funkcję, jeśli wystąpił błąd podczas tworzenia folderu

    # Ścieżka do pliku rezerwa.txt
    plik_wyjsciowy = os.path.join(sciezka_folder, "rezerwa.txt")

    # Jeśli plik istnieje, tworzymy nowy z numerem
    if os.path.exists(plik_wyjsciowy):
        i = 2
        while True:
            nowa_nazwa_pliku = os.path.join(sciezka_folder, f"rezerwa{i}.txt")
            if not os.path.exists(nowa_nazwa_pliku):
                plik_wyjsciowy = nowa_nazwa_pliku
                break
            i += 1

    # Zawartość pliku w odpowiednim formacie
    tresc_pliku = (
        "[Rez] Rezerwa\n"
        "route_id\tservice_id\ttrip_id\tarrival_time\tdeparture_time\tstop_headsign\tstop_name\n"
        "-------------------------------------------------------------------------------\n"
        f"REZ\tR\t-\t{rozpoczecie}\t{zakonczenie}\t\tRezerwa\n"
    )

    # Tworzenie pliku i zapisanie danych
    try:
        with open(plik_wyjsciowy, "w") as plik:
            plik.write(tresc_pliku)
        print(f"Plik zapisano w {plik_wyjsciowy}")
    except Exception as e:
        print(f"Wystąpił błąd podczas zapisywania pliku: {e}")



def BISDodajRezerwe():
    clear_screen()
    # Wczytywanie wartości z klawiatury
    typ_dnia = input("Wprowadź typ dnia: ")
    clear_screen()
    while True:
        print("Wybrany typ dnia: " + typ_dnia)
        brygada = input("Wprowadź brygadę: ")
        rozpoczecie = input("Wprowadź godzinę rozpoczęcia (format HH:MM): ")
        zakonczenie = input("Wprowadź godzinę zakończenia (format HH:MM): ")

        # Funkcja do dodania sekund, jeśli ich brak
        def dodaj_sekundy(czas):
            if len(czas.split(":")) == 2:  # Jeśli czas ma tylko godzinę i minutę
                return f"{czas}:00"  # Dodajemy sekundy
            return czas  # Jeśli już są sekundy, zwracamy czas bez zmian

        # Używamy funkcji do dodania sekund do rozpoczecie i zakonczenie
        rozpoczecie = dodaj_sekundy(rozpoczecie)
        zakonczenie = dodaj_sekundy(zakonczenie)

        # Tworzenie ścieżki do folderu
        sciezka_folder = os.path.join("WYNIKI", "Gotowe_brygady", typ_dnia, brygada)

        # Sprawdzanie, czy folder istnieje, jeśli nie - tworzymy go
        if not os.path.exists(sciezka_folder):
            try:
                os.makedirs(sciezka_folder)
                print(f"Utworzono folder: {sciezka_folder}")
            except Exception as e:
                print(f"Nie udało się utworzyć folderu: {e}")
                return  # Kończymy funkcję, jeśli wystąpił błąd podczas tworzenia folderu

        # Ścieżka do pliku rezerwa.txt
        plik_wyjsciowy = os.path.join(sciezka_folder, "rezerwa.txt")

        # Jeśli plik istnieje, tworzymy nowy z numerem
        if os.path.exists(plik_wyjsciowy):
            i = 2
            while True:
                nowa_nazwa_pliku = os.path.join(sciezka_folder, f"rezerwa{i}.txt")
                if not os.path.exists(nowa_nazwa_pliku):
                    plik_wyjsciowy = nowa_nazwa_pliku
                    break
                i += 1

        # Zawartość pliku w odpowiednim formacie
        tresc_pliku = (
        "[Rez] Rezerwa\n"
        "route_id\tservice_id\ttrip_id\tarrival_time\tdeparture_time\tstop_headsign\tstop_name\n"
        "-------------------------------------------------------------------------------\n"
        f"REZ\tR\t-\t{rozpoczecie}\t{zakonczenie}\t\tRezerwa\n"
        )

        # Tworzenie pliku i zapisanie danych
        try:
            with open(plik_wyjsciowy, "w") as plik:
                plik.write(tresc_pliku)
            clear_screen()
            print(f"Plik zapisano w {plik_wyjsciowy}")
        except Exception as e:
            clear_screen()
            print(f"Wystąpił błąd podczas zapisywania pliku: {e}")  
  
  
  
  
  
  
  
  
  
  
  
                        

      
      
      
      
      
      
      
      
      
      
      
      
      
      
      

      
      
def NazwijBrygady():
    clear_screen()
    def zmien_nazwy_folderow():
        # Ścieżki do folderów
        folder_paths = ["WYNIKI/Gotowe_brygady/1", "WYNIKI/Gotowe_brygady/2", 
                        "WYNIKI/Gotowe_brygady/3", "WYNIKI/Gotowe_brygady/4"]
        numeracja_file_path = "WYNIKI/Numeracja brygad.txt"

        # Wczytaj dane z pliku Numeracja brygad.txt
        numeracja_map = {}

        try:
            with open(numeracja_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                for row in reader:
                    if len(row) == 2:
                        block_id, id_brygady = row
                        if id_brygady:  # Sprawdź, czy id_brygady nie jest puste
                            numeracja_map[block_id] = id_brygady
                        else:
                            print(f"Pusta wartość id_brygady dla block_id: {block_id}")
        except FileNotFoundError:
            print(f"Nie znaleziono pliku: {numeracja_file_path}")
            return
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku: {e}")
            return

        # Przejdź przez foldery
        for folder_path in folder_paths:
            if not os.path.exists(folder_path):
                print(f"Folder nie istnieje: {folder_path}")
                continue
            
            for folder_name in os.listdir(folder_path):
                folder_full_path = os.path.join(folder_path, folder_name)
                
                # Sprawdź, czy to jest folder
                if os.path.isdir(folder_full_path):
                    # Sprawdź, czy nazwa folderu pasuje do block_id
                    if folder_name in numeracja_map:
                        new_folder_name = numeracja_map[folder_name]
                        
                        # Zabezpieczenie przed podfolderami – usuń ukośniki
                        new_folder_name = new_folder_name.replace('/', '_')
                        new_folder_full_path = os.path.join(folder_path, new_folder_name)
                        
                        try:
                            # Zmień nazwę folderu
                            os.rename(folder_full_path, new_folder_full_path)
                            print(f"Zmieniono nazwę folderu: {folder_name} -> {new_folder_name}")
                        except Exception as e:
                            print(f"Błąd przy zmianie nazwy folderu {folder_name}: {e}")

    # Wywołanie funkcji zmieniającej nazwy folderów
    zmien_nazwy_folderow()
   
      
      
      
      

      
      
def StwórzZbiorczyKursy():
    clear_screen()
    
    # Funkcja do odczytu rozkładów z pliku
    def read_schedule(file_path):
        schedules = []
        current_schedule = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Błąd przy odczycie pliku: {e}")
            return []
        
        for line in lines:
            if line.strip() == "":
                if current_schedule:
                    schedules.append(current_schedule)
                    current_schedule = []
            else:
                current_schedule.append(line)
        
        if current_schedule:
            schedules.append(current_schedule)

        print(f"Znaleziono {len(schedules)} rozkładów.")
        return schedules

    # Funkcja do konwersji czasu z formatu HH:MM:SS na minuty
    def convert_time_to_minutes(time_str):
        hours, minutes, seconds = map(int, time_str.split(':'))
        return hours * 60 + minutes + seconds / 60

    # Funkcja do wyciągania czasów odjazdu
    def get_departure_times(schedule):
        times = []
        for line in schedule:
            if re.match(r'^\d+\s+\d+\s+\d+\s+\d{2}:\d{2}:\d{2}\s+(\d{2}:\d{2}:\d{2})', line):
                departure_time_str = line.split()[4]
                try:
                    departure_time_in_minutes = convert_time_to_minutes(departure_time_str)
                    times.append((departure_time_in_minutes, line))
                except ValueError as e:
                    print(f"Błąd konwersji czasu odjazdu: {departure_time_str}. Błąd: {e}")
        return times

    # Funkcja filtrująca dane rozkładu, zwraca min. czas odjazdu, nazwę folderu i kierunek
    def filter_schedule(schedule):
        header = schedule[0:2]  # Pierwsze dwie linie
        departure_times = get_departure_times(schedule[2:])  # Czas odjazdu w kursach
        
        if not departure_times:
            print("Brak czasów odjazdów w rozkładzie.")
            return None  # Brak danych, zwróć None
        
        min_time_line = min(departure_times, key=lambda x: x[0])[1]
        folder_name = os.path.basename(schedule[0].strip())  # Usuwamy 'Folder:' i zachowujemy tylko nazwę folderu
        direction = header[1].strip()  # Kierunek jest w drugiej linii
        return min_time_line, folder_name, direction

    # Funkcja zapisująca dane do pliku PojazdyLIVE.txt
    def write_to_pojazdy_live(data, output_path):
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                for line in data:
                    file.write(line + "\n")
        except Exception as e:
            print(f"Błąd przy zapisie do pliku: {e}")

    # Funkcja do formatowania godziny, uwzględniająca odjęcie 24 godzin, jeżeli godzina >= 24:00
    def format_time(time_str):
        hours, minutes, _ = time_str.split(':')
        hours = int(hours)
        minutes = int(minutes)
        
        # Jeżeli godzina >= 24, odejmujemy 24 godziny
        if hours >= 24:
            hours -= 24
        
        return f"{hours:02}:{minutes:02}"

    # Funkcja do wyciągania numeru linii (część tekstu między "[" i "]")
    def extract_line(direction):
        match = re.search(r'\[(.*?)\]', direction)
        return match.group(1) if match else ""

    dirs_to_process = ['WYNIKI/Gotowe_brygady/1', 'WYNIKI/Gotowe_brygady/2', 'WYNIKI/Gotowe_brygady/3', 'WYNIKI/Gotowe_brygady/4']

    for main_dir in dirs_to_process:
        if not os.path.exists(main_dir):
            print(f"Błąd: Folder {main_dir} nie istnieje!")
            continue

        output_file = os.path.join(main_dir, 'Kursy.txt')

        # Tworzenie pliku Kursy.txt
        with open(output_file, 'w', encoding='utf-8') as kursy_file:
            for root, dirs, files in os.walk(main_dir):
                if root != main_dir:
                    folder_name = os.path.basename(root)
                    for file in files:
                        if file.endswith('.txt') and re.search(r'\d', file):
                            file_path = os.path.join(root, file)

                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()
                                    kursy_file.write(f"Folder: {folder_name}\n")
                                    kursy_file.write(content + '\n\n')
                                    print(f"Plik {file_path} został dodany do {output_file}")
                            except Exception as e:
                                print(f"Błąd przy przetwarzaniu pliku {file_path}: {e}")

        print(f"Zawartość została zapisana do pliku {output_file}")

        schedules = read_schedule(output_file)
        if schedules:
            min_times_info = []
            for schedule in schedules:
                result = filter_schedule(schedule)
                if result:
                    min_time_line, folder_name, direction = result
                    
                    min_time_str = min_time_line.split()[4]  # Czas odjazdu w formacie HH:MM:SS
                    formatted_time = format_time(min_time_str)  # Formatujemy godzinę
                    line = extract_line(direction)  # Wyciągamy numer linii

                    # Zapisujemy do listy: godzina, numer folderu, kierunek, linia
                    min_times_info.append(f"{formatted_time}\t{folder_name}\t{direction}\t{line}")
            
            # Tworzymy plik PojazdyLIVE.txt
            output_pojazdy_file = os.path.join(main_dir, 'PojazdyLIVE.txt')
            write_to_pojazdy_live(min_times_info, output_pojazdy_file)
            print(f"Minimalne godziny odjazdu, numery folderów, kierunki i linie zapisane do pliku {output_pojazdy_file}")
        else:
            print("Brak rozkładów do przetworzenia.")




      
          
def Podmiana():
    typ_podmiany = input("Wprowadź typ podmiany (nic = w mieście, B = w bazie): ")
    if typ_podmiany == "B":
        SpecialDodajPodmiane()
    else:
        DodajPodmiane()
        
def BISPodmiana():
    while True:  # Pętla nieskończona
        typ_podmiany = input("Wprowadź typ podmiany (nic = w mieście, B = w bazie, Q = wyjście): ")
        
        if typ_podmiany == "Q":  # Opcja wyjścia
            print("Koniec programu.")
            break  # Przerwij pętlę
        
        if typ_podmiany == "B":
            SpecialDodajPodmiane()  # Wywołanie funkcji
        else:
            DodajPodmiane()  # Wywołanie innej funkcji

    

        
def DodajPodmiane():
    clear_screen()
    # Wczytywanie wartości z klawiatury
    
    typ_dnia = input("Wprowadź typ dnia: ")
    brygada = input("Wprowadź brygadę: ")
    Przystanek = input("Przystanek: ")
    Godzina = input("Godzina podmiany (HH:MM): ")

    # Tworzenie ścieżki do folderu
    sciezka_folder = os.path.join("WYNIKI", "Gotowe_brygady", typ_dnia, brygada)

    # Sprawdzanie, czy folder istnieje, jeśli nie - tworzymy go
    if not os.path.exists(sciezka_folder):
        try:
            os.makedirs(sciezka_folder)
            print(f"Utworzono folder: {sciezka_folder}")
        except Exception as e:
            print(f"Nie udało się utworzyć folderu: {e}")
            return  # Kończymy funkcję, jeśli wystąpił błąd podczas tworzenia folderu

    # Ścieżka do pliku rezerwa.txt
    plik_wyjsciowy = os.path.join(sciezka_folder, "podmiana.txt")

    # Zawartość pliku w odpowiednim formacie
    tresc_pliku = (
        f"{Przystanek}\t{Godzina}"
    )

    # Tworzenie pliku i zapisanie danych
    try:
        with open(plik_wyjsciowy, "w", encoding='utf-8') as plik:
            plik.write(tresc_pliku)
        print(f"Plik zapisano w {plik_wyjsciowy}")
    except Exception as e:
        print(f"Wystąpił błąd podczas zapisywania pliku: {e}")      
      
      


def SpecialDodajPodmiane():
    clear_screen()
    # Wczytywanie wartości z klawiatury
    typ_dnia = input("Wprowadź typ dnia: ")
    brygada = input("Wprowadź brygadę: ")
    PrzystanekZakA = input("Przystanek zakończenia zmiany A: ")
    GodzinaZakA = input("Godzina zakończenia zmiany A (HH:MM): ")
    PrzystanekRozpB = input("Przystanek rozpoczęcia zmiany B: ")
    GodzinaRozpB = input("Godzina rozpoczęcia zmiany B (HH:MM): ")

    # Tworzenie ścieżki do folderu
    sciezka_folder = os.path.join("WYNIKI", "Gotowe_brygady", typ_dnia, brygada)

    # Sprawdzanie, czy folder istnieje, jeśli nie - tworzymy go
    if not os.path.exists(sciezka_folder):
        try:
            os.makedirs(sciezka_folder)
            print(f"Utworzono folder: {sciezka_folder}")
        except Exception as e:
            print(f"Nie udało się utworzyć folderu: {e}")
            return  # Kończymy funkcję, jeśli wystąpił błąd podczas tworzenia folderu

    # Ścieżki do plików
    plik_zakA = os.path.join(sciezka_folder, "ZakonczenieA.txt")
    plik_rozpB = os.path.join(sciezka_folder, "RozpoczecieB.txt")

    # Zawartości plików
    tresc_zakA = f"{PrzystanekZakA}\t{GodzinaZakA}"
    tresc_rozpB = f"{PrzystanekRozpB}\t{GodzinaRozpB}"

    # Tworzenie i zapisywanie plików
    try:
        # Plik ZakonczenieA.txt
        with open(plik_zakA, "w", encoding='utf-8') as plik:
            plik.write(tresc_zakA)
        print(f"Plik zapisano w {plik_zakA}")

        # Plik RozpoczecieB.txt
        with open(plik_rozpB, "w", encoding='utf-8') as plik:
            plik.write(tresc_rozpB)
        print(f"Plik zapisano w {plik_rozpB}")

    except Exception as e:
        print(f"Wystąpił błąd podczas zapisywania plików: {e}")
 
      
        
  
  
  
  
def zmien_typ_w_pliku():
    clear_screen()
    # Pobranie danych od użytkownika
    wartosc_dnia = input("Podaj wartość dnia: ").strip()
    numer_brygady = input("Podaj numer brygady: ").strip()
    nowy_typ = input("Podaj nowy typ (B/JZ): ").strip()

    # Ścieżka do pliku Brygady_BIS.txt
    folder_path = f"WYNIKI/Gotowe_brygady/{wartosc_dnia}"
    plik_bis_path = os.path.join(folder_path, "Brygady_BIS.txt")

    # Sprawdzenie, czy plik istnieje
    if not os.path.exists(plik_bis_path):
        print(f"Plik nie istnieje: {plik_bis_path}")
        return

    try:
        # Wczytaj zawartość pliku
        with open(plik_bis_path, mode='r', encoding='utf-8') as file:
            linie = file.readlines()

        # Sprawdzenie, czy numer brygady istnieje w pliku
        znaleziono = False
        for i in range(2, len(linie)):  # Pomijamy pierwsze dwie linie
            if linie[i].startswith(f"{numer_brygady}\t"):
                znaleziono = True
                break

        # Jeśli numer brygady zawiera "/" i nie został znaleziony, zastąp go
        if "/" in numer_brygady and not znaleziono:
            numer_brygady = zastap_numer_brygady(numer_brygady)

        # Przetwórz plik, aby znaleźć i podmienić odpowiedni wiersz
        znaleziono = False
        for i in range(2, len(linie)):  # Pomijamy pierwsze dwie linie
            if linie[i].startswith(f"{numer_brygady}\t"):
                # Znaleziono odpowiednią linię – podmień typ
                stare_dane = linie[i].strip().split('\t')
                if len(stare_dane) == 2:
                    linie[i] = f"{numer_brygady}\t{nowy_typ}\n"
                    znaleziono = True
                    print(f"Zmieniono typ dla numeru brygady {numer_brygady}: {stare_dane[1]} -> {nowy_typ}")
                break

        if not znaleziono:
            print(f"Nie znaleziono numeru brygady {numer_brygady} w pliku.")

        # Zapisz zmodyfikowane dane do pliku
        with open(plik_bis_path, mode='w', encoding='utf-8') as file:
            file.writelines(linie)

    except Exception as e:
        print(f"Wystąpił błąd podczas przetwarzania pliku: {e}")  





        
def zastap_numer_brygady(numer_brygady):
    clear_screen()
    """
    Funkcja zastępuje numer_brygady na wartość nowa_wartosc z pliku 'Numeracja brygad.txt'.
    """
    plik_numeracja_path = "WYNIKI/Numeracja brygad.txt"

    # Sprawdzenie, czy plik istnieje
    if not os.path.exists(plik_numeracja_path):
        print(f"Plik nie istnieje: {plik_numeracja_path}")
        return numer_brygady

    try:
        # Wczytaj zawartość pliku
        with open(plik_numeracja_path, mode='r', encoding='utf-8') as file:
            linie = file.readlines()

        # Wyszukanie numer_brygady i zastąpienie nową wartością
        for linia in linie:
            if "\t" in linia:
                nowa_wartosc, zapisany_numer = linia.strip().split('\t', maxsplit=1)
                if zapisany_numer == numer_brygady:
                    print(f"Zastąpiono numer brygady '{numer_brygady}' na '{nowa_wartosc}'.")
                    return nowa_wartosc

        print(f"Nie znaleziono numeru brygady '{numer_brygady}' w pliku 'Numeracja brygad.txt'.")
        return numer_brygady  # Zwrot oryginalnego numeru, jeśli nie znaleziono zamiennika

    except Exception as e:
        print(f"Wystąpił błąd podczas przetwarzania pliku 'Numeracja brygad.txt': {e}")
        return numer_brygady



      
def ModyfikujBrygadyBIS():
    clear_screen()
    try:
        zmien_typ_w_pliku()
        clear_screen()        
    except Exception as e:
        print(f"Wystąpił błąd w opcji 6: {e}")

  



    
    
    
def ChangeToken():  
    clear_screen()

    try:
        # Pobranie tokenu dwukrotnie od użytkownika
        token1 = input("Wprowadź nowy token: ")
        token2 = input("Potwierdź nowy token: ")

        # Sprawdzenie, czy tokeny są zgodne
        if token1 != token2:
            print("BŁĄD: Wprowadzone tokeny są różne")
            time.sleep(2)
            clear_screen()
            return

        # Ścieżka do pliku Token.txt
        file_path = os.path.join("..", "public", "Token.txt")

        # Utworzenie folderu ../public, jeśli nie istnieje
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Nadpisanie pliku Token.txt
        with open(file_path, "w") as file:
            file.write(token1)

        print("Token został zmieniony.")
        time.sleep(2)
        clear_screen()
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        time.sleep(2)
        clear_screen()
  
  
    
def ShowToken():  
    try:
        with open('../public/Token.txt', 'r') as file:
            content = file.read()
            print("Token administratora: ", content)
    except FileNotFoundError:
        print("Plik nie został znaleziony. Upewnij się, że ścieżka jest poprawna.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")


    

def NewsList():
    # Ścieżka do folderu z newsami
    folder_path = '../public/News'
    
    # Upewniamy się, że folder istnieje
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} nie istnieje.")
        return

    # Pobieranie listy plików w folderze
    files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]

    # Sprawdzanie, czy są pliki tekstowe
    if not files:
        print("Brak plików tekstowych w folderze News.")
        return

    # Wyświetlanie listy plików
    print("Lista plików tekstowych w folderze News:")
    for index, file in enumerate(sorted(files), start=1):
        print(f"{index}. {file}")
    
    
def AddNews():
    clear_screen()
    # Pobranie danych od użytkownika
    data = input("Data: ")
    godzina = input("Godzina: ")
    tytul = input("Tytuł: ")
    tresc = input("Treść: ")
    obrazek = input("Załącznik: ")

    # Ścieżka do folderu, w którym ma zostać zapisany plik
    folder_path = '../public/News'
    
    # Upewnijmy się, że folder istnieje
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Ścieżka do pliku tekstowego, który będzie zawierał news
    file_path = os.path.join(folder_path, f'{data}.txt')

    # Tworzenie zawartości pliku
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f"{tytul}\n")
        file.write(f"{data}; {godzina}\n")
        file.write("\n")  # Pusta linijka
        file.write(f"{tresc}\n")
        if obrazek:  # Jeżeli obrazek jest podany
            file.write(f"{obrazek}\n")
    
    print(f"Dodano Wiadomość.")    
    time.sleep(1)
    clear_screen()
  
  
def EditNews():
    # Ścieżka do folderu z newsami
    folder_path = '../public/News'
    
    # Upewniamy się, że folder istnieje
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} nie istnieje.")
        return
    
    # Pobranie listy plików w folderze
    files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]
    if not files:
        print("Brak plików w folderze News.")
        return


    
    print("0. Anuluj")

    # Wybór pliku do edycji
    try:
        choice = int(input("\nWybierz numer pliku do edycji: "))
        if choice == 0:
            print("Anulowano edycję.")
            return
        if choice < 1 or choice > len(files):
            print("Nieprawidłowy wybór.")
            return
        file_path = os.path.join(folder_path, sorted(files)[choice - 1])
    except ValueError:
        print("Nieprawidłowy numer. Proszę wprowadzić liczbę.")
        return

    # Wczytanie zawartości pliku
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Wyciągamy poszczególne sekcje
    tytul = lines[0].strip() if len(lines) > 0 else ""
    data_dodania = lines[1].strip() if len(lines) > 1 else ""
    tresc = lines[3].strip() if len(lines) > 3 else ""
    obrazek = lines[4].strip() if len(lines) > 4 else ""

    # Wyświetlenie obecnych wartości
    clear_screen()
    print(f"Tytuł: {tytul}")
    print(f"Data dodania: {data_dodania}")
    print(f"Treść: {tresc}")
    print(f"Obrazek: {obrazek if obrazek else 'N/A'}")
    print("\n")
    
    # Wybór, co zmodyfikować
    print("1 - Data dodania")    
    print("2 - Tytuł")
    print("3 - Treść")
    print("4 - Obrazek")
    print("0 - Anuluj")

    choice = input("Wybierz opcję: ")

    if choice == "2":
        tytul = input("Wpisz nowy tytuł: ")
    elif choice == "3":
        tresc = input("Wpisz nową treść: ")
    elif choice == "4":
        obrazek = input("Wpisz nową nazwę obrazka (lub pozostaw puste): ")
    elif choice == "1":
        new_data = input("Wpisz nową datę (np. 2024-12-29): ")
        new_file_path = os.path.join(folder_path, f'{new_data}.txt')
        os.rename(file_path, new_file_path)
        file_path = new_file_path
        data_dodania = f"Dodano {new_data}"
    elif choice == "0":
        clear_screen()
        print("Anulowano modyfikację.")
        time.sleep(1)
        clear_screen()
        return
    else:
        clear_screen()
        print("Nieprawidłowy wybór.")
        time.sleep(1)
        clear_screen()
        return

    # Aktualizacja pliku z newsem
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f"{tytul}\n")
        file.write(f"{data_dodania}\n")
        file.write("\n")  # Pusta linia
        file.write(f"{tresc}\n")
        if obrazek:
            file.write(f"{obrazek}\n")

    print(f"Plik został zaktualizowany: {file_path}")  
    time.sleep(1)
    clear_screen()
  
def DeleteNews():
    # Ścieżka do folderu z newsami
    folder_path = '../public/News'

    # Upewniamy się, że folder istnieje
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} nie istnieje.")
        return

    # Pobieranie listy plików w folderze
    files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]

    # Sprawdzanie, czy są pliki tekstowe
    if not files:
        print("Brak plików tekstowych w folderze News.")
        return

    # Wyświetlanie listy plików
    print("Lista plików tekstowych w folderze News:")
    for index, file in enumerate(sorted(files), start=1):
        print(f"{index}. {file}")

    # Wybór pliku do usunięcia
    try:
        print("0. Wyjdź")
        choice = int(input("\nWybierz numer pliku do usunięcia: "))
        if choice == 0:
            print("Anulowano usuwanie.")
            time.sleep(2)
            clear_screen()
        if choice < 1 or choice > len(files):
            print("Nieprawidłowy wybór.")
            clear_screen()
            DeleteNews()

        # Wybrany plik do usunięcia
        file_to_delete = os.path.join(folder_path, sorted(files)[choice - 1])
        print(f"Wybrany plik: {sorted(files)[choice - 1]}")

        # Potwierdzenie usunięcia
        confirm = input("Czy na pewno chcesz usunąć ten plik? (tak/nie): ").strip().lower()
        if confirm == "tak":
            os.remove(file_to_delete)
            print(f"Plik {sorted(files)[choice - 1]} został usunięty.")
            time.sleep(2)
            clear_screen()
        else:
            clear_screen()            
            print("Anulowano usuwanie.")
            time.sleep(2)
            clear_screen()
    except ValueError:
        print("Nieprawidłowy numer. Proszę wprowadzić liczbę.")
  
  
def NewsToArchy():
    # Ścieżka do folderu z newsami
    folder_path = '../public/News'
    archive_path = '../public/News/Archiwum'

    # Upewniamy się, że folder istnieje
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} nie istnieje.")
        return

    # Upewniamy się, że podfolder Archiwum istnieje
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)

    # Pobieranie listy plików w folderze
    files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]

    # Sprawdzanie, czy są pliki tekstowe
    if not files:
        print("Brak plików tekstowych w folderze News.")
        return

    # Wyświetlanie listy plików
    print("Lista plików tekstowych w folderze News:")
    for index, file in enumerate(sorted(files), start=1):
        print(f"{index}. {file}")

    # Wybór pliku do przeniesienia
    try:
        print("0. Wyjdź")
        choice = int(input("\nWybierz numer pliku do przeniesienia do Archiwum: "))
        if choice == 0:
            clean_screen()
            print("Anulowano przenoszenie.")
            time.sleep(1)
            clean_screen()
            return
        if choice < 1 or choice > len(files):
            print("Nieprawidłowy wybór.")
            return

        # Wybrany plik do przeniesienia
        file_to_move = os.path.join(folder_path, sorted(files)[choice - 1])
        clear_screen()
        print(f"Wybrany plik: {sorted(files)[choice - 1]}")

        # Potwierdzenie przeniesienia
        confirm = input("Czy na pewno chcesz przenieść ten plik do Archiwum? (tak/nie): ").strip().lower()
        if confirm == "tak":
            shutil.move(file_to_move, archive_path)
            print(f"Plik {sorted(files)[choice - 1]} został przeniesiony do Archiwum.")
            time.sleep(2)
            clean_screen()
        else:
            print("Anulowano przenoszenie.")
            time.sleep(2)
    except ValueError:
        print("Nieprawidłowy numer. Proszę wprowadzić liczbę.")    
  


def CallendarCreator():
    # Funkcja do generowania rozkładu
    def generate_schedule_for_date(date):
        if date.weekday() == 5:  # Sobota
            return "Rozkład Sobotni"
        elif date.weekday() == 6:  # Niedziela
            return "Rozkład Niedzielny"
        else:
            return "Rozkład Szkolny"

    # Funkcja do generowania kalendarza
    def generate_calendar(start_date, end_date, output_file, special_dates_file):
        try:
            # Tworzenie folderu, jeśli nie istnieje
            folder = os.path.dirname(output_file)
            if not os.path.exists(folder):
                os.makedirs(folder)

            # Wczytanie specjalnych dat (DD.MM format)
            special_dates = {}
            if os.path.exists(special_dates_file):
                with open(special_dates_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            # Przechowujemy specjalne daty w formacie DD.MM -> opis
                            special_dates[parts[0]] = "\t".join(parts[1:])

            # Otwieramy plik do zapisu
            current_date = start_date
            lines_to_write = []
            while current_date <= end_date:
                # Formatowanie daty na DD.MM.YYYY
                formatted_date = current_date.strftime("%d.%m.%Y")
                # Sprawdzamy datę w formacie DD.MM, aby porównać ją z plikiem specjalnych dat
                short_date = current_date.strftime("%d.%m")
                # Generowanie rozkładu dla danej daty
                schedule_type = generate_schedule_for_date(current_date)
                
                # Sprawdzanie, czy data w formacie DD.MM znajduje się w specjalnych datach
                if short_date in special_dates:
                    lines_to_write.append(f"{formatted_date}\t{special_dates[short_date]}\n")
                else:
                    # Zapisanie daty i rozkładu do pliku
                    lines_to_write.append(f"{formatted_date}\t{schedule_type}\n")
                
                # Przechodzimy do następnego dnia
                current_date += datetime.timedelta(days=1)

            # Zapisanie danych do pliku
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(lines_to_write)

        except Exception as e:
            print(f"Błąd podczas generowania kalendarza: {e}")

    # Ustawienia - data początkowa i końcowa (np. cały rok 2025)
    start_date = datetime.date(2025, 1, 1)
    end_date = datetime.date(2025, 12, 31)
    
    # Ścieżki do plików
    output_file = "../public/Brygady/Callendar.txt"
    special_dates_file = "../public/Brygady/Callendar_special_dates.txt"

    # Generowanie kalendarza
    generate_calendar(start_date, end_date, output_file, special_dates_file)

    print(f"Plik {output_file} został wygenerowany.")

      
    
    
def help():
    clear_screen()
    print("Witaj w pomocy technicznej dotyczącej edycji folderów z plikami brygad na stronę www.brygadowki46.vercel.app")  
    print("Dostęp do tych plików jest wzbroniony dla osób trzecich nieporzadanych, proszę uszanuj to.")  
    print("Poniżej znajdziesz aktualne oznaczenia która zakładka co robi.")
    print("")
    print("===========================================")
    print("Opcja 1: Wczytaj brygady")
    print("===========================================")
    print("Funkcja wczytaj brygady przetwarza pliki udostepnione przez ZTM a następnie tworzy folder WYNIKI, w nim poszczególne podfoldery z wartościami service_ID, następnie tworzy podfolder Gotowe_brygady, który zawiera posortowane brygady.")
    time.sleep(10)
    clear_screen()
      
      
      
      
def PodmianaList():
    # Ścieżka głównego folderu
    base_path = "WYNIKI/Gotowe_brygady"

    # Iteracja po folderach "1", "2", "3", "4"
    for folder in ["1", "2", "3", "4"]:
        # Zamiana "_" na "/"
        formatted_folder = folder.replace("_", "/")
        folder_path = os.path.join(base_path, formatted_folder)
        podmiana_list_file = os.path.join(folder_path, "Podmiana_list.txt")

        # Tymczasowy bufor na dane do sortowania
        data_to_sort = []

        # Iteracja po podfolderach w folderze
        for subfolder in os.listdir(folder_path):
            subfolder_path = os.path.join(folder_path, subfolder)

            if os.path.isdir(subfolder_path):
                podmiana_file_path = os.path.join(subfolder_path, "podmiana.txt")

                # Sprawdzenie, czy plik podmiana.txt istnieje
                if os.path.exists(podmiana_file_path):
                    with open(podmiana_file_path, "r", encoding="utf-8") as podmiana_file:
                        for line in podmiana_file:
                            line = line.strip()
                            if line:
                                # Dodaj dane do bufora w formacie: (Nazwa_folderu, Przystanek, Godzina_Podmiany)
                                # Zamiana "_" na "/" podczas zapisu tylko w pliku
                                data_to_sort.append((subfolder, *line.split("\t")))

        # Sortowanie danych według godziny (drugi element tuple)
        data_to_sort.sort(key=lambda x: x[2])

        # Zapis posortowanych danych do pliku
        with open(podmiana_list_file, "w", encoding="utf-8") as output_file:
            for entry in data_to_sort:
                # Zamiana "_" na "/" w zapisie do pliku
                output_file.write(f"{entry[0].replace('_', '/')}\t{entry[1]}\t{entry[2]}\n")

    print("Operacja zakończona.")

    
def PodmianaBAZA():    

    def read_files_and_create_list(directory):
        # Lista do zapisania wyników
        result_list = []

        # Ścieżka do folderu "WYNIKI/Gotowe_brygady/1"
        path = os.path.join("WYNIKI", "Gotowe_brygady", directory)
        
        # Przechodzimy przez wszystkie foldery w danym katalogu
        for subfolder in os.listdir(path):
            subfolder_path = os.path.join(path, subfolder)
            
            zakonczenie_file = os.path.join(subfolder_path, "ZakonczenieA.txt")
            rozpoczecie_file = os.path.join(subfolder_path, "RozpoczecieB.txt")
            
            if os.path.isfile(zakonczenie_file) and os.path.isfile(rozpoczecie_file):
                # Odczytujemy pliki
                with open(zakonczenie_file, 'r') as f:
                    zakonczenie = f.readline().strip()
                with open(rozpoczecie_file, 'r') as f:
                    rozpoczecie = f.readline().strip()
                
                # Zamiana "_" na "/" w nazwie subfoldera
                subfolder = subfolder.replace("_", "/")
                
                # Tworzymy linie do listy
                result_line = f"{subfolder}\t{zakonczenie}\t{rozpoczecie}"
                result_list.append(result_line)
        
        return result_list

    def sort_and_write_to_file(directory, lines):
        # Sortujemy linie po godzinie (ostatnia kolumna)
        sorted_lines = sorted(lines, key=lambda x: x.split('\t')[3])
        
        # Zapisujemy do pliku PodmianaBAZA_list.txt
        path = os.path.join("WYNIKI", "Gotowe_brygady", directory)
        output_path = os.path.join(path, "PodmianaBAZA_list.txt")
        with open(output_path, 'w') as output_file:
            for line in sorted_lines:
                output_file.write(line + "\n")

    # Lista folderów "1", "2", "3", "4"
    folders = ["1", "2", "3", "4"]

    for folder in folders:
        lines = read_files_and_create_list(folder)
        sort_and_write_to_file(folder, lines)

    print("Pliki zostały pomyślnie zapisane i posortowane!")




    
def RezerwaList():
    # Ścieżka głównego folderu
    base_path = "WYNIKI/Gotowe_brygady"

    # Iteracja po folderach "1", "2", "3", "4"
    for folder in ["1", "2", "3", "4"]:
        folder_path = os.path.join(base_path, folder)
        rezerwa_list_file = os.path.join(folder_path, "Rezerwa_list.txt")

        # Tymczasowy bufor na dane do sortowania
        data_to_sort = []

        # Iteracja po podfolderach w folderze
        for subfolder in os.listdir(folder_path):
            subfolder_path = os.path.join(folder_path, subfolder)

            if os.path.isdir(subfolder_path):
                rezerwa_file_path = os.path.join(subfolder_path, "rezerwa.txt")

                # Sprawdzenie, czy plik Rezerwa.txt istnieje
                if os.path.exists(rezerwa_file_path):
                    with open(rezerwa_file_path, "r", encoding="utf-8") as rezerwa_file:
                        # Iteracja po liniach w pliku
                        for line in rezerwa_file:
                            line = line.strip()
                            # Pomijamy linie nagłówka oraz separatora
                            if line.startswith("[Rez]") or line.startswith("route_id") or line.startswith("-"):
                                continue

                            # Rozdzielamy dane w linii
                            fields = line.split("\t")
                            if len(fields) >= 5:
                                arrival_time = fields[3][:5]  # Wyciągamy tylko HH:MM
                                departure_time = fields[4][:5]  # Wyciągamy tylko HH:MM
                                # Dodajemy dane do bufora
                                data_to_sort.append((subfolder, arrival_time, departure_time))

        # Sortowanie danych według czasu przyjazdu (drugi element tuple)
        data_to_sort.sort(key=lambda x: x[1])

        # Zapis posortowanych danych do pliku
        with open(rezerwa_list_file, "w", encoding="utf-8") as output_file:
            for entry in data_to_sort:
                output_file.write(f"{entry[0].replace('_', '/')}\t{entry[1]}\t{entry[2]}\n")

    print("Operacja zakończona.")

import os
from datetime import datetime, timedelta

def calculate_time_difference(start_time, end_time):
    fmt = "%H:%M"
    try:
        start = datetime.strptime(start_time, fmt)

        end_parts = end_time.split(':')
        if int(end_parts[0]) >= 24:
            end_time = f"{(int(end_parts[0]) - 24):02}:{end_parts[1]}"  # Zapewnia poprawny format "01:30"

        end = datetime.strptime(end_time, fmt)

        if end < start:
            end += timedelta(days=1)

        difference = (end - start).total_seconds() / 3600
        return difference
    except ValueError:
        print(f"BŁĄD: Nieprawidłowy format godziny: {start_time}, {end_time}")
        return None


def ZaproponujBrygadyBIS():
    base_paths = [
        "WYNIKI/Gotowe_brygady/1",
        "WYNIKI/Gotowe_brygady/2",
        "WYNIKI/Gotowe_brygady/3",
        "WYNIKI/Gotowe_brygady/4"
    ]

    for base_path in base_paths:
        if not os.path.exists(base_path):
            print(f"BŁĄD: Folder {base_path} nie istnieje.")
            continue

        output_file = os.path.join(base_path, "Brygady_BIS.txt")
        print(f"Tworzenie pliku: {output_file}")

        with open(output_file, "w", encoding="utf-8") as out_file:
            found_any = False
            out_file.write(" Numer\tB/JZ \n")
            out_file.write(" ------------- \n")

            print(f"Sprawdzanie folderów w: {base_path}")
            for folder in os.listdir(base_path):
                folder_path = os.path.join(base_path, folder)
                if os.path.isdir(folder_path):
                    folder_formatted = folder.replace("_", "/")
                    print(f"📂 Przetwarzanie folderu: {folder_formatted}")

                    start_file = os.path.join(folder_path, "Godz_Rozp.txt")
                    end_file = os.path.join(folder_path, "Godz_Zak.txt")

                    if os.path.exists(start_file) and os.path.exists(end_file):
                        print(f"✅ Pliki znalezione w {folder_formatted}")

                        with open(start_file, "r", encoding="utf-8") as sf, open(end_file, "r", encoding="utf-8") as ef:
                            start_time = sf.read().strip()
                            end_time = ef.read().strip()

                            time_diff = calculate_time_difference(start_time, end_time)
                            if time_diff is None:
                                continue

                            found_any = True
                            if time_diff < 10:
                                if int(start_time.split(":")[0]) >= 20 and time_diff < 10:
                                    out_file.write(f"{folder_formatted}\tJZN\n")
                                else:
                                    out_file.write(f"{folder_formatted}\tJZ\n")
                            elif time_diff > 10:
                                bis_file_path = os.path.join(folder_path, "CzyBIS.txt")
                                if os.path.exists(bis_file_path):
                                    with open(bis_file_path, "r", encoding="utf-8") as bis_file:
                                        if "Tak" in bis_file.read().strip():
                                            out_file.write(f"{folder_formatted}\tB\n")
                                        
                                else:
                                    out_file.write(f"{folder_formatted}\tX\n")
                    else:
                        print(f"⚠️ Brak wymaganych plików w {folder_formatted}!")

            if not found_any:
                print("❌ Nie znaleziono żadnych folderów z poprawnymi danymi.")

    print("✅ Zakończono działanie skryptu.")




    
    
    
    
    
    
    
    



import os
from datetime import datetime

def CzyBIS():
    # Lista folderów, które chcemy przetworzyć
    folder_paths = ['WYNIKI/Gotowe_brygady/1', 'WYNIKI/Gotowe_brygady/2', 'WYNIKI/Gotowe_brygady/3', 'WYNIKI/Gotowe_brygady/4']
    
    for folder_path in folder_paths:
        # Sprawdzamy, czy folder istnieje
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Przechodzimy przez wszystkie podfoldery w folderze
            for subfolder in os.listdir(folder_path):
                subfolder_path = os.path.join(folder_path, subfolder)

                try:
                    # Sprawdzamy, czy to folder
                    if os.path.isdir(subfolder_path):
                        print(f'Przechodzę do folderu: {subfolder_path}')
                        
                        # Ścieżka do pliku CzyBIS.txt w danym podfolderze
                        file_path_cybis = os.path.join(subfolder_path, 'CzyBIS-Analiza.txt')
                        
                        # Ścieżka do pliku GOTOWE.txt w danym podfolderze
                        file_path_gotowe = os.path.join(subfolder_path, 'GOTOWE.txt')

                        # Tworzymy plik CzyBIS.txt
                        with open(file_path_cybis, 'w') as file_cybis:

                            # Sprawdzamy, czy plik GOTOWE.txt istnieje
                            if os.path.exists(file_path_gotowe):
                                print(f'Plik GOTOWE.txt istnieje w folderze {subfolder_path}')
                                try:
                                    # Próba otwarcia pliku z określonym kodowaniem (np. 'utf-8', 'latin-1')
                                    with open(file_path_gotowe, 'r', encoding='latin-1') as file_gotowe:
                                        # Pomijamy pierwsze 2 linijki
                                        lines = file_gotowe.readlines()[2:]

                                        # Zmienna do przechowywania wartości departure_time
                                        kurs_times = []
                                        previous_max_time = None  # Zmienna do przechowywania poprzedniego maksymalnego czasu

                                        # Przechodzimy przez wszystkie linie w pliku GOTOWE.txt
                                        for line in lines:
                                            # Sprawdzamy, czy linia jest pusta (oznacza koniec kursu)
                                            if line.strip() == '':
                                                # Jeśli są czasy, obliczamy min i max dla kursu
                                                if kurs_times:
                                                    min_time = min(kurs_times)
                                                    max_time = max(kurs_times)

                                                    # Zapisujemy do pliku
                                                    file_cybis.write(f'Najmniejszy departure_time: {min_time}\n')
                                                    file_cybis.write(f'Największy departure_time: {max_time}\n')

                                                    # Obliczamy przerwę między kursami
                                                    if previous_max_time:
                                                        time_format = "%H:%M:%S"
                                                        # Obliczanie różnicy między ostatnim czasem poprzedniego kursu a pierwszym czasem bieżącego kursu
                                                        min_time_dt = datetime.strptime(min_time, time_format)
                                                        previous_max_time_dt = datetime.strptime(previous_max_time, time_format)

                                                        # Obliczanie różnicy w minutach
                                                        break_time = (min_time_dt - previous_max_time_dt).total_seconds() / 60
                                                        if break_time < 0:  # Jeśli różnica jest ujemna, to znaczy, że coś poszło nie tak
                                                            break_time = 0
                                                        file_cybis.write(f'Przerwa kierowcy: {break_time:.2f} minut\n')
                                                        if break_time > 200:
                                                            file_cybis.write(f'PRZERWA BISOWA\n')
                                                            # Tworzymy plik CzyBIS.txt, jeśli warunek jest spełniony
                                                            cybis_file_path = os.path.join(subfolder_path, 'CzyBIS.txt')
                                                            with open(cybis_file_path, 'w') as cybis_file:
                                                                cybis_file.write("Tak")
                                                    

                                                    # Aktualizujemy poprzedni maksymalny czas
                                                    previous_max_time = max_time

                                                    file_cybis.write('\n')

                                                # Resetujemy listę czasów dla nowego kursu
                                                kurs_times = []
                                            else:
                                                # Dzielimy linię na kolumny (oddzielone tabulatorem)
                                                columns = line.split('\t')

                                                # Wartość route_id (1-sza kolumna) traktujemy jako identyfikator kursu
                                                if len(columns) > 4:
                                                    # Dodajemy departure_time do listy czasów dla aktualnego kursu
                                                    departure_time = columns[4]

                                                    # Zapisujemy godzinę dokładnie tak, jak jest w pliku (bez konwersji)
                                                    kurs_times.append(departure_time)

                                        # Po zakończeniu pętli, zapisujemy ostatni kurs
                                        if kurs_times:
                                            min_time = min(kurs_times)
                                            max_time = max(kurs_times)

                                            # Zapisujemy do pliku
                                            file_cybis.write(f'Najmniejszy departure_time: {min_time}\n')
                                            file_cybis.write(f'Największy departure_time: {max_time}\n')

                                except UnicodeDecodeError as e:
                                    print(f'Błąd przy odczycie pliku GOTOWE.txt w folderze {subfolder_path}: {e}')
                                    file_cybis.write(f'Błąd przy odczycie pliku GOTOWE.txt w folderze {subfolder_path}: {e}\n')
                            else:
                                print(f'Brak pliku GOTOWE.txt w folderze {subfolder_path}')
                                file_cybis.write(f'Brak pliku GOTOWE.txt w folderze {subfolder_path}\n')

                        print(f'Plik CzyBIS.txt został utworzony w folderze: {subfolder_path}')
                    else:
                        print(f'{subfolder_path} nie jest folderem, pomijam.')
                except Exception as e:
                    print(f'Błąd w folderze {subfolder_path}: {e}')
        else:
            print(f'Folder {folder_path} nie istnieje lub nie jest folderem.')

    
def WczytajNumeracje():
    clear_screen()
    input(f'Prawidłowa nazwa pliku xml:  ServiceCodes.xml\n Aby kontynuować kliknij ENTER')
    # Definiowanie ścieżki do pliku XML
    sciezka_pliku = 'ServiceCodes.xml'  # Poprawna nazwa zmiennej

    # Wczytanie zawartości pliku XML
    with open(sciezka_pliku, 'r', encoding='utf-8-sig') as file:
        xml_content = file.read()

    # Parsowanie zawartości XML
    korzen = ET.fromstring(xml_content)

    # Definiowanie przestrzeni nazw
    namespaces = {'ns': 'http://www.transxchange.org.uk/'}

    # Otwieramy plik tekstowy do zapisu
    with open('WYNIKI/Numeracja brygad.txt', 'w', encoding='utf-8') as f:
        # Iteracja przez wszystkie elementy Service
        for service in korzen.findall('.//ns:Service', namespaces):
            # Szukanie ServiceCode i PrivateCode
            service_code = service.find('ns:ServiceCode', namespaces).text if service.find('ns:ServiceCode', namespaces) is not None else ''
            private_code = service.find('ns:PrivateCode', namespaces).text if service.find('ns:PrivateCode', namespaces) is not None else ''
            
            # Zapisujemy do pliku
            f.write(f"{service_code}\t{private_code}\n")
    
        

        

def Pozmieniaj():
    plik = "trips.txt"
    
    while True:
        numer_brygady = input("Podaj numer brygady (lub 'q' aby zakończyć): ")
        if numer_brygady.lower() == 'q':
            break
        
        nowy_numer = input("Podaj numer do zastąpienia: ")
        
        with open(plik, "r", encoding="utf-8") as f:
            linie = f.readlines()
        
        with open(plik, "w", encoding="utf-8") as f:
            for linia in linie:
                pola = linia.strip().split(",")
                
                if pola[0] == numer_brygady:
                    print(f"Zmieniono: {linia.strip()} -> {numer_brygady},{nowy_numer},{','.join(pola[2:])}")
                    pola[1] = nowy_numer
                
                f.write(",".join(pola) + "\n")
    

def SprawdzPozmieniaj():
    plik = "trips.txt"
    
    with open(plik, "r", encoding="utf-8") as f:
        linie = f.readlines()
    
    print("Linijki, w których druga wartość jest różna od 1, 2, 3 oraz 4:")
    for linia in linie:
        pola = linia.strip().split(",")
        if pola[1] not in {"1", "2", "3", "4"}:
            print(linia.strip())    
    
    
    
    
      
      
    
    
    
    
    
    
    
    
    
    
    
    










import os
import re
from datetime import datetime, timedelta

def find_stop_name_for_end(end_time, output_dir):
    """ Funkcja do szukania stop_name w pliku 'PierwotneGotowe.txt' w danym folderze """
    pierwotne_file_path = os.path.join(output_dir, "PierwotneGotowe.txt")
    
    if not os.path.exists(pierwotne_file_path):
        print(f"Plik {pierwotne_file_path} nie istnieje.")
        return None
    
    with open(pierwotne_file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    
    lines = lines[2:]

    for line in lines:
        if line.strip() == "":
            continue
        
        match = re.match(r"(\S+)\t(\S+)\t(\S+)\t(\S+:\S+:\S+)\t(\S+:\S+:\S+)\t(.*)\t(.*)", line)
        if match:
            _, _, _, arrival_time, _, _, stop_name = match.groups()
            
            end_time_without_seconds = end_time.strip()[:5]  # HH:MM
            arrival_time_without_seconds = arrival_time[:5]  # HH:MM
            
            if end_time_without_seconds == arrival_time_without_seconds:
                return stop_name
    
    print(f"Nie znaleziono stop_name dla godziny: {end_time}")
    return None

def subtract_one_minute(time_str):
    time_obj = datetime.strptime(time_str, "%H:%M")
    new_time_obj = time_obj - timedelta(minutes=1)
    return new_time_obj.strftime("%H:%M")

def time_difference_in_hours(start_time, end_time):
    start_obj = datetime.strptime(start_time, "%H:%M")
    end_obj = datetime.strptime(end_time, "%H:%M")
    difference = end_obj - start_obj
    return difference.total_seconds() / 3600

import os
import re
import subprocess
import time

def UtworzGodzPodmiany():
    for folder in ["1", "2", "3", "4"]:
        input_path = f"WYNIKI/Gotowe_brygady/{folder}/PodmianyStronaKierowcow.txt"
        print(f"Sprawdzanie pliku: {input_path}")
        
        if not os.path.exists(input_path):
            wyborr = input(f"Plik {input_path} nie istnieje. Czy stworzyć plik? (tak/nie): ")
            if wyborr.lower() == "tak":
                os.makedirs(os.path.dirname(input_path), exist_ok=True)
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write("")  # pusty plik

                print("Otwieranie pliku w edytorze tekstowym. Wklej dane i zapisz plik, potem zamknij edytor.")
                if os.name == 'nt':  # Windows
                    subprocess.Popen(['notepad.exe', input_path])
                else:  # Unix-like
                    subprocess.call(['xdg-open', input_path])

                input("Naciśnij Enter po zamknięciu edytora, aby kontynuować...")
            else:
                print(f"Pomijanie folderu {folder}, ponieważ plik nie został utworzony.")
                continue

        with open(input_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        print(f"Wczytano {len(lines)} linijek z pliku w folderze {folder}.")

        for i, line in enumerate(lines):
            print(f"Przetwarzanie linii: {line.strip()}")
            match = re.match(r"(\S+)\t(\d{1,2}:\d{2}) - (\d{1,2}:\d{2})", line)
            if match:
                sluzba, start, end = match.groups()
                print(f"Rozpoznana służba: {sluzba}, Start: {start}, Koniec: {end}")
                
                if sluzba.endswith("B") or not sluzba.endswith("A"):
                    print(f"Pominięto służbę: {sluzba}")
                    continue

                time_diff = time_difference_in_hours(start, end)
                if time_diff < 6:
                    print(f"Różnica godzin dla służby {sluzba} jest mniejsza niż 6 godziny ({time_diff:.2f} godz.). Pomijam tę służbę.")
                    continue
                
                output_dir = f"WYNIKI/Gotowe_brygady/{folder}/{sluzba[:-1].replace('/', '_')}"
                os.makedirs(output_dir, exist_ok=True)
                
                if i + 1 < len(lines):
                    next_match = re.match(r"(\S+)\t(\d{1,2}:\d{2}) - (\d{1,2}:\d{2})", lines[i + 1])
                    if next_match:
                        next_start = next_match.group(2)
                        if end != next_start:
                            print(f"Koniec ({end}) nie pasuje do początku następnej służby ({next_start}). Tworzenie plików informacyjnych.")
                            with open(os.path.join(output_dir, "zakonczenieA.txt"), "w", encoding="utf-8") as file:
                                file.write(f"Lubelska Zajezdnia MPK \t {end}\n")
                            with open(os.path.join(output_dir, "rozpoczecieB.txt"), "w", encoding="utf-8") as file:
                                file.write(f"Lubelska Zajezdnia MPK \t {next_start}\n")
                            continue
                
                original_end = end  
                stop_name = find_stop_name_for_end(end, output_dir)
                liczbaprob = 0
                
                while stop_name is None:
                    liczbaprob += 1
                    print(f"Nie znaleziono stop_name dla godziny: {end}. Próbuję dla godziny wcześniejszej.")
                    end = subtract_one_minute(end)  
                    stop_name = find_stop_name_for_end(end, output_dir)
                    if liczbaprob > 200:
                        break
                
                output_path = os.path.join(output_dir, "podmiana.txt")
                with open(output_path, "w", encoding="utf-8") as out_file:
                    out_file.write(f"{stop_name}\t{original_end}\t{end}\n")
                
                print(f"Utworzono {output_path}")
    
    input("Naciśnij Enter, aby zakończyć...")












import os
import re

def parse_kursy_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    written_files = set()  # Śledzenie plików, które już zostały utworzone

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("Folder:"):
            folder_number = line.split(" ")[1]

            i += 1
            match = re.search(r'\[(.*?)\]', lines[i])
            if match:
                line_number = match.group(1)
            else:
                continue

            while i < len(lines) and not lines[i].startswith("route_id"):
                i += 1

            i += 2  # Pominięcie linii z kreskami
            while i < len(lines) and lines[i].strip():
                parts = lines[i].split("\t")
                if len(parts) >= 6:
                    departure_time = parts[4]
                    route_id = parts[0]
                    stop_name = parts[6].strip().replace("/", "_")

                    if i + 1 < len(lines) and lines[i + 1].strip() == "":
                        break

                    folder_part = file_path.split("/")[2]
                    stop_folder = f"../Przystanki/{folder_part}/{stop_name}"
                    os.makedirs(stop_folder, exist_ok=True)

                    stop_file = os.path.join(stop_folder, f"{line_number}.txt")

                    # Zerowanie pliku przy pierwszym użyciu
                    if stop_file not in written_files:
                        with open(stop_file, "w", encoding="utf-8") as f:
                            pass  # Zeruje plik
                        written_files.add(stop_file)

                    with open(stop_file, "a", encoding="utf-8") as f:
                        f.write(f"{departure_time}\t{folder_number}\t{route_id}\n")

                i += 1
        else:
            i += 1

    
    
    
    
    
    
    
    
    
    
    
    
    


    
    
    
    
    
import xml.etree.ElementTree as ET
import locale    
    
    
def Wczytaj_Przystanki():
    input('Prawidłowa nazwa pliku xml: ServiceCodes.xml\nAby kontynuować kliknij ENTER')

    # Definiowanie ścieżki do pliku XML
    sciezka_pliku = 'ServiceCodes.xml'

    # Wczytanie zawartości pliku XML
    with open(sciezka_pliku, 'r', encoding='utf-8-sig') as file:
        xml_content = file.read()

    # Parsowanie zawartości XML
    korzen = ET.fromstring(xml_content)

    # Definiowanie przestrzeni nazw
    namespaces = {'ns': 'http://www.transxchange.org.uk/'}

    # Ustawienie lokalizacji na polską
    locale.setlocale(locale.LC_COLLATE, 'pl_PL.UTF-8')

    # Listy przechowujące dane przed zapisaniem
    data = []
    stop_names = []
    stop_name_id_pairs = []

    # Iteracja przez wszystkie elementy StopPoint
    for stop_point in korzen.findall('.//ns:StopPoint', namespaces):
        public_code = stop_point.find('.//ns:Extensions/ns:PublicCode', namespaces)
        stop_ID = stop_point.attrib.get('id', '')
        stop_name = stop_point.find('.//ns:Descriptor/ns:CommonName', namespaces)
        on_demand = stop_point.find('.//ns:Extensions/ns:OnDemand', namespaces)
        ticket_zone_ref = stop_point.find('.//ns:Extensions/ns:TicketZones/ns:TicketZoneRef', namespaces)
        latitude = stop_point.find('.//ns:Place/ns:Location/ns:Latitude', namespaces)
        longitude = stop_point.find('.//ns:Place/ns:Location/ns:Longitude', namespaces)
        adm_city_element = stop_point.find('.//ns:Extensions/ns:AdministrativeAreaRefs/ns:AdministrativeAreaRef', namespaces)

        public_code = public_code.text if public_code is not None else ''
        stop_name = stop_name.text if stop_name is not None else ''
        on_demand = on_demand.text if on_demand is not None else ''
        ticket_zone_ref = ticket_zone_ref.text if ticket_zone_ref is not None else ''
        latitude = latitude.text if latitude is not None else ''
        longitude = longitude.text if longitude is not None else ''
        AdmCity = adm_city_element.text if adm_city_element is not None else ''

        if ticket_zone_ref == "1":
            ticket_zone_ref = "A"
        elif ticket_zone_ref == "2":
            ticket_zone_ref = "B"

        adm_city_map = {
            "001": "Rzeszów",
            "005": "Krasne",
            "003": "Tyczyn",
            "006": "Świlcza",
            "009": "Siedliska",
            "010": "Chmielnik",
            "007": "Trzebownisko",
            "004": "Głogów Młp.",
            "008": "Boguchwała",
            "012": "Łańcut Miasto",
            "013": "Łańcut Gmina"
        }

        AdmCity = adm_city_map.get(AdmCity, "BRAK INFORMACJI")

        data.append([public_code, stop_name, on_demand, ticket_zone_ref, latitude, longitude, AdmCity])
        stop_names.append(stop_name)
        stop_name_id_pairs.append((stop_name, stop_ID))

    # Sortowanie danych
    data.sort(key=lambda x: locale.strxfrm(x[1]))
    stop_names.sort(key=locale.strxfrm)
    stop_name_id_pairs.sort(key=lambda x: locale.strxfrm(x[0]))

    # Upewniamy się, że folder WYNIKI istnieje
    os.makedirs('WYNIKI', exist_ok=True)

    # Zapis danych do plików
    with open('WYNIKI/Przystanki.txt', 'w', encoding='utf-8') as f:
        for row in data:
            f.write("\t".join(row) + "\n")

    with open('WYNIKI/Przystanki_names.txt', 'w', encoding='utf-8') as f:
        for name in stop_names:
            f.write(name + "\n")


def ZmienNazewnictwo():
    katalog_glowny = "WYNIKI"
    katalog_brygady = os.path.join(katalog_glowny, "Gotowe_brygady")

    try:
        with open("calendar.txt", "r", encoding="utf-8") as file:
            linie = file.readlines()

        # Pomijamy nagłówek
        for linia in linie[1:]:
            pola = linia.strip().split(",")
            if not pola or len(pola) < 1:
                continue

            stary_service_id = pola[0]
            print(f"\nZnaleziono service_id: {stary_service_id}")
            decyzja = input("Czy chcesz zmienić ten service_id? (t/n): ").strip().lower()

            if decyzja == "t":
                nowy_service_id = input("Podaj nową wartość dla tego service_id: ").strip()
                
                # Ścieżki
                sciezka_stara_glowna = os.path.join(katalog_glowny, stary_service_id)
                sciezka_nowa_glowna = os.path.join(katalog_glowny, nowy_service_id)

                sciezka_stara_brygady = os.path.join(katalog_brygady, stary_service_id)
                sciezka_nowa_brygady = os.path.join(katalog_brygady, nowy_service_id)

                # Zmiana w katalogu głównym
                if os.path.exists(sciezka_stara_glowna):
                    if not os.path.exists(sciezka_nowa_glowna):
                        shutil.move(sciezka_stara_glowna, sciezka_nowa_glowna)
                        print(f"Zmieniono nazwę folderu w '{katalog_glowny}': '{stary_service_id}' → '{nowy_service_id}'")
                    else:
                        print(f"Folder docelowy '{sciezka_nowa_glowna}' już istnieje. Pomijam.")
                else:
                    print(f"Folder '{sciezka_stara_glowna}' nie istnieje.")

                # Zmiana w Gotowe_brygady
                if os.path.exists(sciezka_stara_brygady):
                    if not os.path.exists(sciezka_nowa_brygady):
                        shutil.move(sciezka_stara_brygady, sciezka_nowa_brygady)
                        print(f"Zmieniono nazwę folderu w 'Gotowe_brygady': '{stary_service_id}' → '{nowy_service_id}'")
                    else:
                        print(f"Folder docelowy '{sciezka_nowa_brygady}' już istnieje. Pomijam.")
                else:
                    print(f"Folder '{sciezka_stara_brygady}' nie istnieje.")

            elif decyzja == "n":
                continue
            else:
                print("Nieprawidłowy wybór. Pomijam ten wpis.")

    except FileNotFoundError:
        print("Plik 'calendar.txt' nie został znaleziony.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")


    
    
    
    
    
    
    
import shutil
import os

def ZaaktualizujPliki():
    # Ścieżki folderów
    base_path = "../public/Brygady/"
    folders_to_delete = ["PowszedniWolny", "Sobotni", "Niedzielny"]
    source_folder = os.path.join(base_path, "Powszedni")

    # Usunięcie folderów docelowych
    for folder_name in folders_to_delete:
        target_path = os.path.join(base_path, folder_name)
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
            print(f"Usunięto folder: {target_path}")
        else:
            print(f"Folder nie istnieje: {target_path}")

    # Skopiowanie folderu źródłowego pod nowe nazwy
    for folder_name in folders_to_delete:
        target_path = os.path.join(base_path, folder_name)
        shutil.copytree(source_folder, target_path)
        print(f"Skopiowano {source_folder} do {target_path}")




    
    
    
    
    
    
    
    
    
      
      
def menu():
    while True:
        print("====== Pliki strony ============")
        print("1. Wczytaj brygady")
        print("2. Wczytaj numeracje brygad")
        print("3. Nazwij Brygady")
        print("4. Dodaj rezerwe")
        print("5. Dodaj podmiane")
        print("6. Utwórz Linie.txt")
        print("7. Utwórz Godz Rozp i Godz Zak")
        print("8. Utwórz plik GOTOWE.txt")  
        print("9. Wyznacz brygady bisowe")
        print("10. Wczytaj rodzaj brygad")
        print("11. Stwórz Liste Podmian")
        print("12. Stwórz Liste Podmian - wariant BAZA")
        print("13. Stwórz Liste Rezerw")
        print("14. Utwórz plik zbiorczy Kursy") 
        print("15 - TESTY POZMIENIAJ")
        print("16 - TESTY SPRAWDŹ PODMIENIAJ CZY SĄ INNE WARTOŚCI NIZ 1234")
        print("17 - TESTOWANKO utwórz liste podmian automatycznie")
        print("18. Utwórz plik Przystanki")
        print("19. Odczytaj przystanki (nazewnictwo itd)")
        print("100. Zaaktualizuj foldery (usuń stare, wstaw zaaktualizowane)")
        print("")
        print("20. Brygady + Numeracja + Nazwanie + Linie + Godziny + GOTOWE.txt + Wyznacz bb + Wczytaj bb + Plik Zbiorczy Kursy")
        print("calendar - wyświetl plik callendar.txt")
        print("================================")

        print("")
        print("====== Kody zapętlone ==============")
        print("Aby skorzystać z kodu zapętlonego, należy przed numerem wpisać znak hasztag #")
        print("Aby wyjść z trybu zapętlonego, należy zrestartować konsole")
        print("")
        print("====== Strona www ==============")
        print("90. Panel Wiadomości")
        print("91. Token administratora")
        wybor = input("Wybierz opcję: ")
        
        if wybor == "1":
            WczytajBrygady() 
            input("Gotowe.")
        elif wybor == "2":
            WczytajNumeracje()
            input("Gotowe.")            
        elif wybor == "3":
            NazwijBrygady()
            input("Gotowe.")            
        elif wybor == "4":
            DodajRezerwe() 
            input("Gotowe.")            
        elif wybor == "#4":
            BISDodajRezerwe()
            input("Gotowe.")            
        elif wybor == "5":
            Podmiana()
            input("Gotowe.")            
        elif wybor == "#5":
            BISPodmiana()
            input("Gotowe.")            
        elif wybor == "6":
            StwórzLinietxt()
            input("Gotowe.")            
        elif wybor == "7":
            StwórzGodzRozpGodzZak()
            input("Gotowe.")            
        elif wybor == "8":
            UtwórzGOTOWEtxt()
            input("Gotowe.")            
        elif wybor == "9":
            CzyBIS()
            input("Gotowe.")            
        elif wybor == "10":
            ZaproponujBrygadyBIS()
            input("Gotowe.")            
        elif wybor == "11":
            PodmianaList()
            input("Gotowe.")            
        elif wybor == "12":
            PodmianaBAZA()
            input("Gotowe.")            
        elif wybor == "13":
            RezerwaList()
            input("Gotowe.")            
        elif wybor == "14":
            StwórzZbiorczyKursy()
            input("Gotowe.")   
        elif wybor == "15":
            Pozmieniaj()
            input("Gotowe.")    
        elif wybor == "16":
            SprawdzPozmieniaj()
            input("Gotowe.")   
        elif wybor == '17':
            UtworzGodzPodmiany()
            input("Gotowe.")   
        elif wybor == '18':
            parse_kursy_file("WYNIKI/Gotowe_brygady/1/Kursy.txt")
            parse_kursy_file("WYNIKI/Gotowe_brygady/2/Kursy.txt")
            parse_kursy_file("WYNIKI/Gotowe_brygady/3/Kursy.txt")
            parse_kursy_file("WYNIKI/Gotowe_brygady/4/Kursy.txt")
            input("Gotowe.")
        elif wybor == '19':
            Wczytaj_Przystanki()
            input("Gotowe.")
        elif wybor == 'calendar':
            ZmienNazewnictwo()
        elif wybor == "20":
            clear_screen()
            #WczytajBrygady()            
            #WczytajNumeracje()
            #NazwijBrygady()
            #clear_screen()
            
            #clear_screen()
            czyrezerwa = input("Czy chcesz dodać rezerwe? t/n: ")
            while czyrezerwa == 't':
                DodajRezerwe()
                RezerwaList()
                czyrezerwa = input("Gotowe, czy chcesz dodać jeszcze jedną? t/n: ")
            clear_screen()
            #UtwórzGOTOWEtxt()
            czypodmiany = input("Czy chcesz aby system wygenerował automatycznie podmiany kierowców? t/n : ")
            if czypodmiany == "t":
                UtworzGodzPodmiany()
                PodmianaList()
                PodmianaBAZA()
            StwórzLinietxt()            
            StwórzGodzRozpGodzZak()
            CzyBIS()
            ZaproponujBrygadyBIS()
            StwórzZbiorczyKursy()
            parse_kursy_file("WYNIKI/Gotowe_brygady/1/Kursy.txt")
            parse_kursy_file("WYNIKI/Gotowe_brygady/2/Kursy.txt")
            parse_kursy_file("WYNIKI/Gotowe_brygady/3/Kursy.txt")
            parse_kursy_file("WYNIKI/Gotowe_brygady/4/Kursy.txt")
            Wczytaj_Przystanki()
            input("Gotowe.")  
        elif wybor == "100":
            ZaaktualizujPliki()
        elif wybor == "90":
            NewsMenu()
        elif wybor == "91":
            TokenMenu()
        elif wybor == "help":
            help()
        else:
            print("\nNiepoprawny wybór, spróbuj ponownie.\n")
            time.sleep(0.5)
            clear_screen()
            
            
def NewsMenu():
    clear_screen()
    print("===== MENU =====")
    print("1. Lista wiadomości")
    print("2. Utwórz Wiadomość")
    print("3. Edytuj wiadomość")
    print("4. Usuń wiadomość")    
    print("5. Przenieś wiadomość do archiwum")
    print("0. Wyjdź")
    Newswybor = input("Wybierz opcję: ")

    if Newswybor == "1":
            clear_screen()    
            NewsList()   
            input("Naciśnij [ENTER], aby kontunować...")
            NewsMenu()
    elif Newswybor == "2":
            clear_screen()
            AddNews()
    elif Newswybor == "3":
            clear_screen()  
            NewsList()
            EditNews()
    elif Newswybor == "4":
            clear_screen()
            DeleteNews()
    elif Newswybor == "5":
            clear_screen()
            NewsToArchy()
    elif Newswybor == "0":
            clear_screen() 
            

def TokenMenu():
    clear_screen()
    print("===== MENU =====")
    print("1. Wyświetl Token")
    print("2. Zmień Token")
    tokenwybor = input("Wybierz opcję: ")

    if tokenwybor == "1":
            clear_screen()    
            ShowToken()
            time.sleep(2)
            clear_screen()
    elif tokenwybor == "2":
            clear_screen()
            ChangeToken()
            
            
            
# Uruchomienie menu
if __name__ == "__main__":
    menu()
