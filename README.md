# Gestore Gift Card Bambu Lab

App desktop per Windows (interfaccia in italiano) per gestire le gift card Bambu Lab da 40 € e 200 € ottenute con i punti MakerWorld.

## Cosa fa

- **Calcolatore gift card**: inserisci il prezzo di un oggetto Bambu Lab e l'app ti dice quante gift card da 40 € servono (524 punti ciascuna), quanti punti usi e l'eventuale avanzo. Una tabella mostra quanto incassi vendendo ogni card da 30 a 40 € e quanto guadagni in più rispetto a convertire gli stessi punti direttamente in soldi.
- **Versione iPhone**: https://trambustobot.github.io/gift-card-bambu/ (da Safari: Condividi → Aggiungi alla schermata Home). Il codice è in `docs/`, i dati restano sul telefono.
- **Inventario gift card**: tabella con Taglio, Codice, Stato e Acquirente, modificabile direttamente cliccando sulle celle (salvataggio automatico). Con «Incolla codici» crei una riga per ogni codice copiato. «Esporta CSV» e «Importa CSV» passano l'inventario tra PC e iPhone: l'importazione aggiorna le card con lo stesso codice e aggiunge quelle nuove.

Il valore di un punto in USD e il cambio USD→EUR si modificano direttamente nel calcolatore.
I dati sono salvati in `%APPDATA%\BambuGiftCard\dati.json`.

## Creare il file .exe

**Opzione A, sul tuo PC**: installa Python 3.10+ da python.org (spunta "Add python.exe to PATH"), poi fai doppio clic su `build.bat`. L'eseguibile sarà in `dist\GestoreGiftCardBambu.exe`.

**Opzione B, con GitHub**: carica questa cartella in un repository GitHub. Il workflow in `.github/workflows/build.yml` crea l'exe a ogni push su `main`: lo trovi nella scheda *Actions*, nella sezione *Artifacts* dell'esecuzione. Se crei un tag `v1.0`, l'exe viene allegato anche a una Release.

## Avviare senza compilare

`python app.py` (serve solo Python, nessuna libreria esterna).
