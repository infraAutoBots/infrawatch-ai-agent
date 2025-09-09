# ✅ Checklist de Deploy - InfraWatch AI Agent

## 📋 Pré-Deploy (Desenvolvimento)

- [ ] Testado localmente com `python main.py`
- [ ] Todas as dependências estão no `requirements.txt`
- [ ] Arquivo `runtime.txt` especifica versão correta do Python
- [ ] `Procfile` configurado corretamente
- [ ] Credenciais removidas do código (não hardcoded)
- [ ] Configurações de produção no `config.py`
- [ ] Script de validação executado: `python validate_deploy.py`

## 🔧 Arquivos de Deploy

- [ ] `Procfile` - Define comando de inicialização
- [ ] `requirements.txt` - Lista todas as dependências
- [ ] `runtime.txt` - Especifica versão do Python
- [ ] `railway.json` - Configurações específicas do Railway
- [ ] `.env.example` - Template das variáveis de ambiente

## 🌐 Configuração do Railway

### 1. Criação do Projeto
- [ ] Conta criada no Railway
- [ ] Repositório conectado ao Railway
- [ ] Build configurado (automático via Nixpacks)

### 2. Variáveis de Ambiente Obrigatórias
- [ ] `GOOGLE_API_KEY` - Chave da API do Google Gemini
- [ ] `INFRAWATCH_AGENT_EMAIL` - Email do agente
- [ ] `INFRAWATCH_AGENT_PASSWORD` - Senha do agente

### 3. Variáveis de Ambiente Recomendadas
- [ ] `DEBUG=False` - Desabilita modo debug
- [ ] `LOG_LEVEL=INFO` - Nível de log para produção
- [ ] `INFRAWATCH_API_URL` - URL do backend (se diferente do padrão)

## 🚀 Deploy

- [ ] Push das mudanças para o repositório
- [ ] Build iniciado automaticamente no Railway
- [ ] Build concluído com sucesso
- [ ] Aplicação iniciada sem erros
- [ ] URL da aplicação disponível

## 🧪 Pós-Deploy (Testes)

### Health Check
- [ ] `GET /health` retorna status 200
- [ ] Logs não mostram erros críticos

### Funcionalidades Core
- [ ] `POST /api/chat` funciona corretamente
- [ ] Integração com Gemini funcionando
- [ ] Conexão com InfraWatch Backend estabelecida
- [ ] Sistema de autenticação operacional

### Performance
- [ ] Tempo de resposta aceitável (<5s para chat simples)
- [ ] Aplicação não está crashando
- [ ] Uso de memória dentro dos limites

## 🔄 Monitoramento Contínuo

- [ ] Logs configurados e sendo coletados
- [ ] Métricas de performance monitoradas
- [ ] Alertas configurados para falhas
- [ ] Backup/restore testado

## 🆘 Rollback Plan

Em caso de problemas:
- [ ] Procedimento de rollback documentado
- [ ] Backup da versão anterior disponível
- [ ] Contatos de emergência definidos

## 📝 Documentação

- [ ] `README.md` atualizado com instruções de deploy
- [ ] `RAILWAY_DEPLOY.md` contém guia completo
- [ ] Variáveis de ambiente documentadas
- [ ] Endpoints da API documentados

## 🎯 Critérios de Sucesso

- [ ] ✅ Aplicação responde em menos de 30 segundos após deploy
- [ ] ✅ Chat com IA funcionando corretamente
- [ ] ✅ Integração com backend estabelecida
- [ ] ✅ Logs não mostram erros críticos
- [ ] ✅ Todas as rotas da API respondem corretamente

---

**Status**: ⏳ Em Progresso | ✅ Concluído | ❌ Falhou

**Data do Deploy**: _________________

**Responsável**: _________________

**URL da Aplicação**: _________________
