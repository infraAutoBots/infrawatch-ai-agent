#!/usr/bin/env python3

import os
import sys
import asyncio
from pathlib import Path

# Adiciona o diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

def main():
    """Função principal para executar o AI Agent"""
    
    # Setup logging
    setup_logging()
    logger = get_logger("startup")
    
    logger.info("=" * 60)
    logger.info("🤖 INFRAWATCH AI AGENT")
    logger.info("=" * 60)
    logger.info(f"🔧 Host: {settings.api_host}")
    logger.info(f"🌐 Port: {settings.api_port}")
    logger.info(f"🐛 Debug: {settings.debug}")
    logger.info(f"🧠 Gemini Model: {settings.gemini_model}")
    logger.info(f"📊 Vector DB: {settings.chroma_db_path}")
    logger.info(f"🔗 InfraWatch API: {settings.infrawatch_api_url}")
    logger.info("=" * 60)
    
    # Verifica configurações essenciais
    if not settings.google_api_key:
        logger.error("❌ GOOGLE_API_KEY não configurada!")
        logger.error("Por favor, configure sua API key do Gemini no arquivo .env")
        sys.exit(1)
    
    # Cria diretórios necessários
    os.makedirs(settings.chroma_db_path, exist_ok=True)
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    logger.info("🚀 Iniciando servidor...")
    
    # Importa uvicorn aqui para evitar problemas de import
    try:
        import uvicorn
        
        uvicorn.run(
            "app.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level=settings.log_level.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
