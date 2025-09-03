import httpx
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.models import ChatMessage, AnalysisResponse, MessageType

logger = get_logger("gemini_service")


class GeminiService:
    """Serviço para integração com Google Gemini via API REST"""
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.model_name = "gemini-2.0-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self.timeout = 30.0
        
        logger.info(f"Gemini service inicializado com modelo {self.model_name}")
    
    async def _make_gemini_request(self, contents: List[Dict[str, Any]]) -> str:
        """Faz requisição para a API do Gemini"""
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": min(self.max_tokens, 8192),
                "topP": settings.top_p
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Erro na API Gemini ({response.status_code}): {error_detail}")
                    raise Exception(f"Gemini API error: {response.status_code}")
                
                result = response.json()
                
                # Extrai o texto da resposta
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            return parts[0]["text"]
                
                raise Exception("Resposta inválida da API Gemini")
                
        except httpx.TimeoutException:
            logger.error("Timeout na requisição para Gemini API")
            raise Exception("Timeout na comunicação com Gemini API")
        except Exception as e:
            logger.error(f"Erro na requisição Gemini: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Retorna o prompt do sistema para o contexto de infraestrutura"""
        return """Você é um assistente especializado em análise de infraestrutura de TI e monitoramento de sistemas. 

CONTEXTO:
- Você tem acesso a dados de monitoramento SNMP, métricas de sistemas, alertas e logs
- Seus usuários são administradores de sistemas, engenheiros de rede e profissionais de TI
- Você deve fornecer análises técnicas precisas, diagnósticos e recomendações práticas

ESPECIALIDADES:
- Análise de performance de servidores (CPU, memória, disk, rede)
- Diagnóstico de problemas de infraestrutura
- Interpretação de alertas e métricas SNMP
- Recomendações de otimização
- Análise preditiva de falhas
- Planejamento de capacidade
- Troubleshooting de conectividade

ESTILO DE RESPOSTA:
- Seja técnico mas acessível
- Use dados concretos quando disponível
- Forneça recomendações acionáveis
- Inclua possíveis causas e soluções
- Considere impacto nos negócios
- Sugira próximos passos quando apropriado

FORMATO DE SAÍDA:
- Respostas claras e estruturadas
- Use métricas e números quando relevante
- Inclua severidade/prioridade quando aplicável
- Forneça sugestões de ações quando possível

Responda sempre em português brasileiro de forma profissional e técnica."""
    
    async def generate_response(
        self, 
        user_query: str,
        retrieved_context: List[str] = None,
        infrastructure_data: Optional[Dict[str, Any]] = None,
        conversation_history: List[ChatMessage] = None
    ) -> AnalysisResponse:
        """Gera uma resposta usando o Gemini com contexto RAG"""
        
        try:
            # Prepara o contexto do sistema
            system_context = self._get_system_prompt()
            
            # Adiciona contexto RAG
            if retrieved_context:
                context_text = "\n".join(retrieved_context)
                system_context += f"\n\nCONTEXTO RELEVANTE ENCONTRADO:\n{context_text}"
            
            # Adiciona dados da infraestrutura
            if infrastructure_data:
                infrastructure_context = f"\n\nDADOS ATUAIS DA INFRAESTRUTURA:\n{json.dumps(infrastructure_data, indent=2, ensure_ascii=False)}"
                system_context += infrastructure_context
            
            # Prepara histórico da conversa
            chat_history_text = ""
            if conversation_history:
                history_messages = []
                for msg in conversation_history[-5:]:  # Últimas 5 mensagens
                    role = "Assistente" if msg.type == MessageType.ASSISTANT else "Usuário"
                    history_messages.append(f"{role}: {msg.message}")
                chat_history_text = "Histórico da conversa: " + "\n".join(history_messages)
            
            # Monta o conteúdo para a API
            contents = [
                {
                    "parts": [
                        {"text": system_context},
                        {"text": chat_history_text},
                        {"text": f"Usuário: {user_query}"}
                    ]
                }
            ]
            
            logger.info(f"Gerando resposta para query: {user_query[:100]}...")
            
            # Faz a requisição
            response_text = await self._make_gemini_request(contents)
            
            if not response_text or not response_text.strip():
                raise Exception("Resposta vazia do Gemini")
            
            # Extrai sugestões da resposta
            suggestions = self._extract_suggestions(response_text)
            
            # Calcula confiança
            confidence = self._calculate_confidence(response_text, retrieved_context or [])
            
            analysis_response = AnalysisResponse(
                answer=response_text,
                confidence=confidence,
                sources=[f"Gemini {self.model_name}", "InfraWatch Data"],
                suggestions=suggestions,
                metadata={
                    "model": self.model_name,
                    "temperature": self.temperature,
                    "context_items": len(retrieved_context) if retrieved_context else 0,
                    "has_infrastructure_data": infrastructure_data is not None
                }
            )
            
            logger.info("Resposta gerada com sucesso")
            return analysis_response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com Gemini: {e}")
            
            # Retorna uma resposta de fallback
            return AnalysisResponse(
                answer="Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente ou reformule sua pergunta.",
                confidence=0.0,
                sources=[],
                suggestions=["Tente reformular a pergunta", "Verifique a conectividade", "Consulte os logs do sistema"],
                metadata={"error": str(e)}
            )
    
    def _extract_suggestions(self, response_text: str) -> List[str]:
        """Extrai sugestões da resposta (heurística simples)"""
        suggestions = []
        
        # Procura por padrões comuns de sugestões
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recomendo', 'sugiro', 'deveria', 'pode', 'considere']):
                if len(line) < 100:  # Evita linhas muito longas
                    suggestions.append(line)
        
        # Sugestões padrão se nenhuma foi encontrada
        if not suggestions:
            suggestions = [
                "Ver métricas detalhadas",
                "Analisar logs do sistema", 
                "Verificar alertas recentes",
                "Revisar configurações"
            ]
        
        return suggestions[:4]  # Máximo 4 sugestões
    
    def _calculate_confidence(self, response_text: str, context: List[str]) -> float:
        """Calcula um score de confiança heurístico"""
        confidence = 50.0  # Base
        
        # Aumenta confiança com mais contexto
        confidence += min(len(context) * 5, 20)
        
        # Aumenta confiança com respostas mais detalhadas
        word_count = len(response_text.split())
        if word_count > 50:
            confidence += min(word_count / 10, 20)
        
        # Aumenta confiança se menciona dados específicos
        if any(keyword in response_text.lower() for keyword in ['cpu', 'memória', 'disk', 'rede', 'snmp', 'alert']):
            confidence += 10
        
        return min(confidence, 95.0)  # Máximo 95%
    
    async def analyze_metrics(
        self, 
        metrics_data: Dict[str, Any],
        analysis_type: str = "general"
    ) -> AnalysisResponse:
        """Analisa métricas específicas"""
        
        system_context = self._get_system_prompt()
        system_context += f"\n\nTIPO DE ANÁLISE: {analysis_type}"
        system_context += f"\n\nDADOS DE MÉTRICAS PARA ANÁLISE:\n{json.dumps(metrics_data, indent=2, ensure_ascii=False)}"
        
        analysis_prompt = """
Por favor, faça uma análise detalhada das métricas fornecidas, identificando:
1. Estado atual dos sistemas
2. Possíveis problemas ou anomalias
3. Tendências preocupantes
4. Recomendações específicas
5. Ações prioritárias necessárias

Forneça uma análise técnica mas compreensível, com foco em insights acionáveis.
"""
        
        contents = [
            {
                "parts": [
                    {"text": system_context},
                    {"text": analysis_prompt}
                ]
            }
        ]
        
        try:
            response_text = await self._make_gemini_request(contents)
            
            suggestions = self._extract_suggestions(response_text)
            confidence = self._calculate_confidence(response_text, [])
            
            return AnalysisResponse(
                answer=response_text,
                confidence=confidence,
                sources=[f"Gemini {self.model_name}", "Metrics Analysis"],
                suggestions=suggestions,
                metadata={
                    "analysis_type": analysis_type,
                    "metrics_count": len(metrics_data),
                    "model": self.model_name
                }
            )
            
        except Exception as e:
            logger.error(f"Erro na análise de métricas: {e}")
            return AnalysisResponse(
                answer="Erro ao analisar as métricas. Verifique os dados e tente novamente.",
                confidence=0.0,
                sources=[],
                suggestions=["Verificar dados de entrada", "Tentar análise manual"],
                metadata={"error": str(e)}
            )
    
    async def generate_insights_report(
        self, 
        infrastructure_overview: Dict[str, Any]
    ) -> AnalysisResponse:
        """Gera um relatório de insights automático"""
        
        system_context = self._get_system_prompt()
        system_context += f"\n\nDADOS GERAIS DA INFRAESTRUTURA:\n{json.dumps(infrastructure_overview, indent=2, ensure_ascii=False)}"
        
        report_prompt = """
Gere um relatório de insights automático que inclua:

1. **RESUMO EXECUTIVO**
   - Estado geral da infraestrutura
   - Principais pontos de atenção
   
2. **ANÁLISE DETALHADA**
   - Performance atual
   - Problemas identificados
   - Tendências observadas
   
3. **RECOMENDAÇÕES PRIORITÁRIAS**
   - Ações imediatas necessárias
   - Melhorias de médio prazo
   - Planejamento estratégico
   
4. **PREVISÕES E ALERTAS**
   - Possíveis problemas futuros
   - Necessidades de expansão
   - Pontos de monitoramento crítico

Mantenha o relatório técnico mas acessível, com foco em valor para tomada de decisão.
"""
        
        contents = [
            {
                "parts": [
                    {"text": system_context},
                    {"text": report_prompt}
                ]
            }
        ]
        
        try:
            response_text = await self._make_gemini_request(contents)
            
            suggestions = [
                "Exportar relatório completo",
                "Configurar monitoramento avançado",
                "Agendar revisão de infraestrutura",
                "Implementar automações recomendadas"
            ]
            
            confidence = self._calculate_confidence(response_text, [])
            
            return AnalysisResponse(
                answer=response_text,
                confidence=confidence,
                sources=[f"Gemini {self.model_name}", "Infrastructure Overview"],
                suggestions=suggestions,
                metadata={
                    "report_type": "insights",
                    "data_points": len(infrastructure_overview),
                    "generated_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de insights: {e}")
            return AnalysisResponse(
                answer="Erro ao gerar o relatório de insights. Verifique os dados da infraestrutura.",
                confidence=0.0,
                sources=[],
                suggestions=["Verificar dados de entrada", "Tentar geração manual"],
                metadata={"error": str(e)}
            )
