# 🚀 Deploy InfraWatch AI Agent no Railway

## 📋 Pré-requisitos

1. **Conta no Railway**: [railway.app](https://railway.app)
2. **Google API Key**: Chave da API do Google Gemini
3. **Backend InfraWatch**: URL do backend em produção

## 🛠️ Configuração das Variáveis de Ambiente

No Railway, configure as seguintes variáveis de ambiente:

### 🔑 Obrigatórias
```bash
GOOGLE_API_KEY=sua_chave_da_api_do_google
INFRAWATCH_AGENT_EMAIL=seu_email_do_agente
INFRAWATCH_AGENT_PASSWORD=sua_senha_do_agente
```

### 🌐 Configurações de Produção
```bash
DEBUG=False
INFRAWATCH_API_URL=https://infrawatch-backend-production.up.railway.app
LOG_LEVEL=INFO
```

### ⚙️ Opcionais (valores padrão funcionam)
```bash
GEMINI_MODEL=gemini-2.0-flash
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_TOKENS=4096
TEMPERATURE=0.7
TOP_P=0.9
CACHE_TTL=300
MAX_REQUESTS_PER_MINUTE=60
```

## 🚀 Passos para Deploy

1. **Faça fork/clone do repositório**
2. **Conecte ao Railway**:
   - Acesse [railway.app](https://railway.app)
   - Faça login com GitHub
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Escolha este repositório

3. **Configure as variáveis de ambiente**:
   - No dashboard do Railway, vá para a aba "Variables"
   - Adicione as variáveis obrigatórias listadas acima

4. **Deploy automático**:
   - O Railway detectará automaticamente o `Procfile`
   - O build começará automaticamente
   - Em alguns minutos, sua aplicação estará online

## 📊 Verificação do Deploy

Após o deploy, você pode testar:

1. **Health Check**:
   ```bash
   curl https://seu-dominio.railway.app/health
   ```

2. **Chat Endpoint**:
   ```bash
   curl -X POST https://seu-dominio.railway.app/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Olá, como você pode me ajudar?"}'
   ```

## 🔧 Estrutura de Arquivos para Deploy

- `Procfile` - Define como iniciar a aplicação
- `requirements.txt` - Dependências Python
- `runtime.txt` - Versão do Python
- `railway.json` - Configurações específicas do Railway

## 🐛 Troubleshooting

### Problema: API Key não configurada
```
❌ GOOGLE_API_KEY não configurada!
```
**Solução**: Configure a variável `GOOGLE_API_KEY` no Railway

### Problema: Erro de conexão com backend
```
❌ Erro ao conectar com InfraWatch Backend
```
**Solução**: Verifique se `INFRAWATCH_API_URL` está correto

### Problema: Timeout ou erro de memória
**Solução**: 
- Verifique os logs no Railway
- Considere otimizar o modelo ou aumentar recursos

## 📝 Logs

Para visualizar logs:
1. Acesse o dashboard do Railway
2. Clique no seu projeto
3. Vá para a aba "Deployments"
4. Clique no deployment ativo
5. Visualize os logs em tempo real

## 🔄 Atualizações

Para atualizar a aplicação:
1. Faça push das mudanças para o repositório
2. O Railway fará deploy automático
3. A aplicação será atualizada em alguns minutos

## 🌟 Features Incluídas

- ✅ Chat com IA usando Google Gemini
- ✅ RAG (Retrieval Augmented Generation)
- ✅ Integração com InfraWatch Backend
- ✅ Sistema de logging
- ✅ Autenticação
- ✅ API REST completa

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs no Railway
2. Confirme as variáveis de ambiente
3. Teste localmente primeiro
4. Consulte a documentação do InfraWatch
