import os

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

def process_folders(base_path):
    print(f"Przechodzenie przez folder: {base_path}")
    
    # Przechodzimy przez wszystkie foldery w folderze bazowym
    for foldername in os.listdir(base_path):
        folder_path = os.path.join(base_path, foldername)
        if os.path.isdir(folder_path):  # Tylko foldery
            sort_lines_by_arrival_time(folder_path)

if __name__ == "__main__":
    base_path = "WYNIKI/Gotowe_brygady/3"  # Zmień na odpowiednią ścieżkę
    if os.path.exists(base_path):
        process_folders(base_path)
    else:
        print(f"Ścieżka nie istnieje: {base_path}")
