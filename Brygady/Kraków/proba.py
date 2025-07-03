import os


def stworz_katalogi():
    # Ścieżka bazowa
    base_path = os.path.join("WYNIKI", "Gotowe_brygady")
    os.makedirs(base_path, exist_ok=True)

    # Wczytaj plik ręcznie linia po linii
    try:
        with open("calendar.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("❌ Nie znaleziono pliku 'calendar.txt'.")
        return

    # Pomijamy nagłówek
    for line in lines[1:]:
        # Pomijaj puste linie
        if not line.strip():
            continue

        # Podziel po przecinkach
        parts = line.strip().split(",")

        # Sprawdź, czy mamy wystarczająco kolumn
        if len(parts) < 1:
            print("⚠️ Pominięto niepoprawny wiersz:", line)
            continue

        # Weź service_id (pierwsza kolumna)
        service_id = parts[0].strip()

        # Stwórz folder dla tego service_id
        folder_path = os.path.join(base_path, service_id)
        os.makedirs(folder_path, exist_ok=True)
        print(f"✔ Utworzono: {folder_path}")

# Przykładowe wywołanie funkcji
# stworz_katalogi()




    


def wypakujdane():
    base_path = os.path.join("WYNIKI", "Gotowe_brygady")
    stop_times_file = "stop_times.txt"
    stops_file = "stops.txt"
    trips_file = "trips.txt"
    routes_file = "routes.txt"
    
    # Wczytaj trips.txt i zbuduj słownik trip_id -> route_id
    trip_to_route = {}
    try:
        with open(trips_file, "r", encoding="utf-8") as f_trips:
            lines_trips = f_trips.readlines()
    except FileNotFoundError:
        print(f"❌ Nie znaleziono pliku '{trips_file}'. Nie będzie mapowania trip_id na route_id.")
        trip_to_route = None
    else:
        header_trips = lines_trips[0].strip().split(",")
        try:
            idx_trip_id = header_trips.index("trip_id")
            idx_route_id = header_trips.index("route_id")
        except ValueError as e:
            print(f"❌ Brak kolumny w pliku trips.txt: {e}")
            trip_to_route = None
        else:
            for line in lines_trips[1:]:
                if not line.strip():
                    continue
                parts = line.strip().split(",")
                if len(parts) <= max(idx_trip_id, idx_route_id):
                    continue
                tid = parts[idx_trip_id].strip()
                rid = parts[idx_route_id].strip()
                trip_to_route[tid] = rid
    
    # Wczytaj routes.txt i zbuduj słownik route_id -> route_short_name
    routeid_to_shortname = {}
    try:
        with open(routes_file, "r", encoding="utf-8") as f_routes:
            lines_routes = f_routes.readlines()
    except FileNotFoundError:
        print(f"❌ Nie znaleziono pliku '{routes_file}'. Nie będzie mapowania route_id na route_short_name.")
        routeid_to_shortname = None
    else:
        header_routes = lines_routes[0].strip().split(",")
        try:
            idx_route_id_r = header_routes.index("route_id")
            idx_route_short_name = header_routes.index("route_short_name")
        except ValueError as e:
            print(f"❌ Brak kolumny w pliku routes.txt: {e}")
            routeid_to_shortname = None
        else:
            for line in lines_routes[1:]:
                if not line.strip():
                    continue
                parts = line.strip().split(",")
                if len(parts) <= max(idx_route_id_r, idx_route_short_name):
                    continue
                rid = parts[idx_route_id_r].strip()
                rsn = parts[idx_route_short_name].strip().replace('"', '')  # usuwamy cudzysłowy
                routeid_to_shortname[rid] = rsn
    
    # Wczytaj stops.txt i zbuduj słownik stop_id -> stop_name
    stop_id_to_name = {}
    try:
        with open(stops_file, "r", encoding="utf-8") as f_stops:
            lines_stops = f_stops.readlines()
    except FileNotFoundError:
        print(f"❌ Nie znaleziono pliku '{stops_file}'. Nie będzie mapowania stop_id na stop_name.")
        stop_id_to_name = None
    else:
        header_stops = lines_stops[0].strip().split(",")
        try:
            idx_stop_id = header_stops.index("stop_id")
            idx_stop_name = header_stops.index("stop_name")
        except ValueError as e:
            print(f"❌ Brak kolumny w pliku stops.txt: {e}")
            stop_id_to_name = None
        else:
            for line in lines_stops[1:]:
                if not line.strip():
                    continue
                parts = line.strip().split(",")
                if len(parts) <= max(idx_stop_id, idx_stop_name):
                    continue
                sid = parts[idx_stop_id].strip()
                sname = parts[idx_stop_name].strip().replace('"', '')  # usuwamy cudzysłowy
                stop_id_to_name[sid] = sname
    
    # Wczytaj stop_times.txt
    try:
        with open(stop_times_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ Nie znaleziono pliku '{stop_times_file}'.")
        return
    
    header = lines[0].strip().split(",")
    
    try:
        idx_trip_id = header.index("trip_id")
        idx_arrival_time = header.index("arrival_time")
        idx_departure_time = header.index("departure_time")
        idx_stop_id = header.index("stop_id")
    except ValueError as e:
        print(f"❌ Brak kolumny w nagłówku stop_times.txt: {e}")
        return
    
    for line_num, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        
        parts = line.strip().split(",")
        if len(parts) < max(idx_trip_id, idx_arrival_time, idx_departure_time, idx_stop_id) + 1:
            print(f"⚠️ Linia {line_num} jest niekompletna, pomijam.")
            continue
        
        trip_id = parts[idx_trip_id]
        arrival_time = parts[idx_arrival_time]
        departure_time = parts[idx_departure_time]
        stop_id = parts[idx_stop_id]
        
        # Zamień stop_id na stop_name jeśli jest słownik
        if stop_id_to_name is not None and stop_id in stop_id_to_name:
            stop_name = stop_id_to_name[stop_id]
        else:
            stop_name = stop_id
        
        # trip_id ma format block_X_trip_Y_service_Z
        trip_parts = trip_id.split("_")
        if len(trip_parts) < 6:
            print(f"⚠️ Linia {line_num}: trip_id '{trip_id}' ma zły format, pomijam.")
            continue
        
        block_x = trip_parts[1]
        trip_y = trip_parts[3]
        service_z = trip_parts[5]
        
        folder_path = os.path.join(base_path, service_z, f"block_{block_x}")
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, f"{trip_y}.txt")

        # Jeśli plik nie istnieje, utwórz go z 3 pustymi liniami na początku
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f_out:
                f_out.write("\n\n\n")  # 3 puste linie
        
        # Pobierz route_id z trip_to_route lub wpisz 'UNKNOWN'
        route_id = trip_to_route.get(trip_id, "UNKNOWN") if trip_to_route is not None else "UNKNOWN"
        # Pobierz route_short_name z routeid_to_shortname lub wpisz 'UNKNOWN', usuń cudzysłowy
        route_short_name = routeid_to_shortname.get(route_id, "UNKNOWN") if routeid_to_shortname is not None else "UNKNOWN"
        route_short_name = route_short_name.replace('"', '')
        
        output_line = f"{route_short_name}\t{service_z}\t{trip_y}\t{arrival_time}\t{departure_time}\t\t{stop_name}\n"
        
        with open(file_path, "a", encoding="utf-8") as f_out:
            f_out.write(output_line)
    
    print("✅ Przetwarzanie stop_times.txt zakończone.")



    
    
    
def zmiennazwy():
    base_path = os.path.join("WYNIKI", "Gotowe_brygady")
    blocks_file = "blocks.txt"
    
    # Wczytaj blocks.txt do słownika block_id -> shift
    block_to_shift = {}
    try:
        with open(blocks_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ Nie znaleziono pliku '{blocks_file}'. Nie mogę zmienić nazw folderów.")
        return
    
    header = lines[0].strip().split(",")
    try:
        idx_block_id = header.index("block_id")
        idx_shift = header.index("shift")
    except ValueError as e:
        print(f"❌ Brak kolumny w pliku blocks.txt: {e}")
        return
    
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.strip().split(",")
        if len(parts) <= max(idx_block_id, idx_shift):
            continue
        block_id = parts[idx_block_id].strip()
        shift = parts[idx_shift].strip()
        block_to_shift[block_id] = shift
    
    # Przejdź po folderach w WYNIKI/Gotowe_brygady
    if not os.path.exists(base_path):
        print(f"❌ Folder '{base_path}' nie istnieje.")
        return
    
    for service_folder in os.listdir(base_path):
        service_path = os.path.join(base_path, service_folder)
        if not os.path.isdir(service_path):
            continue
        
        # Przejdź po podfolderach (np. block_1, block_2)
        for block_folder in os.listdir(service_path):
            block_path = os.path.join(service_path, block_folder)
            if not os.path.isdir(block_path):
                continue
            
            # Sprawdź, czy nazwa podfolderu jest w block_to_shift
            if block_folder in block_to_shift:
                new_name = block_to_shift[block_folder]
                new_path = os.path.join(service_path, new_name)
                if os.path.exists(new_path):
                    print(f"⚠️ Folder docelowy '{new_path}' już istnieje, pomijam zmianę nazwy '{block_path}'.")
                    continue
                
                os.rename(block_path, new_path)
                print(f"✅ Zmieniono nazwę: '{block_path}' -> '{new_path}'")
            else:
                print(f"⚠️ Brak dopasowania dla folderu '{block_folder}', pomijam.")
    
    print("✅ Zmiana nazw zakończona.")    
    
    
    
    
def utworzlinie():
    base_path = os.path.join("WYNIKI", "Gotowe_brygady")
    
    if not os.path.exists(base_path):
        print(f"❌ Brak folderu bazowego: {base_path}")
        return
    
    for service_folder in os.listdir(base_path):
        service_path = os.path.join(base_path, service_folder)
        if not os.path.isdir(service_path):
            continue
        
        for block_folder in os.listdir(service_path):
            block_path = os.path.join(service_path, block_folder)
            if not os.path.isdir(block_path):
                continue
            
            route_names = set()
            
            # Przeszukaj wszystkie pliki .txt w folderze block_X
            for filename in os.listdir(block_path):
                if not filename.endswith(".txt"):
                    continue
                file_path = os.path.join(block_path, filename)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"⚠️ Nie udało się odczytać pliku {file_path}: {e}")
                    continue
                
                # Pierwsze 3 linie to puste, potem od linii 4 są dane
                for line in lines[3:]:
                    if not line.strip():
                        continue
                    parts = line.strip().split("\t")
                    if parts:
                        route_names.add(parts[0])
            
            # Zapisz unikalne route_short_name do pliku linie.txt
            linie_file = os.path.join(block_path, "linie.txt")
            try:
                with open(linie_file, "w", encoding="utf-8") as f_out:
                    for route in sorted(route_names):
                        f_out.write(route + "\n")
            except Exception as e:
                print(f"⚠️ Nie udało się zapisać pliku {linie_file}: {e}")
    
    print("✅ Utworzono pliki linie.txt z unikalnymi route_short_name.")    
    
    
import os
import re

def wyciagnij_godzine(line):
    # Szuka wzorca HH:MM na początku linii lub gdziekolwiek
    match = re.search(r'(\d{1,2}):(\d{2})', line)
    if not match:
        return None
    hh = int(match.group(1))
    mm = int(match.group(2))
    return hh * 60 + mm  # zwraca minuty od północy do łatwego sortowania

def utworzGOTOWEtxt():
    base_path = os.path.join("WYNIKI", "Gotowe_brygady")

    if not os.path.exists(base_path):
        print(f"❌ Brak folderu bazowego: {base_path}")
        return

    exclude_files = {"linie.txt", "godz_rozp.txt", "godz_zak.txt", "GOTOWE.txt"}

    for service_folder in os.listdir(base_path):
        service_path = os.path.join(base_path, service_folder)
        if not os.path.isdir(service_path):
            continue

        for block_folder in os.listdir(service_path):
            block_path = os.path.join(service_path, block_folder)
            if not os.path.isdir(block_path):
                continue

            files_with_times = []

            txt_files = [f for f in os.listdir(block_path)
                         if f.endswith(".txt") and f not in exclude_files]

            for filename in txt_files:
                file_path = os.path.join(block_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = [line.rstrip("\n") for line in f.readlines()]
                except Exception as e:
                    print(f"⚠️ Nie udało się odczytać pliku {file_path}: {e}")
                    continue

                # Pomijamy pierwsze 3 linie
                lines = lines[3:]
                if not lines:
                    continue

                # Wyciągamy godzinę z pierwszej linii
                czas = wyciagnij_godzine(lines[0])
                if czas is None:
                    # Jeśli nie ma godziny, daj dużą wartość, by iść na koniec
                    czas = 9999

                files_with_times.append((czas, filename, lines))

            # Sortujemy po czasie rosnąco
            files_with_times.sort(key=lambda x: x[0])

            collected_blocks = []

            for _, filename, lines in files_with_times:
                if len(lines) == 1:
                    filtered_lines = [lines[0]]
                else:
                    filtered_lines = [lines[0], lines[-1]]
                collected_blocks.append(filtered_lines)

            if not collected_blocks:
                continue

            final_content = []
            for block in collected_blocks:
                final_content.extend(block)
                final_content.append("")

            if final_content and final_content[-1] == "":
                final_content.pop()

            output_file = os.path.join(block_path, "GOTOWE.txt")
            try:
                with open(output_file, "w", encoding="utf-8") as f_out:
                    for line in final_content:
                        f_out.write(line + "\n")
            except Exception as e:
                print(f"⚠️ Nie udało się zapisać pliku {output_file}: {e}")

    print("✅ Utworzono pliki GOTOWE.txt w podfolderach.")



    
    
    
    
import os
import re

def rozpoczecieizakonczenie():
    base_path = os.path.join("WYNIKI", "Gotowe_brygady")

    time_pattern = re.compile(r'(\d{1,2}):(\d{2})')

    if not os.path.exists(base_path):
        print(f"❌ Brak folderu bazowego: {base_path}")
        return

    for service_folder in os.listdir(base_path):
        service_path = os.path.join(base_path, service_folder)
        if not os.path.isdir(service_path):
            continue

        for block_folder in os.listdir(service_path):
            block_path = os.path.join(service_path, block_folder)
            if not os.path.isdir(block_path):
                continue

            gotowe_file = os.path.join(block_path, "GOTOWE.txt")
            if not os.path.isfile(gotowe_file):
                print(f"⚠️ Brak pliku GOTOWE.txt w {block_path}, pomijam.")
                continue

            min_time = None
            max_time = None

            try:
                with open(gotowe_file, "r", encoding="utf-8") as f:
                    for line in f:
                        match = time_pattern.search(line)
                        if not match:
                            continue
                        hh = int(match.group(1))
                        mm = int(match.group(2))
                        total_min = hh * 60 + mm

                        if (min_time is None) or (total_min < min_time):
                            min_time = total_min
                        if (max_time is None) or (total_min > max_time):
                            max_time = total_min
            except Exception as e:
                print(f"⚠️ Błąd podczas czytania {gotowe_file}: {e}")
                continue

            if min_time is None or max_time is None:
                print(f"⚠️ Nie znaleziono żadnej godziny w {gotowe_file}.")
                continue

            def min_to_str(total_min):
                hh = total_min // 60
                mm = total_min % 60
                return f"{hh:02d}:{mm:02d}"

            godz_rozp = min_to_str(min_time)
            godz_zak = min_to_str(max_time)

            try:
                with open(os.path.join(block_path, "Godz_Rozp.txt"), "w", encoding="utf-8") as f_rozp:
                    f_rozp.write(godz_rozp + "\n")
                with open(os.path.join(block_path, "Godz_Zak.txt"), "w", encoding="utf-8") as f_zak:
                    f_zak.write(godz_zak + "\n")
            except Exception as e:
                print(f"⚠️ Błąd podczas zapisu plików Godz_Rozp.txt lub Godz_Zak.txt w {block_path}: {e}")
                continue

    print("✅ Utworzono pliki Godz_Rozp.txt i Godz_Zak.txt we wszystkich podfolderach.")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
def menu():
    while True:
        print("====== Pliki strony ============")
        print("1. Wczytaj foldery z calendar.txt")
        print("2. Wgraj brygady")
        print("3. zmien nazwy folderow")
        print("4. utworz linie")
        print("5. utworz GOTOWE.txt")
        print("6. godz rozp i godz zak")

        wybor = input("Wybierz opcję: ")
        
        if wybor == "1":
            stworz_katalogi() 
            input("Gotowe.")
        elif wybor == "2":
            wypakujdane()
            input("Gotowe.")           
        elif wybor == "3":
            zmiennazwy()
            input("gotowe.")
        elif wybor == "4":
            utworzlinie()
            input("gotowe.")
        elif wybor == "5":
            utworzGOTOWEtxt()
            input("gotowe.")
        elif wybor == "6":
            rozpoczecieizakonczenie()
            input("gotowe.")
        
            
            
# Uruchomienie menu
if __name__ == "__main__":
    menu()    