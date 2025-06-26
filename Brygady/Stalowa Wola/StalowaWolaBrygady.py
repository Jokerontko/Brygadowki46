import os
import shutil

def formatuj_godzine(godzina):
    if len(godzina) == 5:
        return godzina + ":00"
    return godzina

def godzina_do_HHMM(godzina):
    czesci = godzina.strip().split(":")
    godz = int(czesci[0])
    minuty = int(czesci[1])
    return f"{godz:02d}:{minuty:02d}"

def do_HHMMSS(godzina):
    czesci = godzina.strip().split(":")
    godz = int(czesci[0])
    minuty = int(czesci[1])
    return f"{godz:02d}:{minuty:02d}:00"

# Zapytaj użytkownika o nazwę folderu
nazwa_folderu = input("Podaj nazwę folderu dla rozkładów: ").strip()
folder_glowny = os.path.join("WYNIKI", "Gotowe_brygady", nazwa_folderu)
os.makedirs(folder_glowny, exist_ok=True)

# Wczytywanie pliku wejściowego
plik_wejsciowy = "rozklady.txt"
with open(plik_wejsciowy, "r", encoding="utf-8") as f:
    zawartosc = f.read()

# Podział na kursy (pomijając puste linie)
kursy = [linia.strip() for linia in zawartosc.split("\n") if linia.strip()]

kursy_po_brygadzie = {}

for kurs in kursy:
    pola = kurs.split("\t")
    if len(pola) < 6:
        print(f"Pominięto niepoprawny wiersz: {kurs}")
        continue

    linia = pola[0].strip()
    rozp = formatuj_godzine(pola[1].strip())
    zak = formatuj_godzine(pola[2].strip())
    przyst_p = pola[3].strip()
    przyst_k = pola[4].strip()
    brygada_oryg = pola[5].strip()
    brygada_folder = brygada_oryg.replace("/", "_")

    if brygada_folder not in kursy_po_brygadzie:
        kursy_po_brygadzie[brygada_folder] = {
            "kursy": [],
            "gotowe_linie": [],
            "linie_set": set()
        }

    kursy_po_brygadzie[brygada_folder]["kursy"].append(kurs)
    kursy_po_brygadzie[brygada_folder]["linie_set"].add(linia)

    rozp_HHMMSS = do_HHMMSS(rozp)
    zak_HHMMSS = do_HHMMSS(zak)

    linia1 = f"{linia}\tx\tx\t{rozp_HHMMSS}\t{rozp_HHMMSS}\t\t{przyst_p}"
    linia2 = f"{linia}\tx\tx\t{zak_HHMMSS}\t{zak_HHMMSS}\t\t{przyst_k}"
    kursy_po_brygadzie[brygada_folder]["gotowe_linie"].extend([
        linia1,
        linia2,
        ""  # pusta linia po każdej parze
    ])

# Tworzenie folderów i zapisywanie danych
for brygada_folder, dane in kursy_po_brygadzie.items():
    folder_path = os.path.join(folder_glowny, brygada_folder)
    os.makedirs(folder_path, exist_ok=True)

    # kursy.txt
    kursy_path = os.path.join(folder_path, "kursy.txt")
    with open(kursy_path, "w", encoding="utf-8") as f:
        f.write("\n".join(dane["kursy"]))

    # GOTOWE.txt
    gotowe_path = os.path.join(folder_path, "GOTOWE.txt")
    with open(gotowe_path, "w", encoding="utf-8") as f:
        f.write("\n\n")  # dwa puste wiersze na początku
        f.write("\n".join(dane["gotowe_linie"]))

    # Godz_Rozp.txt
    pierwszy_kurs = dane["kursy"][0]
    pola_pierwszy = pierwszy_kurs.split("\t")
    if len(pola_pierwszy) >= 2:
        godz_r = formatuj_godzine(pola_pierwszy[1].strip())
        godz_hhmm = godzina_do_HHMM(godz_r)
        with open(os.path.join(folder_path, "Godz_Rozp.txt"), "w", encoding="utf-8") as f:
            f.write(godz_hhmm)

    # Godz_Zak.txt
    ostatni_kurs = dane["kursy"][-1]
    pola_ostatni = ostatni_kurs.split("\t")
    if len(pola_ostatni) >= 3:
        godz_z = formatuj_godzine(pola_ostatni[2].strip())
        godz_z_hhmm = godzina_do_HHMM(godz_z)
        with open(os.path.join(folder_path, "Godz_Zak.txt"), "w", encoding="utf-8") as f:
            f.write(godz_z_hhmm)

    # linie.txt
    linie_path = os.path.join(folder_path, "linie.txt")
    with open(linie_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(dane["linie_set"])))

    # Usuń kursy.txt
    os.remove(kursy_path)

print(f"\nGotowe. Dane zapisane w folderze: {folder_glowny}")
