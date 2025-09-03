import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logging import get_logger
from app.models import InfrastructureMetrics

logger = get_logger("infrawatch_client")


class InfraWatchClient:
    """Cliente para integração com a API do InfraWatch Backend"""
    
    def __init__(self):
        self.base_url = settings.infrawatch_api_url
        self.api_token = settings.infrawatch_api_token
        self.timeout = 30.0
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Faz uma requisição HTTP para a API do InfraWatch"""
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data, params=params)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data, params=params)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Timeout na requisição para {url}")
            raise Exception(f"Timeout na requisição para InfraWatch API")
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP na requisição para {url}: {e}")
            raise Exception(f"Erro na comunicação com InfraWatch API: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado na requisição para {url}: {e}")
            raise
    
    async def get_endpoints(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Busca todos os endpoints monitorados"""
        params = {"user_id": user_id} if user_id else None
        return await self._make_request("GET", "/api/endpoints", params=params)
    
    async def get_endpoint_data(self, endpoint_id: int) -> Dict[str, Any]:
        """Busca dados de um endpoint específico"""
        return await self._make_request("GET", f"/api/endpoints/{endpoint_id}/data")
    
    async def get_recent_metrics(
        self, 
        endpoint_id: Optional[int] = None,
        hours: int = 24
    ) -> List[InfrastructureMetrics]:
        """Busca métricas recentes dos endpoints"""
        
        since = datetime.now() - timedelta(hours=hours)
        params = {
            "since": since.isoformat(),
            "endpoint_id": endpoint_id
        }
        
        try:
            data = await self._make_request("GET", "/api/metrics/recent", params=params)
            
            metrics_list = []
            for item in data.get("metrics", []):
                metrics = InfrastructureMetrics(
                    endpoint_id=item.get("endpoint_id"),
                    endpoint_name=item.get("endpoint_name", "Unknown"),
                    metrics=item.get("metrics", {}),
                    timestamp=datetime.fromisoformat(item.get("timestamp", datetime.now().isoformat())),
                    status=item.get("status", "unknown")
                )
                metrics_list.append(metrics)
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Erro ao buscar métricas recentes: {e}")
            return []
    
    async def get_alerts(
        self, 
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Busca alertas do sistema"""
        
        params = {"limit": limit}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        
        try:
            return await self._make_request("GET", "/api/alerts", params=params)
        except Exception as e:
            logger.error(f"Erro ao buscar alertas: {e}")
            return []
    
    async def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Busca um alerta específico por ID"""
        try:
            return await self._make_request("GET", f"/api/alerts/{alert_id}")
        except Exception as e:
            logger.error(f"Erro ao buscar alerta {alert_id}: {e}")
            return None
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Busca informações de saúde geral do sistema"""
        try:
            return await self._make_request("GET", "/api/system/health")
        except Exception as e:
            logger.error(f"Erro ao buscar saúde do sistema: {e}")
            return {
                "status": "unknown",
                "endpoints_total": 0,
                "endpoints_online": 0,
                "alerts_active": 0,
                "last_update": datetime.now().isoformat()
            }
    
    async def get_performance_trends(
        self, 
        endpoint_id: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Busca tendências de performance"""
        
        params = {
            "days": days,
            "endpoint_id": endpoint_id
        }
        
        try:
            return await self._make_request("GET", "/api/analytics/trends", params=params)
        except Exception as e:
            logger.error(f"Erro ao buscar tendências: {e}")
            return {"trends": [], "summary": {}}
    
    async def get_infrastructure_overview(self) -> Dict[str, Any]:
        """Busca visão geral da infraestrutura"""
        try:
            # Busca dados em paralelo
            endpoints_task = self.get_endpoints()
            alerts_task = self.get_alerts(status="active")
            health_task = self.get_system_health()
            
            endpoints, alerts, health = await asyncio.gather(
                endpoints_task, alerts_task, health_task,
                return_exceptions=True
            )
            
            # Processa resultados
            total_endpoints = len(endpoints) if isinstance(endpoints, list) else 0
            active_alerts = len(alerts) if isinstance(alerts, list) else 0
            
            # Calcula estatísticas
            online_endpoints = 0
            if isinstance(endpoints, list):
                for endpoint in endpoints:
                    if endpoint.get("status") == "online":
                        online_endpoints += 1
            
            uptime_percentage = (online_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
            
            return {
                "total_endpoints": total_endpoints,
                "online_endpoints": online_endpoints,
                "offline_endpoints": total_endpoints - online_endpoints,
                "active_alerts": active_alerts,
                "uptime_percentage": round(uptime_percentage, 2),
                "health_status": health.get("status", "unknown") if isinstance(health, dict) else "unknown",
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar visão geral da infraestrutura: {e}")
            return {
                "total_endpoints": 0,
                "online_endpoints": 0,
                "offline_endpoints": 0,
                "active_alerts": 0,
                "uptime_percentage": 0.0,
                "health_status": "unknown",
                "last_update": datetime.now().isoformat()
            }
