from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.rag import RAGService
from app.services.auth_service import get_infrawatch_client
from app.services.infrawatch_client import InfraWatchClient
from app.models import ChatMessage, MessageType
from app.core.logging import get_logger

logger = get_logger("chat_routes")

router = APIRouter(prefix="/api/chat", tags=["chat"])
rag_service = RAGService()


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = None
    include_live_data: bool = True


class ChatResponse(BaseModel):
    response: Dict[str, Any]
    conversation_id: Optional[str] = None
    timestamp: str


@router.post("/", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    client: Optional[InfraWatchClient] = Depends(get_infrawatch_client)
):
    """Endpoint para chat com a IA"""
    
    try:
        logger.info(f"Recebida mensagem de chat: {request.message[:100]}...")
        
        # Converte histórico de conversa se fornecido
        conversation_history = []
        if request.conversation_history:
            for msg_data in request.conversation_history:
                message = ChatMessage(
                    message=msg_data.get("message", ""),
                    type=MessageType(msg_data.get("type", "user")),
                    timestamp=datetime.fromisoformat(msg_data.get("timestamp", datetime.now().isoformat())),
                    suggestions=msg_data.get("suggestions", []),
                    metadata=msg_data.get("metadata", {})
                )
                conversation_history.append(message)
        
        # Processa a query com RAG, incluindo cliente autenticado se disponível
        response = await rag_service.process_query(
            query=request.message,
            conversation_history=conversation_history,
            include_live_data=request.include_live_data,
            infrawatch_client=client
        )
        
        # Formata resposta para incluir sugestões como ChatMessage
        chat_response = ChatResponse(
            response=response.to_dict(),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("Resposta do chat gerada com sucesso")
        return chat_response
        
    except Exception as e:
        logger.error(f"Erro no endpoint de chat: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno do servidor: {str(e)}"
        )


class QuickAnalysisRequest(BaseModel):
    endpoint_name: str
    metric_name: str
    time_window_hours: Optional[int] = 24


@router.post("/analyze-metric", response_model=ChatResponse)
async def analyze_metric(
    request: QuickAnalysisRequest,
    client: Optional[InfraWatchClient] = Depends(get_infrawatch_client)
):
    """Endpoint para análise rápida de uma métrica específica"""
    
    try:
        logger.info(f"Análise de métrica solicitada: {request.endpoint_name}.{request.metric_name}")
        
        response = await rag_service.analyze_specific_metric(
            endpoint_name=request.endpoint_name,
            metric_name=request.metric_name,
            time_window_hours=request.time_window_hours,
            infrawatch_client=client
        )
        
        chat_response = ChatResponse(
            response=response.to_dict(),
            timestamp=datetime.now().isoformat()
        )
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Erro na análise de métrica: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno do servidor: {str(e)}"
        )
        logger.error(f"Erro na análise de métrica: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/update-knowledge")
async def update_knowledge_base(background_tasks: BackgroundTasks):
    """Endpoint para atualizar a base de conhecimento"""
    
    def update_kb():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(rag_service.update_knowledge_base())
            logger.info(f"Base de conhecimento atualizada: {result}")
        finally:
            loop.close()
    
    background_tasks.add_task(update_kb)
    
    return {
        "message": "Atualização da base de conhecimento iniciada em segundo plano",
        "timestamp": datetime.now().isoformat()
    }


class SuggestionResponse(BaseModel):
    suggestions: List[str]
    timestamp: str


@router.get("/suggestions", response_model=SuggestionResponse)
async def get_chat_suggestions():
    """Retorna sugestões de perguntas para o chat"""
    
    suggestions = [
        "Como está a performance geral dos servidores?",
        "Quais são os alertas críticos ativos?",
        "Analise o uso de CPU dos últimos dias",
        "Há algum problema de memória nos endpoints?",
        "Gere um relatório de saúde da infraestrutura",
        "Qual servidor tem maior uso de disk?",
        "Identifique tendências de crescimento",
        "Quais otimizações você recomenda?",
        "Analise os padrões de uptime",
        "Prever possíveis falhas"
    ]
    
    return SuggestionResponse(
        suggestions=suggestions,
        timestamp=datetime.now().isoformat()
    )
