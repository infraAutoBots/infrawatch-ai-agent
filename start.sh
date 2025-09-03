#!/bin/bash

# Script para iniciar o InfraWatch AI Agent

echo "🚀 Iniciando InfraWatch AI Agent..."

# Verifica se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Execute ./setup.sh primeiro"
    exit 1
fi

# Ativa ambiente virtual
source venv/bin/activate

# Verifica se .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado. Execute ./setup.sh primeiro"
    exit 1
fi

# Inicia o servidor
python main.py
