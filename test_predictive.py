#!/usr/bin/env python3

import sys
import os
import asyncio

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.predictive_service import PredictiveService
from app.models import PredictiveConfig

async def test_predictive_service():
    """Testa o serviço preditivo com dados simulados"""
    
    print("🧪 Testando Serviço Preditivo...")
    
    service = PredictiveService()
    config = PredictiveConfig(confidence_threshold=70)
    
    # Simula dados reais do backend
    mock_data = {
        'total_endpoints': 14,
        'total_online': 3,
        'total_offline': 11,
        'monitors': [
            {
                'endpoint': '8.8.8.8',
                'data': {
                    'id_end_point': 8,
                    'status': True,
                    'active': True,
                    'ping_rtt': '337.96',
                    'last_updated': '2025-09-13T10:43:48.399821'
                }
            },
            {
                'endpoint': '192.168.1.1',
                'data': {
                    'id_end_point': 54,
                    'status': False,
                    'active': True,
                    'ping_rtt': '11669.14',
                    'last_updated': '2025-09-13T10:43:59.893617'
                }
            },
            {
                'endpoint': '1.1.1.1',
                'data': {
                    'id_end_point': 14,
                    'status': True,
                    'active': True,
                    'ping_rtt': '337.24',
                    'last_updated': '2025-09-13T10:43:48.399281'
                }
            },
            {
                'endpoint': '127.0.0.1',
                'data': {
                    'id_end_point': 2,
                    'status': False,
                    'active': True,
                    'ping_rtt': '337.44',
                    'hrProcessorLoad': 85.5,  # Alto CPU
                    'memTotalReal': 8192,
                    'memAvailReal': 1024,     # Pouca memória disponível
                    'last_updated': '2025-09-13T10:43:48.399544'
                }
            }
        ]
    }
    
    print("📊 Dados de entrada:")
    print(f"  - Total endpoints: {mock_data['total_endpoints']}")
    print(f"  - Online: {mock_data['total_online']}")
    print(f"  - Offline: {mock_data['total_offline']}")
    print(f"  - Monitors: {len(mock_data['monitors'])}")
    
    # Executa análise preditiva
    alerts = await service.analyze_predictive_patterns(mock_data, config)
    
    print(f"\n🚨 Alertas Preditivos Gerados: {len(alerts)}")
    
    if alerts:
        for i, alert in enumerate(alerts, 1):
            print(f"\n  {i}. {alert.endpoint}")
            print(f"     📈 Métrica: {alert.metric}")
            print(f"     ⚠️  Problema: {alert.predicted_issue}")
            print(f"     🎯 Probabilidade: {alert.probability}%")
            print(f"     ⏰ Tempo Estimado: {alert.estimated_time}")
            print(f"     💡 Ações: {', '.join(alert.suggested_actions[:2])}")
    else:
        print("  ❌ Nenhum alerta gerado")
    
    # Teste com dados vazios
    print(f"\n🧪 Testando com dados vazios...")
    empty_alerts = await service.analyze_predictive_patterns({}, config)
    print(f"  📊 Alertas com dados vazios: {len(empty_alerts)}")
    
    # Teste com threshold alto
    print(f"\n🧪 Testando com threshold alto (95%)...")
    high_config = PredictiveConfig(confidence_threshold=95)
    high_alerts = await service.analyze_predictive_patterns(mock_data, high_config)
    print(f"  📊 Alertas com threshold 95%: {len(high_alerts)}")

if __name__ == "__main__":
    asyncio.run(test_predictive_service())
