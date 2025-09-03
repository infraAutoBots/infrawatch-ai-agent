import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("vector_store")


class VectorStore:
    """Gerenciador de armazenamento vetorial usando ChromaDB"""
    
    def __init__(self):
        self.chroma_path = settings.chroma_db_path
        self.collection_name = "infrawatch_knowledge"
        
        # Cria o diretório se não existir
        os.makedirs(self.chroma_path, exist_ok=True)
        
        # Inicializa ChromaDB
        chroma_settings = ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.chroma_path
        )
        
        self.client = chromadb.Client(chroma_settings)
        
        # Cria ou obtém a coleção
        try:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "InfraWatch knowledge base"}
            )
        except Exception:
            # Coleção já existe
            self.collection = self.client.get_collection(name=self.collection_name)
        
        # Inicializa o modelo de embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info(f"Vector store inicializado em {self.chroma_path}")
    
    def _generate_id(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Gera um ID único para o conteúdo"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        timestamp = datetime.now().isoformat()
        return f"{content_hash}_{timestamp}"
    
    def _create_embedding(self, text: str) -> List[float]:
        """Cria embedding para o texto"""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    async def add_document(
        self, 
        content: str, 
        metadata: Dict[str, Any] = None,
        document_id: Optional[str] = None
    ) -> str:
        """Adiciona um documento ao vector store"""
        
        if not content.strip():
            raise ValueError("Conteúdo não pode estar vazio")
        
        try:
            # Gera ID se não fornecido
            if not document_id:
                document_id = self._generate_id(content, metadata)
            
            # Cria embedding
            embedding = await asyncio.to_thread(self._create_embedding, content)
            
            # Prepara metadados
            doc_metadata = {
                "timestamp": datetime.now().isoformat(),
                "content_length": len(content),
                **(metadata or {})
            }
            
            # Adiciona à coleção
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[doc_metadata],
                ids=[document_id]
            )
            
            logger.info(f"Documento adicionado com ID: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Erro ao adicionar documento: {e}")
            raise
    
    async def add_infrastructure_data(
        self, 
        endpoint_name: str,
        metrics: Dict[str, Any],
        alerts: List[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> str:
        """Adiciona dados de infraestrutura formatados ao vector store"""
        
        timestamp = timestamp or datetime.now()
        
        # Formata os dados para texto pesquisável
        content_parts = [
            f"Endpoint: {endpoint_name}",
            f"Timestamp: {timestamp.isoformat()}",
            "",
            "MÉTRICAS:"
        ]
        
        # Adiciona métricas formatadas
        for key, value in metrics.items():
            if key == "hrProcessorLoad":
                content_parts.append(f"- CPU Load: {value}%")
            elif key == "memTotalReal":
                content_parts.append(f"- Total Memory: {value}")
            elif key == "memAvailReal":
                content_parts.append(f"- Available Memory: {value}")
            elif key == "hrStorageSize":
                content_parts.append(f"- Storage Size: {value}")
            elif key == "hrStorageUsed":
                content_parts.append(f"- Storage Used: {value}")
            elif key == "sysUpTime":
                content_parts.append(f"- System Uptime: {value}")
            else:
                content_parts.append(f"- {key}: {value}")
        
        # Adiciona alertas se existirem
        if alerts:
            content_parts.extend(["", "ALERTAS:"])
            for alert in alerts:
                severity = alert.get("severity", "unknown")
                title = alert.get("title", "Alert")
                description = alert.get("description", "")
                content_parts.append(f"- [{severity.upper()}] {title}: {description}")
        
        content = "\n".join(content_parts)
        
        metadata = {
            "type": "infrastructure_data",
            "endpoint_name": endpoint_name,
            "timestamp": timestamp.isoformat(),
            "metrics_count": len(metrics),
            "alerts_count": len(alerts) if alerts else 0
        }
        
        return await self.add_document(content, metadata)
    
    async def search_similar(
        self, 
        query: str, 
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Busca documentos similares baseado na query"""
        
        try:
            # Cria embedding da query
            query_embedding = await asyncio.to_thread(self._create_embedding, query)
            
            # Realiza a busca
            where_clause = filter_metadata if filter_metadata else None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause
            )
            
            # Formata os resultados
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0,
                        'id': results['ids'][0][i] if results['ids'] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Encontrados {len(formatted_results)} documentos similares para: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erro na busca vetorial: {e}")
            return []
    
    async def get_relevant_context(
        self, 
        query: str, 
        max_context_length: int = 2000,
        n_results: int = 3
    ) -> List[str]:
        """Obtém contexto relevante para uma query, otimizado para RAG"""
        
        results = await self.search_similar(query, n_results=n_results)
        
        context_items = []
        total_length = 0
        
        for result in results:
            content = result['content']
            
            # Verifica se adicionar este conteúdo ultrapassaria o limite
            if total_length + len(content) > max_context_length:
                # Trunca o conteúdo para caber no limite restante
                remaining_length = max_context_length - total_length
                if remaining_length > 100:  # Só adiciona se sobrar espaço significativo
                    content = content[:remaining_length] + "..."
                    context_items.append(content)
                break
            
            context_items.append(content)
            total_length += len(content)
        
        logger.info(f"Retornando {len(context_items)} itens de contexto ({total_length} chars)")
        return context_items
    
    async def add_knowledge_base(self, knowledge_data: Dict[str, Any]) -> List[str]:
        """Adiciona uma base de conhecimento estruturada"""
        
        document_ids = []
        
        try:
            # Adiciona documentação de sistemas
            if "systems" in knowledge_data:
                for system_name, system_info in knowledge_data["systems"].items():
                    content = f"""
Sistema: {system_name}
Descrição: {system_info.get('description', 'N/A')}
Tipo: {system_info.get('type', 'N/A')}
Configuração: {json.dumps(system_info.get('config', {}), indent=2)}
Métricas Importantes: {', '.join(system_info.get('important_metrics', []))}
Limites: {json.dumps(system_info.get('thresholds', {}), indent=2)}
Troubleshooting: {system_info.get('troubleshooting', 'N/A')}
"""
                    metadata = {
                        "type": "system_documentation",
                        "system_name": system_name,
                        "category": system_info.get('type', 'unknown')
                    }
                    
                    doc_id = await self.add_document(content, metadata)
                    document_ids.append(doc_id)
            
            # Adiciona playbooks
            if "playbooks" in knowledge_data:
                for playbook_name, playbook_info in knowledge_data["playbooks"].items():
                    content = f"""
Playbook: {playbook_name}
Categoria: {playbook_info.get('category', 'N/A')}
Descrição: {playbook_info.get('description', 'N/A')}
Condições: {playbook_info.get('conditions', 'N/A')}
Passos: {json.dumps(playbook_info.get('steps', []), indent=2)}
Comandos: {'; '.join(playbook_info.get('commands', []))}
"""
                    metadata = {
                        "type": "playbook",
                        "playbook_name": playbook_name,
                        "category": playbook_info.get('category', 'general')
                    }
                    
                    doc_id = await self.add_document(content, metadata)
                    document_ids.append(doc_id)
            
            # Adiciona FAQs
            if "faqs" in knowledge_data:
                for faq in knowledge_data["faqs"]:
                    content = f"""
Pergunta: {faq.get('question', 'N/A')}
Resposta: {faq.get('answer', 'N/A')}
Categoria: {faq.get('category', 'N/A')}
Tags: {', '.join(faq.get('tags', []))}
"""
                    metadata = {
                        "type": "faq",
                        "category": faq.get('category', 'general'),
                        "tags": faq.get('tags', [])
                    }
                    
                    doc_id = await self.add_document(content, metadata)
                    document_ids.append(doc_id)
            
            logger.info(f"Base de conhecimento adicionada: {len(document_ids)} documentos")
            return document_ids
            
        except Exception as e:
            logger.error(f"Erro ao adicionar base de conhecimento: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da coleção"""
        
        try:
            # Conta total de documentos
            count_result = self.collection.count()
            
            # Busca alguns metadados para estatísticas
            sample_results = self.collection.get(
                limit=100,
                include=["metadatas"]
            )
            
            # Analisa tipos de documentos
            doc_types = {}
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    doc_type = metadata.get('type', 'unknown')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            return {
                "total_documents": count_result,
                "document_types": doc_types,
                "collection_name": self.collection_name,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                "total_documents": 0,
                "document_types": {},
                "collection_name": self.collection_name,
                "error": str(e)
            }
    
    def persist(self):
        """Persiste as mudanças no disco"""
        try:
            self.client.persist()
            logger.info("Vector store persistido com sucesso")
        except Exception as e:
            logger.error(f"Erro ao persistir vector store: {e}")
            raise
