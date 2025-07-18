@echo off
title Installation NasMiner PRO - Setup
color 0C

echo ==============================
echo   NasMiner PRO - Setup Batch
echo ==============================

:: Vérifier Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH.
    echo Ouverture de la page de téléchargement...
    powershell -Command "Start-Process 'https://www.python.org/downloads/'"
    echo Veuillez installer Python 3.8+ puis relancer ce setup.
    pause
    exit /b 1
)

:: Mettre à jour pip
echo Mise à jour de pip...
python -m pip install --upgrade pip

:: Installer les dépendances Python nécessaires
echo Installation des dépendances Python...
python -m pip install --no-cache-dir PyQt6 psutil matplotlib Pillow

:: Vérifier et télécharger XMRig si absent
if not exist xmrig.exe (
    echo [*] XMRig non trouvé, téléchargement en cours...
    curl -L -o xmrig.zip https://github.com/xmrig/xmrig/releases/download/v6.21.1/xmrig-6.21.1-msvc-win64.zip
    if errorlevel 1 (
        echo [ERREUR] Le téléchargement de XMRig a échoué.
        pause
        exit /b 1
    )
    echo Extraction de xmrig.zip...
    powershell -Command "Expand-Archive -Path 'xmrig.zip' -DestinationPath '.'"
    move /Y xmrig-6.21.1\xmrig.exe .
    rmdir /S /Q xmrig-6.21.1
    del xmrig.zip
    echo [✔] XMRig installé avec succès !
) else (
    echo [✔] XMRig déjà présent.
)

:: Vérifier dossier img
if not exist img (
    echo [ATTENTION] Le dossier 'img' avec les logos est manquant.
    echo Veuillez ajouter le dossier 'img' avant de lancer le logiciel.
    pause
)

echo Lancement de NasMiner PRO...
python NasMinerSoftware.py

pause

