import os
import re

# Funkcja pomocnicza do sortowania numerów
def numer_sort(key):
    return [int(c) if c.isdigit() else c for c in re.split('(\d+)', key)]

# Lista folderów do przetworzenia
foldery_do_przetworzenia = ["1", "2", "3", "4"]

# Iterujemy po folderach
for folder_num in foldery_do_przetworzenia:
    # Ścieżka do folderu
    sciezka = f"WYNIKI/Gotowe_brygady/{folder_num}"

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

    input("Naciśnij Enter, aby kontynuować...")
