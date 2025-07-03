import os
import re

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
dirs_to_process = ['WYNIKI/Gotowe_brygady/Niedzielny', 'WYNIKI/Gotowe_brygady/Powszedni', 'WYNIKI/Gotowe_brygady/PowszedniWolny', 'WYNIKI/Gotowe_brygady/Sobotni']

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

input("done")
