import os
import time
import csv
import re
import shutil


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
    input("Proces wykonano pomyślnie.")
    clear_screen()
                    




                    
        
        
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
                sorted_numer_linii = sorted(numer_linii_set)

                with open(linie_file, 'w', encoding='utf-8') as l_file:
                    for numer in sorted_numer_linii:
                        l_file.write(numer + '\n')

    input("Proces wykonano pomyślnie.")
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
                    with open(start_file_path, 'a', encoding='utf-8') as start_file:
                        start_file.write(min_time + '\n')

                    # Zapisujemy największy czas do Godz_Zak.txt
                    with open(end_file_path, 'a', encoding='utf-8') as end_file:
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

        print(f"Znaleziono {len(schedules)} rozkładów.")  # Debug: liczba znalezionych rozkładów
        return schedules

    def convert_time_to_minutes(time_str):
        """Konwertuje czas w formacie HH:MM:SS na całkowite minuty."""
        hours, minutes, seconds = map(int, time_str.split(':'))
        return hours * 60 + minutes + seconds / 60  # Zwraca minuty z ułamkiem

    def get_departure_times(schedule):
        times = []
        for line in schedule:
            # Sprawdzenie, czy wiersz jest w formacie z czasem odjazdu
            if re.match(r'^\d+\s+\d+\s+\d+\s+\d{2}:\d{2}:\d{2}\s+(\d{2}:\d{2}:\d{2})', line):
                departure_time_str = line.split()[4]
                try:
                    departure_time_in_minutes = convert_time_to_minutes(departure_time_str)
                    times.append((departure_time_in_minutes, line))
                except ValueError as e:
                    print(f"Błąd konwersji czasu odjazdu: {departure_time_str}. Błąd: {e}")
        return times

    def filter_schedule(schedule):
        header = schedule[0:2]  # Zakładamy, że nagłówki to pierwsze dwa wiersze
        departure_times = get_departure_times(schedule[2:])  # Sprawdzamy tylko kursy
        
        if not departure_times:
            print("Brak czasów odjazdów w rozkładzie.")  # Debug: brak czasów odjazdów
            return []  # Zwracamy pusty rozkład
        
        # Wiersze z minimalnym i maksymalnym departure_time
        min_time = min(departure_times, key=lambda x: x[0])[1]  # Wiersz z minimalnym departure_time
        max_time = max(departure_times, key=lambda x: x[0])[1]  # Wiersz z maksymalnym departure_time
        
        return header + [min_time, max_time]  # Zwracamy nagłówki oraz wiersze z min i max

    def sort_schedules_by_departure(schedules):
        return sorted(schedules, key=lambda sch: get_departure_times(sch[2:])[0][0] if get_departure_times(sch[2:]) else float('inf'))

    def write_sorted_schedules(schedules, output_path):
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                for schedule in schedules:
                    if schedule:  # Upewniamy się, że rozkład nie jest pusty
                        for line in schedule:
                            file.write(line)
                        file.write("\n")
        except Exception as e:
            print(f"Błąd przy zapisie do pliku: {e}")

    # Lista katalogów do przetworzenia
    dirs_to_process = ['WYNIKI/Gotowe_brygady/1', 'WYNIKI/Gotowe_brygady/2', 'WYNIKI/Gotowe_brygady/3', 'WYNIKI/Gotowe_brygady/4']

    for main_dir in dirs_to_process:
        # Sprawdzenie, czy główny folder istnieje
        if not os.path.exists(main_dir):
            print(f"Błąd: Folder {main_dir} nie istnieje!")
            continue

        output_file = os.path.join(main_dir, 'Kursy.txt')  # Plik wyjściowy w aktualnym katalogu

        # Tworzenie lub otwieranie pliku wyjściowego z kodowaniem UTF-8
        with open(output_file, 'w', encoding='utf-8') as kursy_file:
            # Przeglądanie wszystkich podfolderów i plików
            for root, dirs, files in os.walk(main_dir):
                # Pomijamy główny folder, bo chcemy tylko podfoldery
                if root != main_dir:
                    folder_name = os.path.basename(root)  # Pobranie nazwy folderu
                    for file in files:
                        # Sprawdzanie, czy plik ma rozszerzenie .txt i czy w nazwie są cyfry
                        if file.endswith('.txt') and re.search(r'\d', file):
                            file_path = os.path.join(root, file)

                            # Otwieranie pliku z kodowaniem UTF-8
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()

                                    # Wpisywanie zawartości pliku do Kursy.txt z informacją o folderze
                                    kursy_file.write(f"Folder: {folder_name}\n")  # Dodaj nazwę folderu
                                    kursy_file.write(content + '\n\n')
                                    print(f"Plik {file_path} został dodany do {output_file}")
                            except Exception as e:
                                print(f"Błąd przy przetwarzaniu pliku {file_path}: {e}")

        print(f"Zawartość została zapisana do pliku {output_file}")

        # Odczytaj, posortuj i zapisz rozkłady jazdy
        schedules = read_schedule(output_file)
        if schedules:
            filtered_schedules = [filter_schedule(schedule) for schedule in schedules]
            sorted_schedules = sort_schedules_by_departure(filtered_schedules)
            output_sorted_file = os.path.join(main_dir, 'Kursy_filtered_sorted.txt')
            write_sorted_schedules(sorted_schedules, output_sorted_file)
            print(f"Sortowanie i filtrowanie zakończone sukcesem! Wyniki zapisano w {output_sorted_file}")
        else:
            print("Brak rozkładów do przetworzenia.")

      
          
def Podmiana():
    typ_podmiany = input("Wprowadź typ podmiany (nic = w mieście, B = w bazie): ")
    if typ_podmiany == "B":
        SpecialDodajPodmiane()
    else:
        DodajPodmiane()

        
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
        input("Proces wykonano pomyślnie.")
        clear_screen()        
    except Exception as e:
        print(f"Wystąpił błąd w opcji 6: {e}")

  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  

  

      
    
    
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
      
      
      
      
      
      
      
      
      
def menu():
    while True:
        print("===== MENU =====")
        print("1. Wczytaj brygady")
        print("2. Utwórz Linie.txt")
        print("3. Utwórz Godz Rozp i Godz Zak")
        print("4. Utwórz Brygady BIS")
        print("5. Modyfikuj BRYGADY BIS")
        print("6. Dodaj rezerwe")
        print("7. Nazwij Brygady")
        print("8. Utwórz plik zbiorczy Kursy")    
        print("9. Utwórz plik GOTOWE.txt")       
        print("10. Dodaj podmiane")   
        wybor = input("Wybierz opcję: ")
        
        if wybor == "1":
            WczytajBrygady()
        elif wybor == "2":
            StwórzLinietxt()
        elif wybor == "3":
            StwórzGodzRozpGodzZak()
        elif wybor == "4":
            StwórzBrygadyBIS()
        elif wybor == "5":
            ModyfikujBrygadyBIS()    
        elif wybor == "6":
            DodajRezerwe() 
        elif wybor == "7":
            NazwijBrygady()
        elif wybor == "8":
            StwórzZbiorczyKursy() 
        elif wybor == "9":
            UtwórzGOTOWEtxt()
        elif wybor == "10":
            Podmiana()
        elif wybor == "help":
            help()
        else:
            print("\nNiepoprawny wybór, spróbuj ponownie.\n")

# Uruchomienie menu
if __name__ == "__main__":
    menu()
