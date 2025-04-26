import os
import csv

# Ścieżki do folderów
folder_paths = ["WYNIKI/Gotowe_brygady/1", "WYNIKI/Gotowe_brygady/2", 
                "WYNIKI/Gotowe_brygady/3", "WYNIKI/Gotowe_brygady/4"]
numeracja_file_path = "WYNIKI/Numeracja brygad.txt"

# Wczytaj dane z pliku Numeracja brygad.txt
numeracja_map = {}

with open(numeracja_file_path, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter='\t')
    for row in reader:
        if len(row) == 2:
            block_id, id_brygady = row
            if id_brygady:  # Sprawdź, czy id_brygady nie jest puste
                numeracja_map[block_id] = id_brygady
            else:
                print(f"Pusta wartość id_brygady dla block_id: {block_id}")

# Przejdź przez foldery
for folder_path in folder_paths:
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

input("Chuj")