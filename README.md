# InfraWatch AI Agent

Este é um agente de IA especializado em análise de infraestrutura que utiliza RAG (Retrieval Augmented Generation) com o modelo Google Gemini para fornecer insights inteligentes sobre dados de monitoramento.

## 🚀 Características

- **RAG com Gemini**: Integração com Google Gemini para análises contextuais
- **Vector Database**: ChromaDB para busca semântica de conhecimento
- **Integração Backend**: Conexão direta com a API do InfraWatch Backend
- **Análise em Tempo Real**: Processamento contínuo de métricas e alertas
- **Chat Inteligente**: Interface conversacional para consultas
- **Insights Automáticos**: Geração proativa de recomendações

## 📋 Pré-requisitos

- Python 3.8+
- Google Cloud API Key (Gemini)
- InfraWatch Backend rodando
- 4GB+ RAM recomendado

## 🛠️ Instalação

1. **Clone e navegue para o projeto:**
```bash
cd /home/kali/Desktop/infrawatch/infrawatch-ai-agent
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Execute as migrações:**
```bash
python -m app.database.init_db
```

## ⚙️ Configuração

### Google Gemini API
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Gere uma API Key
3. Configure no arquivo `.env`:
```
GOOGLE_API_KEY=sua_api_key_aqui
```

### InfraWatch Backend
Certifique-se que o backend está rodando em `http://localhost:8000`

## 🚀 Execução

```bash
python main.py
```

A API estará disponível em: `http://localhost:8001`

## 📚 Endpoints Principais

- `POST /chat` - Chat com a IA
- `GET /insights` - Insights automáticos
- `POST /analyze` - Análise específica
- `GET /health` - Status do serviço
- `GET /docs` - Documentação interativa

## 🏗️ Arquitetura

```
infrawatch-ai-agent/
├── app/
│   ├── core/           # Configurações e utilitários
│   ├── models/         # Modelos de dados
│   ├── services/       # Lógica de negócio
│   │   ├── rag/        # RAG e embeddings
│   │   ├── gemini/     # Integração Gemini
│   │   └── infrawatch/ # Integração backend
│   ├── api/           # Rotas da API
│   └── database/      # Configuração do banco
├── data/              # Dados e conhecimento
├── vector_db/         # Base vetorial
└── logs/             # Logs do sistema
```

## 🤖 Como Funciona

1. **Ingestão**: Coleta dados do InfraWatch Backend
2. **Processamento**: Cria embeddings e armazena no vector DB
3. **Query**: Usuário faz pergunta via chat
4. **Retrieval**: Busca informações relevantes no vector DB
5. **Generation**: Gemini gera resposta contextualizada
6. **Response**: Retorna insights e recomendações

## 📊 Casos de Uso

- Análise preditiva de falhas
- Recomendações de otimização
- Diagnóstico de problemas
- Relatórios automatizados
- Alertas inteligentes
- Planejamento de capacidade

## 🔧 Desenvolvimento

```bash
# Executar em modo desenvolvimento
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Executar testes
pytest

# Atualizar vector database
python scripts/update_knowledge_base.py
```

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.
