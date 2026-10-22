@echo off
REM Crea GestoreGiftCardBambu.exe nella cartella dist\
REM Requisito: Python 3.10+ per Windows (python.org, con "Add to PATH" spuntato)
cd /d "%~dp0"
python -m pip install --upgrade pip pyinstaller || goto :errore
python -m unittest test_calcoli || goto :errore
python -m PyInstaller --noconfirm --onefile --windowed --name GestoreGiftCardBambu app.py || goto :errore
echo.
echo Fatto! L'eseguibile e' in: %~dp0dist\GestoreGiftCardBambu.exe
pause
exit /b 0
:errore
echo Build non riuscita.
pause
exit /b 1
