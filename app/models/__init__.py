from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class InsightType(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class ChatMessage:
    """Modelo para mensagens do chat"""
    
    def __init__(
        self,
        message: str,
        type: MessageType = MessageType.USER,
        timestamp: Optional[datetime] = None,
        suggestions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(hash(f"{message}{datetime.now().isoformat()}"))
        self.message = message
        self.type = type
        self.timestamp = timestamp or datetime.now()
        self.suggestions = suggestions or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message": self.message,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "suggestions": self.suggestions,
            "metadata": self.metadata
        }


class AIInsight:
    """Modelo para insights da IA"""
    
    def __init__(
        self,
        title: str,
        description: str,
        type: InsightType = InsightType.INFO,
        confidence: float = 0.0,
        recommendation: str = "",
        source_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.id = str(hash(f"{title}{datetime.now().isoformat()}"))
        self.title = title
        self.description = description
        self.type = type
        self.confidence = max(0.0, min(100.0, confidence))  # Garantir entre 0-100
        self.recommendation = recommendation
        self.source_data = source_data or {}
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "source_data": self.source_data,
            "timestamp": self.timestamp.isoformat()
        }


class AnalysisRequest:
    """Modelo para solicitações de análise"""
    
    def __init__(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: str = "general",
        include_predictions: bool = True,
        max_results: int = 10
    ):
        self.query = query
        self.context = context or {}
        self.analysis_type = analysis_type
        self.include_predictions = include_predictions
        self.max_results = max_results
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "context": self.context,
            "analysis_type": self.analysis_type,
            "include_predictions": self.include_predictions,
            "max_results": self.max_results
        }


class AnalysisResponse:
    """Modelo para respostas de análise"""
    
    def __init__(
        self,
        answer: str,
        insights: List[AIInsight] = None,
        confidence: float = 0.0,
        sources: List[str] = None,
        suggestions: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.answer = answer
        self.insights = insights or []
        self.confidence = confidence
        self.sources = sources or []
        self.suggestions = suggestions or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "insights": [insight.to_dict() for insight in self.insights],
            "confidence": self.confidence,
            "sources": self.sources,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class InfrastructureMetrics:
    """Modelo para métricas de infraestrutura"""
    
    def __init__(
        self,
        endpoint_id: int,
        endpoint_name: str,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        status: str = "unknown"
    ):
        self.endpoint_id = endpoint_id
        self.endpoint_name = endpoint_name
        self.metrics = metrics
        self.timestamp = timestamp or datetime.now()
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint_id": self.endpoint_id,
            "endpoint_name": self.endpoint_name,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }
