import express from 'express';
import fs from 'fs';
import path from 'path';
import bodyParser from 'body-parser';
import {
    fileURLToPath
} from 'url';
import {
    dirname
} from 'path';

// Get the __dirname equivalent in ES modules
const __filename = fileURLToPath(
    import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000; // Use Heroku's port or 3000 locally

// Enable JSON processing in request bodies
app.use(bodyParser.json());

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.use(express.static(path.join(__dirname, 'Przystanki')));









app.use(express.json()); // może się jeszcze przydać

app.get('/api/brygada', (req, res) => {
    const godzinaOdjazdu = req.query.godzina;
    const kierunek = req.query.kierunek;
    const wartoscdnia = req.query.dzien;

    console.log('⏱️ Odebrana godzina:', godzinaOdjazdu);
    console.log('📍 Odebrany kierunek:', kierunek);

    if (!godzinaOdjazdu || !kierunek || !wartoscdnia) {
        return res.status(400).json({
            message: 'Brakuje danych: godzina, kierunek lub wartość dnia.'
        });
    }

    const filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', wartoscdnia, 'PojazdyLIVE.txt');

    fs.readFile(filePath, 'utf8', (err, content) => {
        if (err) {
            console.error('❌ Błąd odczytu pliku:', err);
            return res.status(500).json({
                message: 'Błąd serwera podczas odczytu pliku.'
            });
        }

        const lines = content.split('\n').filter(line => line.trim() !== '');
        const godzinaOdjazduBezSekund = godzinaOdjazdu.trim().substring(0, 5); // np. 23:32
        const slowaZZapytania = kierunek.toLowerCase().split(/\s+/);

        console.log(`📂 Przeszukuję ${lines.length} linii...`);

        let najlepszeDopasowanie = null;
        let maksLiczbaSlow = 0;

        for (const line of lines) {
            const [godzinaZPlikuPełna, brygada, kierunekZPliku, linia] = line.split('\t');
            if (!godzinaZPlikuPełna || !kierunekZPliku) continue;

            let godzinaZPlikuBezSekund = godzinaZPlikuPełna.substring(0, 5); // tylko HH:MM

            if (godzinaZPlikuBezSekund === godzinaOdjazduBezSekund) {
                const kierunekZPlikuLower = kierunekZPliku.toLowerCase();

                // Zlicz ile słów z zapytania znajduje się w kierunku z pliku
                let liczbaPasujacychSlow = slowaZZapytania.filter(slowo =>
                    kierunekZPlikuLower.includes(slowo)
                ).length;

                console.log(`🔍 Kierunek z pliku: "${kierunekZPliku}" => Pasujące słowa: ${liczbaPasujacychSlow}`);

                // Zapamiętaj to dopasowanie, jeśli jest lepsze
                if (liczbaPasujacychSlow > maksLiczbaSlow) {
                    maksLiczbaSlow = liczbaPasujacychSlow;
                    najlepszeDopasowanie = {
                        brygada,
                        linia
                    };
                }
            }
        }

        if (najlepszeDopasowanie) {
            console.log(`✅ Najlepsze dopasowanie:`, najlepszeDopasowanie);
            return res.json(najlepszeDopasowanie);
        }

        console.warn('⚠️ Brak dopasowania – zwracam "Nieznana".');
        res.json({
            brygada: '',
            linia: ''
        });
    });
});









import fetch from 'node-fetch';
import cors from 'cors';


app.use(cors());

app.get('/api/vehicles', async (req, res) => {
    try {
        const response = await fetch('http://84.38.160.220/myBusServices/SchedulesService.svc/GetVehicles');
        const xmlData = await response.text();
        res.set('Content-Type', 'application/xml');
        res.send(xmlData);
    } catch (error) {
        console.error('Błąd podczas pobierania danych:', error);
        res.status(500).send('Błąd serwera proxy');
    }
});









app.get('/get-powszedni', (req, res) => {
    // Odbieramy nazwę przystanku i linię z parametrów zapytania
    const przystanekName = decodeURIComponent(req.query.przystanekName);
    const linia = req.query.linia; // Pobieramy parametr 'linia' z zapytania

    // Sprawdzamy, czy oba parametry są przekazane
    if (!przystanekName || !linia) {
        console.error('Brak wymaganych parametrów: przystanekName lub linia');
        return res.status(400).send('Brak wymaganych parametrów');
    }

    // Tworzymy ścieżkę do pliku, gdzie 'Linia' jest używana zamiast '11.txt'
    const filePath = path.join(__dirname, 'Przystanki', '2', przystanekName, `${linia}.txt`);

    console.log('Sprawdzam ścieżkę pliku:', filePath);

    // Sprawdzamy, czy plik istnieje
    fs.access(filePath, fs.constants.F_OK, (err) => {
        if (err) {
            console.error('Plik nie istnieje:', filePath);
            return res.status(404).send('Plik nie istnieje');
        }

        // Jeśli plik istnieje, odczytujemy dane
        fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) {
                console.error('Błąd odczytu pliku:', err.message); // Więcej szczegółów o błędzie
                return res.status(500).send('Błąd odczytu pliku');
            }

            console.log('Odczytano dane:', data); // Logujemy, że dane zostały poprawnie odczytane

            const rows = data.split('\n').map(line => {
                const columns = line.split('\t');
                return {
                    godzina: columns[0],
                    brygada: columns[1],
                    numer: columns[2]
                };
            });

            console.log('Dane przetworzone:', rows); // Logujemy przetworzone dane

            res.json(rows); // Odpowiadamy z danymi w formacie JSON
        });
    });
});


app.get('/get-sobotni', (req, res) => {
    // Odbieramy nazwę przystanku z parametrów zapytania
    const przystanekName = decodeURIComponent(req.query.przystanekName);
    const linia = req.query.linia; // Pobieramy parametr 'linia' z zapytania

    // Tworzymy ścieżkę do pliku, gdzie 'Linia' jest używana zamiast '11.txt'
    const filePath = path.join(__dirname, 'Przystanki', '4', przystanekName, `${linia}.txt`);

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            console.error('Błąd odczytu pliku:', err);
            return res.status(500).send('Błąd odczytu pliku');
        }

        console.log('Odczytano dane:', data); // Dodajemy log do sprawdzenia, czy dane są poprawnie wczytane

        const rows = data.split('\n').map(line => {
            const columns = line.split('\t');
            return {
                godzina: columns[0],
                brygada: columns[1],
                numer: columns[2]
            };
        });

        console.log('Dane przetworzone:', rows); // Logujemy przetworzone dane

        res.json(rows);
    });
});

app.get('/get-niedzielny', (req, res) => {
    // Odbieramy nazwę przystanku z parametrów zapytania
    const przystanekName = decodeURIComponent(req.query.przystanekName);
    const linia = req.query.linia; // Pobieramy parametr 'linia' z zapytania

    // Tworzymy ścieżkę do pliku, gdzie 'Linia' jest używana zamiast '11.txt'
    const filePath = path.join(__dirname, 'Przystanki', '1', przystanekName, `${linia}.txt`);

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            console.error('Błąd odczytu pliku:', err);
            return res.status(500).send('Błąd odczytu pliku');
        }

        console.log('Odczytano dane:', data); // Dodajemy log do sprawdzenia, czy dane są poprawnie wczytane

        const rows = data.split('\n').map(line => {
            const columns = line.split('\t');
            return {
                godzina: columns[0],
                brygada: columns[1],
                numer: columns[2]
            };
        });

        console.log('Dane przetworzone:', rows); // Logujemy przetworzone dane

        res.json(rows);
    });
});



// API do pobierania listy plików z katalogu przystanku
app.get('/api/pliki/:przystanekName', (req, res) => {
    const przystanekName = req.params.przystanekName;
    const folderNames = ['1', '2', '3', '4']; // Lista folderów, które chcemy sprawdzić
    const allFiles = new Set(); // Używamy Set, aby automatycznie usunąć duplikaty

    // Funkcja pomocnicza do sprawdzania folderów
    const findFilesInFolder = (index) => {
        if (index >= folderNames.length) {
            // Po zakończeniu przeszukiwania wszystkich folderów, zwróć pliki
            if (allFiles.size > 0) {
                return res.json(Array.from(allFiles)); // Zwracamy pliki bez duplikatów
            } else {
                return res.status(404).json({
                    error: 'Nie znaleziono plików w żadnym z folderów.'
                });
            }
        }

        const folderPath = path.join(__dirname, 'Przystanki', folderNames[index], przystanekName);

        fs.readdir(folderPath, (err, files) => {
            if (err) {
                // Jeśli jest błąd, próbujemy następny folder
                return findFilesInFolder(index + 1);
            }

            // Filtrujemy tylko pliki tekstowe
            const txtFiles = files.filter(file => file.endsWith('.txt'));

            // Dodajemy pliki do zbioru (Set automatycznie usuwa duplikaty)
            txtFiles.forEach(file => allFiles.add(file));

            // Przechodzimy do następnego folderu
            findFilesInFolder(index + 1);
        });
    };

    // Rozpoczynamy szukanie w pierwszym folderze
    findFilesInFolder(0);
});


// Endpoint do sprawdzania, które linie są nocne
app.get('/api/czyNocna', (req, res) => {
    const filePath = path.join(__dirname, 'Przystanki', 'CzyNocna.txt');

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            console.error("Błąd podczas odczytu CzyNocna.txt:", err);
            return res.status(500).json({
                error: 'Nie udało się odczytać pliku CzyNocna.txt'
            });
        }

        const result = {};
        data.split('\n').forEach(line => {
            const linia = line.trim().split('\t')[0];
            if (linia) {
                result[linia] = true;
            }
        });

        res.json(result);
    });
});




// Login endpoint
app.post('/login', (req, res) => {
    const {
        username,
        password
    } = req.body;

    fs.readFile(path.join(__dirname, 'public', 'users.txt'), 'utf8', (err, data) => {
        if (err) {
            return res.status(500).json({
                error: 'Błąd odczytu pliku'
            });
        }

        const lines = data.trim().split('\n');
        const users = lines.map(line => {
            const [userId, name, surname, login, pass] = line.split(':');
            return {
                userId: userId.trim(),
                name: name.trim(),
                surname: surname.trim(),
                login: login.trim(),
                password: pass.trim()
            };
        });

        const user = users.find(u => u.login === username && u.password === password);

        if (user) {
            res.json(user);
        } else {
            res.status(401).json({
                error: 'Niepoprawna nazwa użytkownika lub hasło.'
            });
        }
    });
});

//Login Panel
app.post('/loginPanel', (req, res) => {
    const {
        token
    } = req.body;

    fs.readFile(path.join(__dirname, 'public', 'Token.txt'), 'utf8', (err, data) => {
        if (err) {
            return res.status(500).json({
                error: 'Błąd odczytu pliku Token.txt'
            });
        }

        const fileToken = data.trim(); // Usuń białe znaki na początku/końcu pliku
        if (fileToken === token) {
            res.json({
                success: true,
                message: 'Token poprawny.'
            });
        } else {
            res.status(401).json({
                error: 'Niepoprawny Token.'
            });
        }
    });
});


// Przerwa Techniczna
app.get('/check-maintenance', (req, res) => {
    const maintenanceFilePath = path.join(__dirname, 'public', 'PrzerwaTechniczna.txt');

    // Odczytaj zawartość pliku za każdym razem, gdy endpoint jest wywoływany
    fs.readFile(maintenanceFilePath, 'utf8', (err, data) => {
        if (err) {
            // Zwróć błąd, jeśli plik nie może zostać odczytany
            return res.status(500).json({
                error: 'Błąd odczytu pliku'
            });
        }

        // Podziel zawartość na słowa (przez białe znaki)
        const words = data.split(/\s+/);

        // Sprawdź, czy "index.html" występuje wśród wyrazów
        const LoginMaintenance = words.includes('index.html');
        const ChooseDayMaintenance = words.includes('ChooseDay.html');
        const KursyMaintenance = words.includes('Kursy.html');

        // Wyślij aktualny wynik do klienta
        res.json({
            LoginMaintenance,
            ChooseDayMaintenance,
            KursyMaintenance
        });
    });
});



// Endpoint sprawdzający plik ChooseYear.txt
app.get('/check-chooseyear', (req, res) => {
    const brygadaTitle = req.query.brygadaTitle; // Pobieranie brygadaTitle z parametru URL

    if (!brygadaTitle) {
        return res.status(400).json({
            error: 'Brak parametru brygadaTitle'
        });
    }

    const mainChooseYear = path.join(__dirname, 'Brygady_Archiwum', brygadaTitle, 'ChooseYear.txt');

    fs.readFile(mainChooseYear, 'utf8', (err, data) => {
        if (err) {
            console.error('Błąd odczytu pliku:', err);
            return res.status(500).json({
                error: 'Błąd odczytu pliku'
            });
        }

        const isChooseYear = data.trim() === 'Tak';
        res.json({
            isChooseYear
        });
    });
});


// Endpoint sprawdzający plik ChooseDay.txt
app.get('/check-chooseday', (req, res) => {
    const brygadaTitle = req.query.brygadaTitle; // Pobieranie brygadaTitle z parametru URL

    if (!brygadaTitle) {
        return res.status(400).json({
            error: 'Brak parametru brygadaTitle'
        });
    }

    const mainChooseDay = path.join(__dirname, 'Brygady_Archiwum', brygadaTitle, 'ChooseDay.txt');

    fs.readFile(mainChooseDay, 'utf8', (err, data) => {
        if (err) {
            console.error('Błąd odczytu pliku:', err);
            return res.status(500).json({
                error: 'Błąd odczytu pliku'
            });
        }

        const isChooseDay = data.trim() === 'Tak';
        res.json({
            isChooseDay
        });
    });
});




// Function to process folders and files
async function processDirectories(basePath) {
    const results = [];
    const folders = await fs.promises.readdir(basePath);

    for (const folder of folders) {
        const folderPath = path.join(basePath, folder);
        const stats = await fs.promises.stat(folderPath);

        if (stats.isDirectory()) {
            const folderName = folder.replace(/_/g, '/');
            const linesPath = path.join(folderPath, 'Linie.txt');
            const godzRozpPath = path.join(folderPath, 'Godz_Rozp.txt');
            const godzZakPath = path.join(folderPath, 'Godz_Zak.txt');

            try {
                const [linie, godzRozp, godzZak] = await Promise.all([
               fs.promises.readFile(linesPath, 'utf-8'),
               fs.promises.readFile(godzRozpPath, 'utf-8'),
               fs.promises.readFile(godzZakPath, 'utf-8')
            ]);

                results.push({
                    brygada: folderName,
                    linie: linie.trim(),
                    godzRozp: godzRozp.trim(),
                    godzZak: godzZak.trim()
                });
            } catch (error) {
                console.error(`Błąd podczas odczytu plików w folderze ${folder}:`, error);
                results.push({
                    brygada: folderName,
                    linie: 'Brak danych',
                    godzRozp: 'Brak danych',
                    godzZak: 'Brak danych'
                });
            }
        }
    }

    return results;
}


// Function to process folders and files ZAPOWIEDZ
async function processDirectoriesZapowiedz(basePath1) {
    const results = [];
    const folders = await fs.promises.readdir(basePath1);

    for (const folder of folders) {
        const folderPath = path.join(basePath1, folder);
        const stats = await fs.promises.stat(folderPath);

        if (stats.isDirectory()) {
            const folderName = folder.replace(/_/g, '/');
            const linesPath = path.join(folderPath, 'Linie.txt');
            const godzRozpPath = path.join(folderPath, 'Godz_Rozp.txt');
            const godzZakPath = path.join(folderPath, 'Godz_Zak.txt');

            try {
                const [linie, godzRozp, godzZak] = await Promise.all([
               fs.promises.readFile(linesPath, 'utf-8'),
               fs.promises.readFile(godzRozpPath, 'utf-8'),
               fs.promises.readFile(godzZakPath, 'utf-8')
            ]);

                results.push({
                    brygada: folderName,
                    linie: linie.trim(),
                    godzRozp: godzRozp.trim(),
                    godzZak: godzZak.trim()
                });
            } catch (error) {
                console.error(`Błąd podczas odczytu plików w folderze ${folder}:`, error);
                results.push({
                    brygada: folderName,
                    linie: 'Brak danych',
                    godzRozp: 'Brak danych',
                    godzZak: 'Brak danych'
                });
            }
        }
    }

    return results;
}

// Endpoint to fetch data dla rozkładu Cmentarne
app.get('/api/dataCMENTARNE', async (req, res) => {
    try {
        const brygadaNumber = req.query.brygada || '1'; // Default to 1 if not provided
        const dataPath = path.join(__dirname, 'Brygady_Zapowiedz', 'WYNIKI', 'Gotowe_brygady', 'CMENTARNE');
        console.log(`Pobieram dane z: ${dataPath}`);
        const data = await processDirectories(dataPath);
        res.json(data);
    } catch (error) {
        console.error('Błąd serwera:', error);
        res.status(500).send('Błąd serwera: ' + error.message);
    }
});


// Endpoint to fetch data DLA ARCHIWUM
app.get('/api/archiwum', async (req, res) => {
    try {
        const dataPath = path.join(__dirname, 'Brygady_Archiwum');
        console.log(`Pobieram dane z: ${dataPath}`);
        const data = await processDirectories(dataPath);
        res.json(data);
    } catch (error) {
        console.error('Błąd serwera:', error);
        res.status(500).send('Błąd serwera: ' + error.message);
    }
});


// Handle GET requests for the path /brygady/* ARCHIWUM
app.get('/Brygady_Archiwum/*', (req, res) => {
    const filePath = path.join(__dirname, 'Brygady_Archiwum', req.params[0]);
    res.sendFile(filePath);
});


// Handle GET requests for the path /brygady/* ZAPOWIEDZ
app.get('/brygady_zapowiedz/*', (req, res) => {
    const filePath = path.join(__dirname, 'Brygady_Zapowiedz', req.params[0]);
    res.sendFile(filePath);
});



// Endpoint to fetch data
app.get('/api/data', async (req, res) => {
    try {
        const brygadaNumber = req.query.brygada || '1'; // Default to 1 if not provided
        const dataPath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', brygadaNumber);
        console.log(`Pobieram dane z: ${dataPath}`);
        const data = await processDirectories(dataPath);
        res.json(data);
    } catch (error) {
        console.error('Błąd serwera:', error);
        res.status(500).send('Błąd serwera: ' + error.message);
    }
});

// Endpoint to fetch data
app.get('/api/dataZapowiedz', async (req, res) => {
    try {
        const brygadaNumber = req.query.brygada || '1'; // Default to 1 if not provided
        const dataPath = path.join(__dirname, 'Brygady_Zmiany', 'WYNIKI', 'Gotowe_brygady', brygadaNumber);
        console.log(`Pobieram dane z: ${dataPath}`);
        const data = await processDirectories(dataPath);
        res.json(data);
    } catch (error) {
        console.error('Błąd serwera:', error);
        res.status(500).send('Błąd serwera: ' + error.message);
    }
});

// New endpoint to update Kierunki.txt
app.put('/updateKierunki', (req, res) => {
    const {
        routeId,
        newValue
    } = req.body;
    const filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Kierunki.txt');

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            return res.status(500).json({
                error: 'Błąd odczytu pliku'
            });
        }

        const updatedText = data.replace(new RegExp(`\\b${routeId}\\b`, 'g'), newValue);

        fs.writeFile(filePath, updatedText, 'utf8', (err) => {
            if (err) {
                return res.status(500).json({
                    error: 'Błąd zapisu pliku'
                });
            }
            res.json({
                message: 'Zaktualizowano plik Kierunki.txt'
            });
        });
    });
});









// Endpoint to fetch data
app.get('/api/data', async (req, res) => {
    try {
        const dataPath = path.join(__dirname, 'Brygady_Archiwum', brygadaNumber);
        console.log(`Pobieram dane z: ${dataPath}`);
        const data = await processDirectories(dataPath);
        res.json(data);
    } catch (error) {
        console.error('Błąd serwera:', error);
        res.status(500).send('Błąd serwera: ' + error.message);
    }
});

// New endpoint to update Kierunki.txt
app.put('/updateKierunki', (req, res) => {
    const {
        routeId,
        newValue
    } = req.body;
    const filePath = path.join(__dirname, 'Brygady_Archiwum', 'Kierunki.txt');

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            return res.status(500).json({
                error: 'Błąd odczytu pliku'
            });
        }

        const updatedText = data.replace(new RegExp(`\\b${routeId}\\b`, 'g'), newValue);

        fs.writeFile(filePath, updatedText, 'utf8', (err) => {
            if (err) {
                return res.status(500).json({
                    error: 'Błąd zapisu pliku'
                });
            }
            res.json({
                message: 'Zaktualizowano plik Kierunki.txt'
            });
        });
    });
});

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Handle GET requests for the path /brygady/*
app.get('/brygady/*', (req, res) => {
    const filePath = path.join(__dirname, 'Brygady', req.params[0]);
    res.sendFile(filePath);
});

// Ścieżka do folderu z plikami tekstowymi
const newsFolder = path.join(__dirname, 'public', 'News');

app.get('/api/files', (req, res) => {
    fs.readdir(newsFolder, (err, files) => {
        if (err) {
            console.error('Błąd odczytu plików:', err);
            return res.status(500).json({
                error: 'Błąd serwera'
            });
        }
        // Filtrowanie tylko plików .txt
        const txtFiles = files.filter(file => file.endsWith('.txt'));
        res.json(txtFiles);
    });
});

// Middleware do ustawiania nagłówków cache
app.use((req, res, next) => {
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
    next();
});

// Twoje trasy
app.get('/', (req, res) => {
    res.send('Witaj w mojej aplikacji!');
});



// Middleware do parsowania JSON
app.use(express.json());

// Ścieżka do pliku Token.txt
const tokenFilePath = path.join(__dirname, 'public', 'Token.txt');

// Endpoint do aktualizacji tokenu
app.post('/update-token', (req, res) => {
    const {
        token
    } = req.body;

    if (!token) {
        console.error('Nieprawidłowy token:', req.body);
        return res.status(400).json({
            message: 'Nieprawidłowy token.'
        });
    }

    console.log('Otrzymano token:', token);

    // Zapisz token do pliku
    fs.writeFile(tokenFilePath, token, (err) => {
        if (err) {
            console.error('Błąd zapisu do pliku:', err);
            return res.status(500).json({
                message: 'Błąd zapisu do pliku.'
            });
        }
        console.log('Token zapisany do pliku:', tokenFilePath);
        res.status(200).json({
            message: 'Token został zaktualizowany.'
        });
    });
});

// Endpoint do pobierania daty z pliku
app.get('/getDateFrom', (req, res) => {
    const filePath = path.join(__dirname, 'public', 'Brygady', 'wazny_od.txt');

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            res.status(500).send('Błąd odczytu pliku');
            return;
        }

        // Odpowiedź z zawartością pliku
        res.send(data.trim()); // .trim() usuwa niepotrzebne białe znaki
    });
});

// Obsługa żądań na innych endpointach
app.use((req, res) => {
    res.status(404).json({
        message: 'Endpoint nie istnieje.'
    });
});









// Middleware do obsługi JSON w ciele żądania
app.use(express.json());

// Ustawienie folderu 'News' (jeśli nie istnieje)
const newsFolderPath = path.join(__dirname, 'public', 'News');
if (!fs.existsSync(newsFolderPath)) {
    console.log('Folder "News" nie istnieje, tworzenie folderu...');
    fs.mkdirSync(newsFolderPath, {
        recursive: true
    }); // Używamy recursive, aby tworzyć foldery, jeśli nie istnieją
} else {
    console.log('Folder "News" już istnieje.');
}

// Endpoint do tworzenia pliku z wiadomościami
app.post('/create-news', (req, res) => {
    const {
        title,
        date,
        text,
        image
    } = req.body;

    console.log('Otrzymane dane:', req.body); // Dodajemy logowanie, aby sprawdzić dane

    // Sprawdzanie, czy wszystkie dane są dostępne
    if (!title || !date || !text || !image) {
        console.log('Brak danych w formularzu');
        return res.status(400).json({
            message: 'Wszystkie pola muszą być wypełnione'
        });
    }

    const newsContent = `
        Tytuł: ${title}
        Data: ${date}
        Treść: ${text}
        Załącznik: ${image}
    `;

    // Unikalna nazwa pliku, aby uniknąć nadpisania
    const fileName = `${title.replace(/\s+/g, '_')}_${Date.now()}.txt`; // Zmieniamy nazwę na unikalną
    const filePath = path.join(newsFolderPath, fileName);

    // Zapisanie pliku
    fs.writeFile(filePath, newsContent, 'utf8', (err) => {
        if (err) {
            console.error('Błąd zapisywania pliku:', err);
            return res.status(500).json({
                message: 'Błąd zapisu pliku'
            });
        }

        console.log('Plik zapisany w folderze News:', fileName);
        res.status(200).json({
            message: 'Wiadomość została zapisana!',
            fileName: fileName // Zwracamy nazwę zapisanego pliku
        });
    });
});







// Middleware do obsługi JSON
app.use(express.json());

app.post('/getRouteStops', (req, res) => {
    console.log('Otrzymano zapytanie POST do /getRouteStops');
    const {
        nrLinii
    } = req.body;

    if (!nrLinii) {
        return res.status(400).json({
            error: "Brak numeru linii."
        });
    }

    // Ścieżka do folderu z plikami tras
    const folderPath = path.join(__dirname, 'public', 'Brygady', 'Trasy_linii');
    const filePath = path.join(folderPath, `${nrLinii}.txt`);

    // Sprawdzanie, czy plik istnieje
    if (!fs.existsSync(filePath)) {
        return res.status(404).json({
            error: "Nie znaleziono pliku dla podanej linii."
        });
    }

    // Odczyt pliku
    fs.readFile(filePath, 'utf-8', (err, data) => {
        if (err) {
            console.error('Błąd odczytu pliku:', err);
            return res.status(500).json({
                error: "Błąd serwera podczas odczytu pliku."
            });
        }

        const stops = data.split('\n').map(stop => stop.trim()).filter(Boolean);
        res.json({
            stops
        });
    });
});


// Endpoint do pobierania daty
app.get('/getDateFrom', (req, res) => {
    // W tym miejscu możesz dynamicznie generować datę
    const dateFrom = new Date().toLocaleDateString('pl-PL');
    res.send(dateFrom);
});









// Middleware do obsługi plików statycznych
app.use(express.static("public"));

// Endpoint API do pobierania typu rozkładu
app.get("/api/rozklad", (req, res) => {
    const filePath = path.join(__dirname, "public/Brygady/Callendar.txt");

    // Pobierz aktualną datę w formacie DD.MM.YYYY
    const today = new Date();
    const formattedDate = today.toLocaleDateString("pl-PL", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    });

    console.log(`Szukam daty: ${formattedDate} w pliku ${filePath}`);

    // Odczytaj zawartość pliku
    fs.readFile(filePath, "utf8", (err, data) => {
        if (err) {
            console.error("Błąd odczytu pliku:", err);
            return res.status(500).json({
                error: "Nie udało się odczytać pliku"
            });
        }

        // Przeszukaj plik, aby znaleźć odpowiedni wpis
        const lines = data.split("\n");
        const foundLine = lines.find(line => line.startsWith(formattedDate));

        if (foundLine) {
            const [, scheduleType] = foundLine.split("\t");
            console.log(`Znaleziono rozkład: ${scheduleType.trim()}`);
            res.json({
                scheduleType: scheduleType.trim()
            });
        } else {
            console.log("Brak danych dla dzisiejszej daty.");
            res.json({
                scheduleType: "Brak danych dla dzisiejszej daty"
            });
        }
    });
});

// Obsługa nieistniejących endpointów
app.use((req, res) => {
    res.status(404).json({
        message: "Endpoint nie istnieje."
    });
});


// Obsługa żądania dla pliku Name_Day.txt
app.get('/Brygady/Name_Day.txt', (req, res) => {
    const filePath = path.join(__dirname, 'Name_Day.txt');

    // Sprawdzenie, czy plik istnieje
    fs.access(filePath, fs.constants.F_OK, (err) => {
        if (err) {
            // Jeśli plik nie istnieje, zwróć błąd 404
            console.error('Plik Name_Day.txt nie istnieje');
            res.status(404).send('Plik Name_Day.txt nie istnieje');
        } else {
            // Jeśli plik istnieje, wysyłamy go do klienta
            res.sendFile(filePath);
        }
    });
});









// Route do obsługi pliku
app.get('../../Brygady/WYNIKI/Gotowe_brygady/:folder/Podmiana_list.txt', (req, res) => {
    const folder = req.params.folder; // Pobiera nazwę folderu
    let filePath = '';

    // Ustawienie odpowiedniego path w zależności od folderu
    if (folder === '1') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '1', 'Podmiana_list.txt');
    } else if (folder === '2') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '2', 'Podmiana_list.txt');
    } else if (folder === '3') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '3', 'Podmiana_list.txt');
    } else if (folder === '4') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '4', 'Podmiana_list.txt');
    } else {
        return res.status(404).send('Nieznana ścieżka');
    }

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            return res.status(500).send('Błąd podczas odczytu pliku');
        }

        res.type('txt').send(data);
    });
});


// Route do obsługi pliku
app.get('../../Brygady/WYNIKI/Gotowe_brygady/:folder/PodmianaBAZA_list.txt', (req, res) => {
    const folder = req.params.folder; // Pobiera nazwę folderu
    let filePath = '';

    // Ustawienie odpowiedniego path w zależności od folderu
    if (folder === '1') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '1', 'PodmianaBAZA_list.txt');
    } else if (folder === '2') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '2', 'PodmianaBAZA_list.txt');
    } else if (folder === '3') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '3', 'PodmianaBAZA_list.txt');
    } else if (folder === '4') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '4', 'PodmianaBAZA_list.txt');
    } else {
        return res.status(404).send('Nieznana ścieżka');
    }

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            return res.status(500).send('Błąd podczas odczytu pliku');
        }

        res.type('txt').send(data);
    });
});




// Route do obsługi pliku
app.get('../../Brygady/WYNIKI/Gotowe_brygady/:folder/Rezerwa_list.txt', (req, res) => {
    const folder = req.params.folder; // Pobiera nazwę folderu
    let filePath = '';

    // Ustawienie odpowiedniego path w zależności od folderu
    if (folder === '1') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '1', 'Rezerwa_list.txt');
    } else if (folder === '2') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '2', 'Rezerwa_list.txt');
    } else if (folder === '3') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '3', 'Rezerwa_list.txt');
    } else if (folder === '4') {
        filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Gotowe_brygady', '4', 'Rezerwa_list.txt');
    } else {
        return res.status(404).send('Nieznana ścieżka');
    }

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            return res.status(500).send('Błąd podczas odczytu pliku');
        }

        res.type('txt').send(data);
    });
});







app.get('/przystanki', (req, res) => {
    const filePath = path.join(__dirname, 'Brygady', 'WYNIKI', 'Przystanki.txt');

    // Sprawdzamy, czy plik istnieje
    fs.exists(filePath, (exists) => {
        if (!exists) {
            return res.status(404).json({
                error: 'Plik Przystanki.txt nie został znaleziony.'
            });
        }

        // Odczytujemy plik
        fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) {
                console.error('Błąd odczytu pliku:', err);
                return res.status(500).json({
                    error: 'Nie udało się wczytać danych'
                });
            }

            // Zwracamy dane w formie JSON
            const stops = data.split('\n').filter(line => line.trim()).map(line => {
                const parts = line.split('\t');
                return {
                    kod: parts[0]?.trim() || '',
                    nazwa: parts[1]?.trim() || '',
                    naZadanie: parts[2]?.trim().toLowerCase() === 'true',
                    strefa: parts[3]?.trim() || '',
                    linie: '' // Można tu dodać obsługiwane linie, jeśli są dostępne w innym pliku
                };
            });

            res.json(stops);
        });
    });
});








// Uruchomienie serwera
app.listen(PORT, () => {
    console.log(`Serwer działa na porcie ${PORT}`);
});
