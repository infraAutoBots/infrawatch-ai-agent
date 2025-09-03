from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from app.services.rag import RAGService
from app.core.logging import get_logger

logger = get_logger("insights_routes")

router = APIRouter(prefix="/api/insights", tags=["insights"])
rag_service = RAGService()


class InsightResponse(BaseModel):
    insights: List[Dict[str, Any]]
    timestamp: str
    total: int


@router.get("/", response_model=InsightResponse)
async def get_automatic_insights():
    """Endpoint para obter insights automáticos da IA"""
    
    try:
        logger.info("Gerando insights automáticos...")
        
        insights = await rag_service.generate_automatic_insights()
        
        insights_data = [insight.to_dict() for insight in insights]
        
        response = InsightResponse(
            insights=insights_data,
            timestamp=datetime.now().isoformat(),
            total=len(insights_data)
        )
        
        logger.info(f"Retornando {len(insights_data)} insights automáticos")
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar insights automáticos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


class ReportRequest(BaseModel):
    report_type: str = "general"
    include_predictions: bool = True


class ReportResponse(BaseModel):
    report: Dict[str, Any]
    timestamp: str


@router.post("/report", response_model=ReportResponse)
async def generate_insights_report(request: ReportRequest):
    """Gera um relatório detalhado de insights"""
    
    try:
        logger.info(f"Gerando relatório de insights tipo: {request.report_type}")
        
        # Busca overview da infraestrutura
        from app.services.infrawatch_client import InfraWatchClient
        infrawatch_client = InfraWatchClient()
        
        infrastructure_overview = await infrawatch_client.get_infrastructure_overview()
        
        # Gera relatório com Gemini
        from app.services.gemini import GeminiService
        gemini_service = GeminiService()
        
        report = await gemini_service.generate_insights_report(infrastructure_overview)
        
        response = ReportResponse(
            report=report.to_dict(),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("Relatório de insights gerado com sucesso")
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


class StatsResponse(BaseModel):
    vector_store_stats: Dict[str, Any]
    system_stats: Dict[str, Any]
    timestamp: str


@router.get("/stats", response_model=StatsResponse)
async def get_system_stats():
    """Retorna estatísticas do sistema de IA"""
    
    try:
        # Estatísticas do vector store
        vector_stats = await rag_service.vector_store.get_collection_stats()
        
        # Estatísticas do sistema
        from app.services.infrawatch_client import InfraWatchClient
        infrawatch_client = InfraWatchClient()
        
        system_overview = await infrawatch_client.get_infrastructure_overview()
        
        system_stats = {
            "infrawatch_connected": True,
            "gemini_model": "gemini-1.5-pro",
            "last_knowledge_update": vector_stats.get("last_updated"),
            **system_overview
        }
        
        response = StatsResponse(
            vector_store_stats=vector_stats,
            system_stats=system_stats,
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )
