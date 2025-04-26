import os

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

            print(f'Sukces! Zapisano {len(sorted_numer_linii)} unikalnych numerów linii do pliku {linie_file}.')

input("Gotowe!")
