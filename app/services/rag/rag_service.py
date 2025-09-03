import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.services.rag.vector_store import VectorStore
from app.services.infrawatch_client import InfraWatchClient
from app.services.gemini import GeminiService
from app.models import AnalysisRequest, AnalysisResponse, ChatMessage, AIInsight, InsightType
from app.core.logging import get_logger

logger = get_logger("rag_service")


class RAGService:
    """Serviço principal de RAG (Retrieval Augmented Generation)"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.gemini_service = GeminiService()
        
        logger.info("RAG Service inicializado")
    
    async def process_query(
        self, 
        query: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        include_live_data: bool = True,
        infrawatch_client: Optional[InfraWatchClient] = None
    ) -> AnalysisResponse:
        """Processa uma query usando RAG com dados ao vivo"""
        
        try:
            logger.info(f"Processando query: {query[:100]}...")
            
            # 1. Busca contexto relevante no vector store
            context_task = self.vector_store.get_relevant_context(
                query, 
                max_context_length=1500,
                n_results=3
            )
            
            # 2. Busca dados ao vivo se solicitado e cliente disponível
            live_data_task = None
            if include_live_data and infrawatch_client:
                live_data_task = self._get_live_infrastructure_data(infrawatch_client)
            
            # Executa buscas em paralelo
            if live_data_task:
                context, live_data = await asyncio.gather(
                    context_task, live_data_task,
                    return_exceptions=True
                )
                
                if isinstance(live_data, Exception):
                    logger.warning(f"Erro ao buscar dados ao vivo: {live_data}")
                    live_data = None
            else:
                context = await context_task
                live_data = None
            
            if isinstance(context, Exception):
                logger.warning(f"Erro ao buscar contexto: {context}")
                context = []
            
            # 3. Gera resposta com Gemini
            response = await self.gemini_service.generate_response(
                user_query=query,
                retrieved_context=context,
                infrastructure_data=live_data,
                conversation_history=conversation_history
            )
            
            logger.info("Query processada com sucesso")
            return response
            
        except Exception as e:
            logger.error(f"Erro ao processar query: {e}")
            return AnalysisResponse(
                answer="Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
                confidence=0.0,
                sources=[],
                suggestions=["Tente reformular a pergunta", "Verifique a conectividade"],
                metadata={"error": str(e)}
            )
    
    async def _get_live_infrastructure_data(self, infrawatch_client: InfraWatchClient) -> Optional[Dict[str, Any]]:
        """Busca dados atuais da infraestrutura"""
        
        try:
            # Busca dados em paralelo
            overview_task = infrawatch_client.get_infrastructure_overview()
            alerts_task = infrawatch_client.get_alerts(status="active", limit=10)
            metrics_task = infrawatch_client.get_recent_metrics(hours=1)
            
            overview, alerts, recent_metrics = await asyncio.gather(
                overview_task, alerts_task, metrics_task,
                return_exceptions=True
            )
            
            # Processa resultados
            live_data = {
                "timestamp": datetime.now().isoformat(),
                "overview": overview if not isinstance(overview, Exception) else {},
                "active_alerts": alerts if not isinstance(alerts, Exception) else [],
                "recent_metrics": [m.to_dict() for m in recent_metrics] if not isinstance(recent_metrics, Exception) else []
            }
            
            return live_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados ao vivo: {e}")
            return None
    
    async def generate_automatic_insights(self, infrastructure_data: Optional[Dict[str, Any]] = None) -> List[AIInsight]:
        """Gera insights automáticos baseados nos dados atuais"""
        
        try:
            logger.info("Gerando insights automáticos...")
            
            insights = []
            
            # Se não temos dados da infraestrutura, gera insights genéricos
            if not infrastructure_data:
                insight = AIInsight(
                    title="Sistema de Monitoramento Desconectado",
                    description="Não foi possível conectar com o backend InfraWatch para obter dados atualizados",
                    type=InsightType.WARNING,
                    confidence=95.0,
                    recommendation="Verificar conectividade com o backend e credenciais de autenticação",
                    source_data={"connection_status": "disconnected"}
                )
                insights.append(insight)
                return insights
            
            # 1. Análise de alertas críticos
            active_alerts = infrastructure_data.get("active_alerts", 0)
            if active_alerts > 0:
                insight_type = InsightType.CRITICAL if active_alerts >= 5 else InsightType.WARNING
                insight = AIInsight(
                    title=f"{active_alerts} Alertas Ativos Detectados",
                    description=f"Sistema possui {active_alerts} alertas ativos que requerem atenção",
                    type=insight_type,
                    confidence=95.0,
                    recommendation="Revisar e resolver alertas ativos prioritariamente",
                    source_data={"active_alerts_count": active_alerts}
                )
                insights.append(insight)
            
            # 2. Análise de uptime
            uptime = infrastructure_data.get("uptime_percentage", 0)
            if uptime < 99.0:
                insight_type = InsightType.CRITICAL if uptime < 95.0 else InsightType.WARNING
                insight = AIInsight(
                    title="Uptime Abaixo do Esperado",
                    description=f"Disponibilidade atual de {uptime}% está abaixo do ideal (>99%)",
                    type=insight_type,
                    confidence=88.0,
                    recommendation="Investigar causa da indisponibilidade e implementar melhorias na estabilidade",
                    source_data={"current_uptime": uptime}
                )
                insights.append(insight)
            
            # 3. Análise de endpoints offline
            total_endpoints = infrastructure_data.get("total_endpoints", 0)
            offline_endpoints = infrastructure_data.get("offline_endpoints", 0)
            if offline_endpoints > 0:
                insight_type = InsightType.CRITICAL if offline_endpoints > total_endpoints * 0.2 else InsightType.WARNING
                insight = AIInsight(
                    title=f"{offline_endpoints} Endpoints Offline",
                    description=f"{offline_endpoints} de {total_endpoints} endpoints estão offline",
                    type=insight_type,
                    confidence=90.0,
                    recommendation="Investigar conectividade e status dos endpoints offline",
                    source_data={"offline_endpoints": offline_endpoints, "total_endpoints": total_endpoints}
                )
                insights.append(insight)
            
            # 4. Análise de crescimento
            if total_endpoints > 20:
                insight = AIInsight(
                    title="Infraestrutura em Crescimento",
                    description=f"Monitorando {total_endpoints} endpoints - considerar otimizações de escala",
                    type=InsightType.INFO,
                    confidence=75.0,
                    recommendation="Avaliar implementação de automações e ferramentas de gestão centralizada",
                    source_data={"total_endpoints": total_endpoints}
                )
                insights.append(insight)
            
            # 5. Insight positivo se tudo estiver bem
            if active_alerts == 0 and uptime >= 99.0 and offline_endpoints == 0:
                insight = AIInsight(
                    title="Sistema Operando Normalmente",
                    description="Todos os indicadores principais estão dentro dos parâmetros esperados",
                    type=InsightType.SUCCESS,
                    confidence=90.0,
                    recommendation="Manter rotinas de monitoramento e backups atualizados",
                    source_data=infrastructure_data
                )
                insights.append(insight)
            
            logger.info(f"Gerados {len(insights)} insights automáticos")
            return insights
            
        except Exception as e:
            logger.error(f"Erro ao gerar insights automáticos: {e}")
            return []
    
    async def update_knowledge_base(self) -> Dict[str, Any]:
        """Atualiza a base de conhecimento com dados recentes"""
        
        try:
            logger.info("Atualizando base de conhecimento...")
            
            # Busca dados recentes
            endpoints = await self.infrawatch_client.get_endpoints()
            recent_metrics = await self.infrawatch_client.get_recent_metrics(hours=24)
            alerts = await self.infrawatch_client.get_alerts(limit=50)
            
            documents_added = 0
            
            # Adiciona métricas recentes agrupadas por endpoint
            endpoint_metrics = {}
            for metric in recent_metrics:
                endpoint_id = metric.endpoint_id
                if endpoint_id not in endpoint_metrics:
                    endpoint_metrics[endpoint_id] = {
                        "endpoint_name": metric.endpoint_name,
                        "metrics": [],
                        "latest_status": metric.status
                    }
                endpoint_metrics[endpoint_id]["metrics"].append(metric.metrics)
            
            # Adiciona dados de cada endpoint
            for endpoint_id, data in endpoint_metrics.items():
                # Calcula médias das métricas
                avg_metrics = {}
                if data["metrics"]:
                    for key in ["hrProcessorLoad", "memTotalReal", "memAvailReal"]:
                        values = []
                        for m in data["metrics"]:
                            value = m.get(key)
                            if value and isinstance(value, str) and value.replace('%', '').replace('.', '').isdigit():
                                values.append(float(value.replace('%', '')))
                        
                        if values:
                            avg_metrics[key] = sum(values) / len(values)
                
                # Busca alertas relacionados ao endpoint
                related_alerts = [a for a in alerts if a.get("id_endpoint") == endpoint_id]
                
                # Adiciona ao vector store
                doc_id = await self.vector_store.add_infrastructure_data(
                    endpoint_name=data["endpoint_name"],
                    metrics=avg_metrics,
                    alerts=related_alerts
                )
                
                documents_added += 1
            
            # Persiste as mudanças
            self.vector_store.persist()
            
            stats = await self.vector_store.get_collection_stats()
            
            result = {
                "success": True,
                "documents_added": documents_added,
                "total_documents": stats.get("total_documents", 0),
                "endpoints_processed": len(endpoint_metrics),
                "alerts_processed": len(alerts),
                "updated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Base de conhecimento atualizada: {documents_added} documentos adicionados")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao atualizar base de conhecimento: {e}")
            return {
                "success": False,
                "error": str(e),
                "updated_at": datetime.now().isoformat()
            }
    
    async def analyze_specific_metric(
        self, 
        endpoint_name: str, 
        metric_name: str,
        time_window_hours: int = 24,
        infrawatch_client: Optional[InfraWatchClient] = None
    ) -> AnalysisResponse:
        """Analisa uma métrica específica de um endpoint"""
        
        try:
            if not infrawatch_client:
                return AnalysisResponse(
                    answer="Não foi possível analisar a métrica: conexão com InfraWatch não disponível.",
                    confidence=0.0,
                    sources=[],
                    suggestions=[
                        "Verificar conectividade com o backend InfraWatch",
                        "Verificar credenciais de autenticação"
                    ]
                )
            
            # Busca dados históricos
            recent_metrics = await infrawatch_client.get_recent_metrics(endpoint_ip=endpoint_name, hours=time_window_hours)
            
            # Filtra métricas do endpoint específico
            endpoint_metrics = [m for m in recent_metrics if m.endpoint_name.lower() == endpoint_name.lower()]
            
            if not endpoint_metrics:
                return AnalysisResponse(
                    answer=f"Nenhuma métrica encontrada para o endpoint '{endpoint_name}' nas últimas {time_window_hours} horas.",
                    confidence=0.0,
                    sources=[],
                    suggestions=[
                        "Verificar se o nome do endpoint está correto",
                        "Verificar se o endpoint está ativo",
                        "Tentar um período de tempo maior"
                    ]
                )
            
            # Prepara dados para análise
            metric_values = []
            for m in endpoint_metrics:
                value = m.metrics.get(metric_name)
                if value:
                    metric_values.append({
                        "timestamp": m.timestamp.isoformat(),
                        "value": value,
                        "status": m.status
                    })
            
            analysis_data = {
                "endpoint_name": endpoint_name,
                "metric_name": metric_name,
                "time_window_hours": time_window_hours,
                "data_points": len(metric_values),
                "metric_values": metric_values[-20:]  # Últimos 20 pontos
            }
            
            # Gera análise com Gemini
            response = await self.gemini_service.analyze_metrics(
                analysis_data, 
                analysis_type=f"specific_metric_{metric_name}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao analisar métrica específica: {e}")
            return AnalysisResponse(
                answer="Erro ao analisar a métrica solicitada. Verifique os parâmetros e tente novamente.",
                confidence=0.0,
                sources=[],
                suggestions=["Verificar conectividade", "Tentar análise geral"],
                metadata={"error": str(e)}
            )
