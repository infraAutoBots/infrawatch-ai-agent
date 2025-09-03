#!/usr/bin/env python3
"""
Script para testar a autenticação do InfraWatch AI Agent
"""

import asyncio
import sys
import os

# Adicionar o diretório do infrawatch-ai-agent ao path
sys.path.insert(0, "c:\\Users\\User\\Videos\\infrawatch\\infrawatch-ai-agent")

from app.services.infrawatch_client import InfraWatchClient
from app.core.config import Settings

async def test_authentication():
    """Testa a autenticação e algumas operações básicas"""
    
    print("🔧 Testando autenticação do InfraWatch AI Agent...")
    
    try:
        # Criar cliente
        client = InfraWatchClient()
        
        print(f"📡 Conectando com: {client.base_url}")
        print(f"👤 Credenciais: {client.agent_email}")
        
        # Fazer login
        print("\n🔐 Fazendo login...")
        login_success = await client.login()
        
        if not login_success:
            print("❌ Falha na autenticação")
            return False
            
        print("✅ Login realizado com sucesso!")
        print(f"🎟️ Token obtido: {client._access_token[:50]}...")
        
        # Testar operações
        print("\n📊 Testando operações...")
        
        # 1. Buscar endpoints
        print("   • Buscando endpoints...")
        endpoints = await client.get_endpoints()
        print(f"   ✅ {len(endpoints)} endpoints encontrados")
        
        # 2. Buscar overview
        print("   • Buscando overview da infraestrutura...")
        overview = await client.get_infrastructure_overview()
        print(f"   ✅ Overview obtido:")
        print(f"      - Total endpoints: {overview.get('total_endpoints', 0)}")
        print(f"      - Online: {overview.get('online_endpoints', 0)}")
        print(f"      - Uptime: {overview.get('uptime_percentage', 0)}%")
        print(f"      - Alertas ativos: {overview.get('active_alerts', 0)}")
        
        # 3. Buscar alertas
        print("   • Buscando alertas...")
        alerts = await client.get_alerts(limit=5)
        print(f"   ✅ {len(alerts)} alertas encontrados")
        
        print("\n🎉 Todos os testes passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    # Configurar settings (simular .env)
    os.environ["INFRAWATCH_API_URL"] = "http://localhost:8000"
    os.environ["INFRAWATCH_AGENT_EMAIL"] = "ndondadaniel2020@gmail.com"
    os.environ["INFRAWATCH_AGENT_PASSWORD"] = "ndondadaniel2020@gmail.com"
    
    success = asyncio.run(test_authentication())
    
    if success:
        print("\n✨ InfraWatch AI Agent está pronto para uso!")
    else:
        print("\n💥 Problemas na configuração. Verifique os logs acima.")
        sys.exit(1)
