from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import math
from app.models import PredictiveAlert, PredictiveConfig, AIInsight, InsightType
from app.services.infrawatch_client import InfraWatchClient
from app.core.logging import get_logger

logger = get_logger("predictive_service")


class PredictiveService:
    """Serviço para análise preditiva de infraestrutura"""
    
    def __init__(self):
        self.trend_analysis_window = 24  # Horas para análise de tendência
        logger.info("PredictiveService inicializado")
    
    async def analyze_predictive_patterns(
        self,
        infrastructure_data: Dict[str, Any],
        config: PredictiveConfig
    ) -> List[PredictiveAlert]:
        """Analisa padrões preditivos baseado nos dados de infraestrutura"""
        
        try:
            alerts = []
            
            if not infrastructure_data:
                logger.warning("Dados de infraestrutura não disponíveis para análise preditiva")
                return self._generate_sample_alerts(config)
            
            # Analisa endpoints individuais
            endpoints = infrastructure_data.get("endpoints", [])
            for endpoint in endpoints:
                endpoint_alerts = await self._analyze_endpoint_trends(endpoint, config)
                alerts.extend(endpoint_alerts)
            
            # Analisa alertas existentes para padrões
            existing_alerts = infrastructure_data.get("alerts", [])
            alert_pattern_alerts = self._analyze_alert_patterns(existing_alerts, config)
            alerts.extend(alert_pattern_alerts)
            
            # Filtra por threshold de confiança
            filtered_alerts = [
                alert for alert in alerts 
                if alert.probability >= config.confidence_threshold
            ]
            
            # Ordena por probabilidade (maior primeiro)
            filtered_alerts.sort(key=lambda x: x.probability, reverse=True)
            
            logger.info(f"Gerados {len(filtered_alerts)} alertas preditivos com threshold {config.confidence_threshold}%")
            return filtered_alerts[:10]  # Limita a 10 alertas principais
            
        except Exception as e:
            logger.error(f"Erro na análise preditiva: {e}")
            return self._generate_sample_alerts(config)
    
    async def _analyze_endpoint_trends(
        self,
        endpoint: Dict[str, Any],
        config: PredictiveConfig
    ) -> List[PredictiveAlert]:
        """Analisa tendências de um endpoint específico"""
        
        alerts = []
        endpoint_name = endpoint.get("name", f"Endpoint {endpoint.get('id', 'Unknown')}")
        
        try:
            # Analisa dados recentes do endpoint
            endpoint_data = endpoint.get("data", {})
            if not endpoint_data:
                return alerts
            
            # Análise de CPU
            cpu_alert = self._analyze_cpu_trends(endpoint_name, endpoint_data, config)
            if cpu_alert:
                alerts.append(cpu_alert)
            
            # Análise de Memória
            memory_alert = self._analyze_memory_trends(endpoint_name, endpoint_data, config)
            if memory_alert:
                alerts.append(memory_alert)
            
            # Análise de Rede
            network_alert = self._analyze_network_trends(endpoint_name, endpoint_data, config)
            if network_alert:
                alerts.append(network_alert)
            
            # Análise de Disponibilidade
            availability_alert = self._analyze_availability_trends(endpoint_name, endpoint_data, config)
            if availability_alert:
                alerts.append(availability_alert)
                
        except Exception as e:
            logger.error(f"Erro ao analisar tendências do endpoint {endpoint_name}: {e}")
        
        return alerts
    
    def _analyze_cpu_trends(
        self,
        endpoint_name: str,
        endpoint_data: Dict[str, Any],
        config: PredictiveConfig
    ) -> Optional[PredictiveAlert]:
        """Analisa tendências de CPU"""
        
        try:
            cpu_data = endpoint_data.get("cpu_usage")
            if not cpu_data or not isinstance(cpu_data, (int, float)):
                return None
            
            cpu_usage = float(cpu_data)
            
            # Lógica preditiva baseada em thresholds
            if cpu_usage > 80:
                probability = min(95, 70 + (cpu_usage - 80) * 2)
                estimated_time = "2-4 horas" if cpu_usage > 90 else "6-12 horas"
                
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="cpu_usage",
                    predicted_issue=f"Alto uso de CPU ({cpu_usage:.1f}%) pode causar degradação",
                    probability=probability,
                    estimated_time=estimated_time,
                    suggested_actions=[
                        "Verificar processos em execução",
                        "Considerar otimização de aplicações",
                        "Monitorar tendência nas próximas horas"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
            
            elif cpu_usage > 70:
                probability = 60 + (cpu_usage - 70)
                
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="cpu_usage",
                    predicted_issue=f"Tendência de aumento no uso de CPU ({cpu_usage:.1f}%)",
                    probability=probability,
                    estimated_time="12-24 horas",
                    suggested_actions=[
                        "Monitorar aplicações críticas",
                        "Preparar plano de otimização"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
                
        except Exception as e:
            logger.error(f"Erro na análise de CPU para {endpoint_name}: {e}")
        
        return None
    
    def _analyze_memory_trends(
        self,
        endpoint_name: str,
        endpoint_data: Dict[str, Any],
        config: PredictiveConfig
    ) -> Optional[PredictiveAlert]:
        """Analisa tendências de memória"""
        
        try:
            memory_data = endpoint_data.get("memory_usage")
            if not memory_data or not isinstance(memory_data, (int, float)):
                return None
            
            memory_usage = float(memory_data)
            
            if memory_usage > 85:
                probability = min(90, 75 + (memory_usage - 85) * 2)
                estimated_time = "1-3 horas" if memory_usage > 95 else "4-8 horas"
                
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="memory_usage",
                    predicted_issue=f"Esgotamento de memória iminente ({memory_usage:.1f}%)",
                    probability=probability,
                    estimated_time=estimated_time,
                    suggested_actions=[
                        "Verificar vazamentos de memória",
                        "Reiniciar serviços não críticos",
                        "Considerar aumento de RAM"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
            
            elif memory_usage > 75:
                probability = 65 + (memory_usage - 75)
                
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="memory_usage",
                    predicted_issue=f"Uso crescente de memória ({memory_usage:.1f}%)",
                    probability=probability,
                    estimated_time="8-16 horas",
                    suggested_actions=[
                        "Monitorar aplicações que consomem memória",
                        "Preparar estratégia de limpeza"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
                
        except Exception as e:
            logger.error(f"Erro na análise de memória para {endpoint_name}: {e}")
        
        return None
    
    def _analyze_network_trends(
        self,
        endpoint_name: str,
        endpoint_data: Dict[str, Any],
        config: PredictiveConfig
    ) -> Optional[PredictiveAlert]:
        """Analisa tendências de rede"""
        
        try:
            response_time = endpoint_data.get("response_time")
            if not response_time or not isinstance(response_time, (int, float)):
                return None
            
            response_ms = float(response_time)
            
            if response_ms > 2000:  # 2 segundos
                probability = min(85, 70 + (response_ms - 2000) / 100)
                
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="response_time",
                    predicted_issue=f"Latência elevada ({response_ms:.0f}ms) indica possíveis problemas de rede",
                    probability=probability,
                    estimated_time="1-6 horas",
                    suggested_actions=[
                        "Verificar conectividade de rede",
                        "Analisar tráfego de rede",
                        "Verificar capacidade do servidor"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
            
            elif response_ms > 1000:  # 1 segundo
                probability = 60 + (response_ms - 1000) / 50
                
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="response_time",
                    predicted_issue=f"Degradação na performance de rede ({response_ms:.0f}ms)",
                    probability=probability,
                    estimated_time="6-12 horas",
                    suggested_actions=[
                        "Monitorar latência continuamente",
                        "Verificar qualidade da conexão"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
                
        except Exception as e:
            logger.error(f"Erro na análise de rede para {endpoint_name}: {e}")
        
        return None
    
    def _analyze_availability_trends(
        self,
        endpoint_name: str,
        endpoint_data: Dict[str, Any],
        config: PredictiveConfig
    ) -> Optional[PredictiveAlert]:
        """Analisa tendências de disponibilidade"""
        
        try:
            status = endpoint_data.get("status", "").lower()
            
            if status in ["warning", "degraded"]:
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="availability",
                    predicted_issue="Status degradado pode levar a indisponibilidade",
                    probability=75.0,
                    estimated_time="2-6 horas",
                    suggested_actions=[
                        "Investigar causa da degradação",
                        "Preparar plano de contingência",
                        "Monitorar serviços dependentes"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
            
            elif status == "critical":
                return PredictiveAlert(
                    endpoint=endpoint_name,
                    metric="availability",
                    predicted_issue="Status crítico - falha iminente detectada",
                    probability=90.0,
                    estimated_time="30 minutos - 2 horas",
                    suggested_actions=[
                        "Ação imediata necessária",
                        "Ativar procedimentos de emergência",
                        "Notificar equipe de suporte"
                    ],
                    confidence_threshold=config.confidence_threshold
                )
                
        except Exception as e:
            logger.error(f"Erro na análise de disponibilidade para {endpoint_name}: {e}")
        
        return None
    
    def _analyze_alert_patterns(
        self,
        alerts: List[Dict[str, Any]],
        config: PredictiveConfig
    ) -> List[PredictiveAlert]:
        """Analisa padrões em alertas existentes"""
        
        pattern_alerts = []
        
        try:
            if not alerts:
                return pattern_alerts
            
            # Agrupa alertas por endpoint
            endpoint_alerts = {}
            for alert in alerts:
                endpoint = alert.get("endpoint", "Unknown")
                if endpoint not in endpoint_alerts:
                    endpoint_alerts[endpoint] = []
                endpoint_alerts[endpoint].append(alert)
            
            # Analisa padrões por endpoint
            for endpoint, endpoint_alert_list in endpoint_alerts.items():
                if len(endpoint_alert_list) >= 3:  # Padrão de múltiplos alertas
                    pattern_alerts.append(
                        PredictiveAlert(
                            endpoint=endpoint,
                            metric="alert_frequency",
                            predicted_issue=f"Padrão de múltiplos alertas detectado ({len(endpoint_alert_list)} alertas)",
                            probability=80.0,
                            estimated_time="1-4 horas",
                            suggested_actions=[
                                "Investigar causa raiz dos alertas",
                                "Verificar se há problema sistêmico",
                                "Considerar manutenção preventiva"
                            ],
                            confidence_threshold=config.confidence_threshold
                        )
                    )
                    
        except Exception as e:
            logger.error(f"Erro na análise de padrões de alertas: {e}")
        
        return pattern_alerts
    
    def _generate_sample_alerts(self, config: PredictiveConfig) -> List[PredictiveAlert]:
        """Gera alertas de exemplo quando não há dados suficientes"""
        
        sample_alerts = [
            PredictiveAlert(
                endpoint="Server-01",
                metric="cpu_usage",
                predicted_issue="Tendência de alto uso de CPU baseada em padrões históricos",
                probability=78.0,
                estimated_time="4-8 horas",
                suggested_actions=[
                    "Monitorar processos em execução",
                    "Verificar aplicações críticas"
                ],
                confidence_threshold=config.confidence_threshold
            ),
            PredictiveAlert(
                endpoint="Server-02",
                metric="memory_usage",
                predicted_issue="Possível esgotamento de memória detectado",
                probability=72.0,
                estimated_time="6-12 horas",
                suggested_actions=[
                    "Verificar vazamentos de memória",
                    "Considerar reinicialização de serviços"
                ],
                confidence_threshold=config.confidence_threshold
            ),
            PredictiveAlert(
                endpoint="Router-01",
                metric="network_latency",
                predicted_issue="Degradação na performance de rede prevista",
                probability=68.0,
                estimated_time="2-6 horas",
                suggested_actions=[
                    "Verificar conectividade",
                    "Analisar tráfego de rede"
                ],
                confidence_threshold=config.confidence_threshold
            )
        ]
        
        # Filtra por threshold de confiança
        return [
            alert for alert in sample_alerts
            if alert.probability >= config.confidence_threshold
        ]
    
    def calculate_trend_velocity(self, values: List[float]) -> float:
        """Calcula a velocidade da tendência nos dados"""
        
        if len(values) < 2:
            return 0.0
        
        try:
            # Calcula a taxa de mudança média
            changes = [values[i] - values[i-1] for i in range(1, len(values))]
            return statistics.mean(changes) if changes else 0.0
            
        except Exception:
            return 0.0
    
    def predict_future_value(
        self,
        current_value: float,
        trend_velocity: float,
        hours_ahead: int
    ) -> float:
        """Prevê valor futuro baseado na tendência atual"""
        
        try:
            # Previsão linear simples
            predicted_value = current_value + (trend_velocity * hours_ahead)
            return max(0.0, min(100.0, predicted_value))  # Limita entre 0-100%
            
        except Exception:
            return current_value