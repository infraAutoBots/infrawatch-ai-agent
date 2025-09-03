#!/bin/bash

# Script para setup completo do InfraWatch AI Agent

echo "🤖 INFRAWATCH AI AGENT - SETUP"
echo "================================"

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

echo "🐍 Python encontrado: $(python3 --version)"

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instala dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Copia arquivo .env se não existir
if [ ! -f ".env" ]; then
    echo "⚙️ Criando arquivo .env..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Configure sua GOOGLE_API_KEY no arquivo .env"
fi

# Inicializa base de conhecimento
echo "🧠 Inicializando base de conhecimento..."
python scripts/init_knowledge_base.py

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Próximos passos:"
echo "1. Configure sua GOOGLE_API_KEY no arquivo .env"
echo "2. Execute: ./start.sh ou python main.py"
echo "3. Acesse: http://localhost:8001/docs"
echo ""
