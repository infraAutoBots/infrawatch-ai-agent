#!/usr/bin/env python3

"""
Script para inicializar a base de conhecimento do AI Agent
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Adiciona o diretório do projeto ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rag import VectorStore
from app.core.logging import setup_logging, get_logger


async def initialize_knowledge_base():
    """Inicializa a base de conhecimento com dados padrão"""
    
    # Setup logging
    setup_logging()
    logger = get_logger("init_knowledge")
    
    logger.info("🧠 Inicializando base de conhecimento...")
    
    try:
        # Inicializa o vector store
        vector_store = VectorStore()
        
        # Carrega dados da base de conhecimento
        knowledge_file = project_root / "data" / "knowledge_base.json"
        
        if not knowledge_file.exists():
            logger.error(f"❌ Arquivo de conhecimento não encontrado: {knowledge_file}")
            return False
        
        logger.info("📖 Carregando base de conhecimento...")
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
        
        # Adiciona conhecimento ao vector store
        document_ids = await vector_store.add_knowledge_base(knowledge_data)
        
        logger.info(f"✅ Base de conhecimento carregada: {len(document_ids)} documentos adicionados")
        
        # Persiste as mudanças
        vector_store.persist()
        logger.info("💾 Base de conhecimento persistida")
        
        # Mostra estatísticas
        stats = await vector_store.get_collection_stats()
        logger.info("📊 Estatísticas da base de conhecimento:")
        logger.info(f"   Total de documentos: {stats.get('total_documents', 0)}")
        logger.info(f"   Tipos de documentos: {stats.get('document_types', {})}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar base de conhecimento: {e}")
        return False


def main():
    """Função principal"""
    
    print("=" * 60)
    print("🤖 INFRAWATCH AI AGENT - INICIALIZAÇÃO")
    print("=" * 60)
    
    # Executa inicialização
    success = asyncio.run(initialize_knowledge_base())
    
    if success:
        print("✅ Base de conhecimento inicializada com sucesso!")
        print("\nPróximos passos:")
        print("1. Configure sua GOOGLE_API_KEY no arquivo .env")
        print("2. Execute: python main.py")
        print("3. Acesse: http://localhost:8001/docs")
    else:
        print("❌ Falha na inicialização da base de conhecimento")
        sys.exit(1)


if __name__ == "__main__":
    main()
