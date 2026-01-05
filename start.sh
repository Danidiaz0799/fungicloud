#!/bin/bash
# Script de inicio rápido para FungiCloud

echo "======================================"
echo "FungiCloud - Inicio Rápido"
echo "======================================"

# Verificar Python
echo -e "\n[1/6] Verificando Python..."
python3 --version || { echo "Error: Python 3.9+ requerido"; exit 1; }

# Crear virtual environment
echo -e "\n[2/6] Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate || . venv/Scripts/activate

# Instalar dependencias
echo -e "\n[3/6] Instalando dependencias..."
pip install -r requirements.txt

# Verificar .env
echo -e "\n[4/6] Verificando configuración..."
if [ ! -f .env ]; then
    echo "⚠️  Advertencia: No existe .env"
    echo "Copiando .env.example a .env..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita .env con tus credenciales antes de continuar"
    read -p "Presiona ENTER cuando hayas configurado .env..."
fi

# Inicializar base de datos
echo -e "\n[5/6] Inicializando base de datos..."
python -c "from database import init_database; init_database()"

# Crear admin
echo -e "\n[6/6] ¿Deseas crear un usuario administrador? (s/n)"
read -r response
if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
    python create_admin.py
fi

echo -e "\n======================================"
echo "✅ FungiCloud listo para ejecutar"
echo "======================================"
echo -e "\nComandos útiles:"
echo "  Desarrollo:  python app.py"
echo "  Producción:  gunicorn -w 4 -b 0.0.0.0:5000 app:app"
echo ""
