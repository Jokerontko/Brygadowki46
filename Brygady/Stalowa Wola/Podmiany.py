import os

# Ścieżka do źródłowego pliku z podmianami
plik_wejsciowy = "podmiany.txt"

# Mapowanie skrótów na typy dnia
mapa_typow_dnia = {
    "PS": "Powszedni",
    "PW": "PowszedniWolny",
    "SS": "Sobotni",
    "NS": "Niedzielny"
}

# Struktura do zbierania danych wg (typ_dnia, brygada)
dane = {}

with open(plik_wejsciowy, "r", encoding="utf-8") as f:
    for linia in f:
        linia = linia.strip()
        if not linia:
            continue  # pomiń puste linie

        try:
            rozklad, brygada, godzina, przystanek = linia.split("\t")
        except ValueError:
            print(f"Nieprawidłowy format linii: {linia}")
            continue

        typ_dnia = mapa_typow_dnia.get(rozklad.strip())
        if not typ_dnia:
            print(f"Nieznany typ rozkładu: {rozklad}")
            continue

        brygada = brygada.strip().replace("/", "_")
        klucz = (typ_dnia, brygada)

        if klucz not in dane:
            dane[klucz] = []

        dane[klucz].append(f"{przystanek.strip()}\t{godzina.strip()}\t{godzina.strip()}")

# Tworzenie plików podmiana.txt
for (typ_dnia, brygada), linie in dane.items():
    katalog = os.path.join("WYNIKI", "Gotowe_brygady", typ_dnia, brygada)
    os.makedirs(katalog, exist_ok=True)
    sciezka_pliku = os.path.join(katalog, "podmiana.txt")

    with open(sciezka_pliku, "w", encoding="utf-8") as f:
        f.write("\n".join(linie))

print("Gotowe. Pliki zostały utworzone.")
