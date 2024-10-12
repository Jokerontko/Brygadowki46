const express = require('express');
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 3000; // Używaj portu z Heroku lub 3000 w lokalnym środowisku

// Umożliwienie przetwarzania JSON w ciele żądań
app.use(bodyParser.json());

// Umożliwienie korzystania z plików statycznych
app.use(express.static('public'));

app.get('/', (req, res) => {
   res.sendFile(__dirname + '/public/index.html');
});



// Funkcja do przetwarzania folderów i plików
async function processDirectories(basePath) {
   const results = [];
   const folders = await fs.promises.readdir(basePath);

   for (const folder of folders) {
      const folderPath = path.join(basePath, folder);
      const stats = await fs.promises.stat(folderPath);

      if (stats.isDirectory()) {
         const folderName = folder.replace(/_/g, '/');
         const linesPath = path.join(folderPath, 'linie.txt');
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

// Endpoint do pobierania danych
app.get('/api/data', async (req, res) => {
   try {
      const dataPath = path.join(__dirname, '/Brygady/WYNIKI/Gotowe_brygady/1');
      const data = await processDirectories(dataPath);
      res.json(data);
   } catch (error) {
      console.error('Błąd serwera:', error);
      res.status(500).send('Błąd serwera: ' + error.message);
   }
});

// Endpoint do logowania
app.post('/login', (req, res) => {
   const {
      username,
      password
   } = req.body;

   // Odczytanie danych z pliku users.txt
   fs.readFile('public/users.txt', 'utf8', (err, data) => {
      if (err) {
         return res.status(500).json({
            error: 'Błąd odczytu pliku'
         });
      }

      // Rozdzielanie danych na linie
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

      // Szukaj użytkownika o podanym loginie i haśle
      const user = users.find(u => u.login === username && u.password === password);

      if (user) {
         res.json(user); // Zwróć dane użytkownika, jeśli logowanie się powiodło
      } else {
         res.status(401).json({
            error: 'Niepoprawna nazwa użytkownika lub hasło.'
         });
      }
   });
});

// Nowy endpoint do aktualizacji pliku Kierunki.txt
app.put('/updateKierunki', (req, res) => {
   const {
      routeId,
      newValue
   } = req.body;
   const filePath = path.join(__dirname, 'Brygady/WYNIKI/Kierunki.txt'); // Upewnij się, że ścieżka jest poprawna

   fs.readFile(filePath, 'utf8', (err, data) => {
      if (err) {
         return res.status(500).json({
            error: 'Błąd odczytu pliku'
         });
      }

      // Zaktualizuj zawartość pliku
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

// Umożliwienie serwowania plików statycznych
app.use(express.static(path.join(__dirname, 'public')));

// Obsługa zapytań GET dla ścieżki /brygady/*
app.get('/brygady/*', (req, res) => {
   const filePath = path.join(__dirname, 'Brygady', req.params[0]);
   res.sendFile(filePath);
});

// Uruchomienie serwera
app.listen(PORT, () => {
   console.log(`Serwer działa na http://localhost:${PORT}`);
});
