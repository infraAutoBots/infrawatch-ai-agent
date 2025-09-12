from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.predictive_service import PredictiveService
from app.services.gemini import GeminiService
from app.services.auth_service import get_infrawatch_client
from app.services.infrawatch_client import InfraWatchClient
from app.models import (
    PredictiveAlert, PredictiveConfig, PredictiveAnalysisRequest, 
    PredictiveAnalysisResponse, AIInsight, InsightType
)
from app.core.logging import get_logger

logger = get_logger("predictive_routes")

router = APIRouter(prefix="/api/predictive", tags=["predictive-analytics"])
predictive_service = PredictiveService()
gemini_service = GeminiService()


class PredictiveAnalysisRequestAPI(BaseModel):
    """Modelo de request para análise preditiva via API"""
    confidence_threshold: float = 70.0
    prediction_window: str = "24h"
    analysis_type: str = "performance"
    real_time_enabled: bool = False
    time_range: str = "24h"
    endpoints: Optional[List[str]] = []
    include_live_data: bool = True
    max_alerts: int = 10


class PredictiveAnalysisResponseAPI(BaseModel):
    """Modelo de response para análise preditiva via API"""
    alerts: List[Dict[str, Any]]
    summary: str
    insights: List[Dict[str, Any]]
    confidence: float
    trends: Dict[str, Any]
    recommendations: List[str]
    timestamp: str
    metadata: Dict[str, Any]


@router.post("/analyze", response_model=PredictiveAnalysisResponseAPI)
async def generate_predictive_analysis(
    request: PredictiveAnalysisRequestAPI,
    client: Optional[InfraWatchClient] = Depends(get_infrawatch_client)
):
    """Endpoint principal para análise preditiva da infraestrutura"""
    
    try:
        logger.info(f"Iniciando análise preditiva com threshold {request.confidence_threshold}%")
        
        # Cria configuração de análise
        config = PredictiveConfig(
            confidence_threshold=request.confidence_threshold,
            prediction_window=request.prediction_window,
            analysis_type=request.analysis_type,
            real_time_enabled=request.real_time_enabled,
            time_range=request.time_range,
            endpoints=request.endpoints or []
        )
        
        # Busca dados da infraestrutura se cliente disponível
        infrastructure_data = None
        if client and request.include_live_data:
            try:
                infrastructure_data = await client.get_infrastructure_overview()
                logger.info("Dados da infraestrutura obtidos com sucesso")
            except Exception as e:
                logger.warning(f"Falha ao buscar dados da infraestrutura: {e}")
        
        # Executa análise preditiva usando o serviço
        alerts = await predictive_service.analyze_predictive_patterns(
            infrastructure_data, config
        )
        
        # Gera análise avançada com Gemini AI
        gemini_analysis = await gemini_service.generate_predictive_analysis(
            infrastructure_data, config.to_dict()
        )
        
        # Combina resultados do serviço preditivo com análise do Gemini
        combined_summary = f"{gemini_analysis.get('summary', 'Análise preditiva concluída')}. {len(alerts)} alertas preditivos gerados."
        
        # Converte alertas preditivos para insights
        predictive_insights = []
        for alert in alerts:
            insight = AIInsight(
                title=f"Alerta Preditivo: {alert.predicted_issue}",
                description=f"Endpoint {alert.endpoint} - Probabilidade: {alert.probability}%",
                type=InsightType.WARNING if alert.probability >= 80 else InsightType.INFO,
                confidence=alert.probability,
                recommendation=f"Ação recomendada em {alert.estimated_time}: {', '.join(alert.suggested_actions[:2])}"
            )
            predictive_insights.append(insight)
        
        # Combina recomendações
        all_recommendations = gemini_analysis.get('recommendations', [])
        for alert in alerts[:3]:  # Top 3 alertas
            all_recommendations.extend(alert.suggested_actions[:1])
        
        # Remove duplicatas de recomendações
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        # Calcula confiança geral
        overall_confidence = gemini_analysis.get('confidence', 75)
        if alerts:
            alert_confidence = sum(alert.probability for alert in alerts) / len(alerts)
            overall_confidence = (overall_confidence + alert_confidence) / 2
        
        # Monta response
        response = PredictiveAnalysisResponseAPI(
            alerts=[alert.to_dict() for alert in alerts],
            summary=combined_summary,
            insights=[insight.to_dict() for insight in predictive_insights],
            confidence=round(overall_confidence, 1),
            trends=gemini_analysis.get('trends', {}),
            recommendations=unique_recommendations[:5],  # Limita a 5 recomendações
            timestamp=datetime.now().isoformat(),
            metadata={
                "config": config.to_dict(),
                "gemini_analysis": True,
                "infrastructure_data_available": infrastructure_data is not None,
                "total_alerts": len(alerts),
                "high_priority_alerts": len([a for a in alerts if a.probability >= 80])
            }
        )
        
        logger.info(f"Análise preditiva concluída: {len(alerts)} alertas, confiança {overall_confidence:.1f}%")
        return response
        
    except Exception as e:
        logger.error(f"Erro na análise preditiva: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na análise preditiva: {str(e)}"
        )


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_predictive_alerts(
    confidence_threshold: float = 70.0,
    max_results: int = 10,
    client: Optional[InfraWatchClient] = Depends(get_infrawatch_client)
):
    """Endpoint simplificado para obter apenas alertas preditivos"""
    
    try:
        logger.info(f"Buscando alertas preditivos com threshold {confidence_threshold}%")
        
        # Configuração padrão
        config = PredictiveConfig(confidence_threshold=confidence_threshold)
        
        # Busca dados da infraestrutura
        infrastructure_data = None
        if client:
            try:
                infrastructure_data = await client.get_infrastructure_overview()
            except Exception as e:
                logger.warning(f"Falha ao buscar dados da infraestrutura: {e}")
        
        # Gera alertas preditivos
        alerts = await predictive_service.analyze_predictive_patterns(
            infrastructure_data, config
        )
        
        # Limita resultados
        limited_alerts = alerts[:max_results]
        
        logger.info(f"Retornando {len(limited_alerts)} alertas preditivos")
        return [alert.to_dict() for alert in limited_alerts]
        
    except Exception as e:
        logger.error(f"Erro ao buscar alertas preditivos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao buscar alertas: {str(e)}"
        )


@router.get("/config", response_model=Dict[str, Any])
async def get_default_config():
    """Retorna configuração padrão para análise preditiva"""
    
    try:
        default_config = PredictiveConfig()
        
        return {
            "default_config": default_config.to_dict(),
            "available_windows": ["1h", "6h", "24h", "72h", "168h"],
            "available_types": ["performance", "predictive", "comparative", "anomaly"],
            "threshold_range": {"min": 50, "max": 100},
            "description": "Configurações padrão para análise preditiva de infraestrutura"
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração padrão: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.post("/trends", response_model=Dict[str, Any])
async def analyze_trends(
    time_range: str = "24h",
    metrics: Optional[List[str]] = None,
    client: Optional[InfraWatchClient] = Depends(get_infrawatch_client)
):
    """Analisa tendências específicas em métricas da infraestrutura"""
    
    try:
        logger.info(f"Analisando tendências para período {time_range}")
        
        # Busca dados recentes
        infrastructure_data = None
        if client:
            try:
                infrastructure_data = await client.get_infrastructure_overview()
            except Exception as e:
                logger.warning(f"Falha ao buscar dados: {e}")
        
        # Análise básica de tendências
        trends_analysis = {
            "time_range": time_range,
            "metrics_analyzed": metrics or ["cpu_usage", "memory_usage", "response_time"],
            "overall_trend": "stable",
            "risk_indicators": [],
            "recommendations": []
        }
        
        if infrastructure_data:
            endpoints = infrastructure_data.get("endpoints", [])
            
            # Verifica indicadores de risco
            high_cpu_endpoints = []
            high_memory_endpoints = []
            
            for endpoint in endpoints:
                endpoint_data = endpoint.get("data", {})
                endpoint_name = endpoint.get("name", "Unknown")
                
                cpu_usage = endpoint_data.get("cpu_usage", 0)
                memory_usage = endpoint_data.get("memory_usage", 0)
                
                if cpu_usage > 80:
                    high_cpu_endpoints.append(endpoint_name)
                    trends_analysis["risk_indicators"].append(f"Alto CPU em {endpoint_name}: {cpu_usage}%")
                
                if memory_usage > 85:
                    high_memory_endpoints.append(endpoint_name)
                    trends_analysis["risk_indicators"].append(f"Alta memória em {endpoint_name}: {memory_usage}%")
            
            # Determina tendência geral
            if high_cpu_endpoints or high_memory_endpoints:
                trends_analysis["overall_trend"] = "declining"
                trends_analysis["recommendations"].extend([
                    "Monitorar recursos críticos",
                    "Considerar otimização de performance",
                    "Verificar aplicações com alto consumo"
                ])
            else:
                trends_analysis["overall_trend"] = "stable"
                trends_analysis["recommendations"].append("Continuar monitoramento regular")
        
        trends_analysis["timestamp"] = datetime.now().isoformat()
        trends_analysis["data_available"] = infrastructure_data is not None
        
        logger.info(f"Análise de tendências concluída: {trends_analysis['overall_trend']}")
        return trends_analysis
        
    except Exception as e:
        logger.error(f"Erro na análise de tendências: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na análise: {str(e)}"
        )