@echo off
REM Script de inicio rápido para FungiCloud (Windows)

echo ======================================
echo FungiCloud - Inicio Rápido
echo ======================================

REM Verificar Python
echo.
echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.9+ requerido
    exit /b 1
)

REM Crear virtual environment
echo.
echo [2/6] Creando entorno virtual...
python -m venv venv
call venv\Scripts\activate

REM Instalar dependencias
echo.
echo [3/6] Instalando dependencias...
pip install -r requirements.txt

REM Verificar .env
echo.
echo [4/6] Verificando configuración...
if not exist .env (
    echo Advertencia: No existe .env
    echo Copiando .env.example a .env...
    copy .env.example .env
    echo IMPORTANTE: Edita .env con tus credenciales antes de continuar
    pause
)

REM Inicializar base de datos
echo.
echo [5/6] Inicializando base de datos...
python -c "from database import init_database; init_database()"

REM Crear admin
echo.
echo [6/6] Deseas crear un usuario administrador? (S/N)
set /p response=
if /i "%response%"=="S" (
    python create_admin.py
)

echo.
echo ======================================
echo FungiCloud listo para ejecutar
echo ======================================
echo.
echo Comandos útiles:
echo   Desarrollo:  python app.py
echo   Producción:  gunicorn -w 4 -b 0.0.0.0:5000 app:app
echo.
pause
