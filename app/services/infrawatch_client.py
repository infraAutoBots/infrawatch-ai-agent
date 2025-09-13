import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from app.core.config import settings
from app.core.logging import get_logger
from app.models import InfrastructureMetrics

logger = get_logger("infrawatch_client")


class InfraWatchClient:
    """Cliente para integração com a API do InfraWatch Backend"""
    
    def __init__(self):
        self.base_url = settings.infrawatch_api_url
        self.timeout = 30.0
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        
        # Credenciais específicas do agente
        self.agent_email = settings.infrawatch_agent_email
        self.agent_password = settings.infrawatch_agent_password
        
    async def login(self) -> bool:
        """Faz login na API do InfraWatch e obtém o token de acesso"""
        
        if not self.agent_email or not self.agent_password:
            logger.error("Credenciais do agente não configuradas")
            return False
            
        try:
            login_data = {
                "email": self.agent_email,
                "password": self.agent_password
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get("access_token")
                    self._refresh_token = data.get("refresh_token")
                    
                    # Calcula quando o token expira (assumindo 30 minutos como padrão)
                    expires_in_minutes = 30  # Pode ser obtido da configuração
                    self._token_expires_at = datetime.now() + timedelta(minutes=expires_in_minutes - 5)  # 5 min de margem
                    
                    logger.info("Login realizado com sucesso no InfraWatch")
                    return True
                else:
                    logger.error(f"Falha no login: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro durante o login: {e}")
            return False
    
    async def refresh_access_token(self) -> bool:
        """Renova o token de acesso usando o refresh token"""
        
        if not self._refresh_token:
            logger.warning("Refresh token não disponível, realizando login completo")
            return await self.login()
        
        try:
            headers = {"Authorization": f"Bearer {self._refresh_token}"}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/auth/refresh",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get("access_token")
                    
                    # Atualiza o tempo de expiração
                    expires_in_minutes = 30
                    self._token_expires_at = datetime.now() + timedelta(minutes=expires_in_minutes - 5)
                    
                    logger.info("Token renovado com sucesso")
                    return True
                else:
                    logger.error(f"Falha na renovação do token: {response.status_code}")
                    # Se falha na renovação, tenta login completo
                    return await self.login()
                    
        except Exception as e:
            logger.error(f"Erro durante renovação do token: {e}")
            return await self.login()
    
    async def ensure_authenticated(self) -> bool:
        """Garante que o cliente está autenticado com token válido"""
        
        # Se não tem token, faz login
        if not self._access_token:
            return await self.login()
        
        # Se o token está próximo do vencimento, renova
        if self._token_expires_at and datetime.now() >= self._token_expires_at:
            logger.info("Token próximo do vencimento, renovando...")
            return await self.refresh_access_token()
        
        return True
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_on_auth_failure: bool = True
    ) -> Dict[str, Any]:
        """Faz uma requisição HTTP para a API do InfraWatch"""
        
        # Garante que está autenticado
        if not await self.ensure_authenticated():
            raise Exception("Falha na autenticação com a API do InfraWatch")
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        
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
                
                # Se recebeu 401/403 e deve tentar reautenticar
                if response.status_code in [401, 403] and retry_on_auth_failure:
                    logger.warning("Token inválido, tentando reautenticar...")
                    if await self.login():
                        # Tenta a requisição novamente com novo token
                        headers = {"Authorization": f"Bearer {self._access_token}"}
                        if method.upper() == "GET":
                            response = await client.get(url, headers=headers, params=params)
                        elif method.upper() == "POST":
                            response = await client.post(url, headers=headers, json=data, params=params)
                        elif method.upper() == "PUT":
                            response = await client.put(url, headers=headers, json=data, params=params)
                        elif method.upper() == "DELETE":
                            response = await client.delete(url, headers=headers, params=params)
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Timeout na requisição para {url}")
            raise Exception(f"Timeout na requisição para InfraWatch API")
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP na requisição para {url}: {e}")
            raise Exception(f"Erro na comunicação com InfraWatch API: {e}")
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP na requisição para {url}: {e}")
            raise Exception(f"Erro na comunicação com InfraWatch API: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado na requisição para {url}: {e}")
            raise
    
    async def get_endpoints(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Busca todos os endpoints monitorados"""
        try:
            data = await self._make_request("GET", "/monitor/status")
            # A rota /monitor/status retorna informações dos endpoints
            return data.get("endpoints", [])
        except Exception as e:
            logger.error(f"Erro ao buscar endpoints: {e}")
            return []
    
    async def get_endpoint_data(self, endpoint_ip: str) -> Dict[str, Any]:
        """Busca dados de um endpoint específico por IP"""
        try:
            return await self._make_request("GET", f"/monitor/{endpoint_ip}")
        except Exception as e:
            logger.error(f"Erro ao buscar dados do endpoint {endpoint_ip}: {e}")
            return {}
    
    async def get_endpoint_history(
        self, 
        endpoint_ip: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Busca histórico de dados dos endpoints"""
        
        try:
            params = {"hours": hours}
            if endpoint_ip:
                params["endpoint_ip"] = endpoint_ip
                
            data = await self._make_request("GET", "/monitor/history", params=params)
            return data.get("history", [])
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return []
    
    async def get_recent_metrics(
        self, 
        endpoint_ip: Optional[str] = None,
        hours: int = 24
    ) -> List[InfrastructureMetrics]:
        """Busca métricas recentes dos endpoints usando histórico"""
        
        try:
            history_data = await self.get_endpoint_history(endpoint_ip, hours)
            
            metrics_list = []
            for item in history_data:
                metrics = InfrastructureMetrics(
                    endpoint_id=item.get("endpoint_ip", "unknown"),
                    endpoint_name=item.get("nickname", "Unknown"),
                    metrics=item.get("data", {}),
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
        
        params = {"size": limit}
        if status:
            # Converte o status para minúsculo para compatibilidade com o backend
            params["status"] = status.lower()
        if severity:
            # Converte a severidade para minúsculo para compatibilidade com o backend
            params["severity"] = severity.lower()
        
        try:
            data = await self._make_request("GET", "/alerts/", params=params)
            return data.get("data", [])  # A API retorna os alertas no campo "data"
        except Exception as e:
            logger.error(f"Erro ao buscar alertas: {e}")
            return []
    
    async def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Busca um alerta específico por ID"""
        try:
            return await self._make_request("GET", f"/alerts/{alert_id}")
        except Exception as e:
            logger.error(f"Erro ao buscar alerta {alert_id}: {e}")
            return None
    
    async def get_alerts_stats(self) -> Dict[str, Any]:
        """Busca estatísticas de alertas"""
        try:
            return await self._make_request("GET", "/alerts/stats")
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas de alertas: {e}")
            return {"total": 0, "active": 0, "resolved": 0}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Busca informações de saúde geral do sistema"""
        try:
            # Combina dados de status e alertas para criar visão de saúde
            status_data = await self._make_request("GET", "/monitor/status")
            alerts_stats = await self.get_alerts_stats()
            
            endpoints = status_data.get("endpoints", [])
            total_endpoints = len(endpoints)
            online_endpoints = sum(1 for ep in endpoints if ep.get("status") == "online")
            
            return {
                "status": "healthy" if online_endpoints == total_endpoints else "degraded",
                "endpoints_total": total_endpoints,
                "endpoints_online": online_endpoints,
                "alerts_active": alerts_stats.get("active", 0),
                "last_update": datetime.now().isoformat()
            }
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
        endpoint_ip: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Busca tendências de performance através do histórico"""
        
        try:
            # Busca histórico de vários dias
            hours = days * 24
            history_data = await self.get_endpoint_history(endpoint_ip, hours)
            
            # Processa dados para extrair tendências
            trends = {
                "cpu_trend": [],
                "memory_trend": [],
                "uptime_trend": []
            }
            
            for item in history_data:
                data = item.get("data", {})
                timestamp = item.get("timestamp")
                
                if data.get("cpu"):
                    trends["cpu_trend"].append({
                        "timestamp": timestamp,
                        "value": data.get("cpu")
                    })
                
                if data.get("memory"):
                    trends["memory_trend"].append({
                        "timestamp": timestamp,
                        "value": data.get("memory")
                    })
            
            return {
                "trends": trends,
                "summary": {
                    "data_points": len(history_data),
                    "period_days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar tendências: {e}")
            return {"trends": [], "summary": {}}
    
    async def get_infrastructure_overview(self) -> Dict[str, Any]:
        """Busca visão geral da infraestrutura usando a nova rota otimizada"""
        try:
            # Usa a nova rota consolidada do backend
            response = await self._make_request("GET", "/monitor/overview")
            
            if response.get("success") and response.get("data"):
                data = response["data"]
                
                # Retorna no formato esperado pelo agente IA
                return {
                    "total_endpoints": data.get("total_endpoints", 0),
                    "online_endpoints": data.get("online_endpoints", 0),
                    "offline_endpoints": data.get("offline_endpoints", 0),
                    "uptime_percentage": data.get("uptime_percentage", 0.0),
                    "active_alerts": data.get("active_alerts", 0),
                    "alerts_by_severity": data.get("alerts_by_severity", {}),
                    "health_status": data.get("health_status", "unknown"),
                    "last_update": data.get("last_update"),
                    "summary": data.get("summary", {})
                }
            else:
                logger.warning("Resposta inválida da rota /monitor/overview, usando fallback")
                return await self._get_infrastructure_overview_fallback()
                
        except Exception as e:
            logger.error(f"Erro ao buscar overview otimizado: {e}")
            logger.info("Tentando método de fallback...")
            return await self._get_infrastructure_overview_fallback()
    
    async def _get_infrastructure_overview_fallback(self) -> Dict[str, Any]:
        """Método de fallback que combina múltiplas requisições e inclui dados dos monitors"""
        try:
            # Busca dados em paralelo usando as rotas corretas
            status_task = self._make_request("GET", "/monitor/status")
            alerts_task = self.get_alerts(status="active")  # Usando "active" em minúsculas
            
            status_data, alerts = await asyncio.gather(
                status_task, alerts_task,
                return_exceptions=True
            )
            
            # Processa dados de status
            monitors = []
            total_endpoints = 0
            online_endpoints = 0
            
            if isinstance(status_data, dict):
                monitors = status_data.get("monitors", [])
                total_endpoints = status_data.get("total", 0)
                online_endpoints = status_data.get("total_online", 0)
                offline_endpoints = status_data.get("total_offline", 0)
            
            # Processa alertas
            active_alerts = len(alerts) if isinstance(alerts, list) else 0
            
            # Calcula estatísticas
            uptime_percentage = (online_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
            
            # Determina status de saúde
            health_status = "healthy"
            if uptime_percentage < 50:
                health_status = "critical"
            elif uptime_percentage < 80:
                health_status = "degraded"
            elif active_alerts > 5:
                health_status = "warning"
            
            return {
                "total_endpoints": total_endpoints,
                "online_endpoints": online_endpoints,
                "offline_endpoints": offline_endpoints,
                "uptime_percentage": round(uptime_percentage, 2),
                "active_alerts": active_alerts,
                "health_status": health_status,
                "last_update": datetime.now().isoformat(),
                
                # Dados adicionais para análise preditiva
                "monitors": monitors,  # Dados completos dos monitors para análise detalhada
                "endpoints": [],  # Mantém compatibilidade
                "alerts": alerts if isinstance(alerts, list) else [],
                
                # Estatísticas detalhadas por status
                "summary": {
                    "availability_ratio": uptime_percentage / 100,
                    "critical_endpoints": [m for m in monitors if not m.get("data", {}).get("status", False)],
                    "high_latency_endpoints": [
                        m for m in monitors 
                        if m.get("data", {}).get("ping_rtt") and 
                        float(m.get("data", {}).get("ping_rtt", 0)) > 1000
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar visão geral da infraestrutura (fallback): {e}")
            return {
                "total_endpoints": 0,
                "online_endpoints": 0,
                "offline_endpoints": 0,
                "active_alerts": 0,
                "uptime_percentage": 0.0,
                "health_status": "unknown",
                "last_update": datetime.now().isoformat(),
                "monitors": [],
                "endpoints": [],
                "alerts": []
            }
    
    async def add_endpoint(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adiciona um novo endpoint para monitoramento"""
        try:
            return await self._make_request("POST", "/monitor", data=endpoint_data)
        except Exception as e:
            logger.error(f"Erro ao adicionar endpoint: {e}")
            raise
    
    async def update_endpoint(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza um endpoint existente"""
        try:
            return await self._make_request("PUT", "/monitor", data=endpoint_data)
        except Exception as e:
            logger.error(f"Erro ao atualizar endpoint: {e}")
            raise
    
    async def delete_endpoint(self, endpoint_ip: str) -> bool:
        """Remove um endpoint do monitoramento"""
        try:
            await self._make_request("DELETE", f"/monitor/{endpoint_ip}")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover endpoint {endpoint_ip}: {e}")
            return False
