import os

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
            for line in lines:
                # Sprawdzamy, czy linia nie jest pusta
                if line.strip():
                    columns = line.split('\t')
                    if len(columns) > 3:
                        arrival_times.append(columns[3])
                    else:
                        print(f"Nieprawidłowy format linii: {line.strip()}")

            if arrival_times:
                # Zamieniamy czasy na format HH:MM
                arrival_times_hh_mm = [time[:5] for time in arrival_times]
                arrival_times_sorted = sorted(arrival_times_hh_mm)
                min_time = arrival_times_sorted[0]
                max_time = arrival_times_sorted[-1]

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

print("Przetwarzanie zakończone.")
input("Eoeo")
