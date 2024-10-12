import os
import shutil

# Ścieżki do folderów
wyniki_folder = "WYNIKI"
gotowe_brygady_folder = os.path.join(wyniki_folder, "Gotowe_brygady")

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
            source_file_path = os.path.join(wyniki_folder, service_id, route_id, f"{trip_id}.txt")
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
