@echo off
cls
echo Verificando instalacao do Python...

python --version 2>NUL
if errorlevel 1 (
    echo Python nao encontrado! Por favor, instale o Python 3.7 ou superior.
    echo Visite: https://www.python.org/downloads/
    pause
    exit /b
)

echo Verificando dependencias...
pip show pyrogram tgcrypto tqdm halo colorama pyfiglet unidecode >NUL
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Falha ao instalar dependencias.
        pause
        exit /b
    )
)

echo Iniciando ZipFileSender...
python main.py
pause