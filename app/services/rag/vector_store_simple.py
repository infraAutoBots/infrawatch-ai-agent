import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
import re

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("vector_store")


class VectorStore:
    """Armazenamento vetorial simples em memória (sem dependências pesadas)"""
    
    def __init__(self):
        self.knowledge_base = []
        self.load_knowledge_base()
        logger.info("Simple Vector Store inicializado")
    
    def load_knowledge_base(self):
        """Carrega a base de conhecimento do arquivo JSON"""
        try:
            knowledge_file = os.path.join("data", "knowledge_base.json")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"Carregados {len(self.knowledge_base)} itens da base de conhecimento")
            else:
                logger.warning("Arquivo knowledge_base.json não encontrado")
                self.knowledge_base = []
        except Exception as e:
            logger.error(f"Erro ao carregar knowledge_base.json: {e}")
            self.knowledge_base = []
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Calculadora de similaridade simples baseada em palavras-chave"""
        # Converte para minúsculas e remove caracteres especiais
        text1_clean = re.sub(r'[^a-záàâãéêíóôõúç\s]', '', text1.lower())
        text2_clean = re.sub(r'[^a-záàâãéêíóôõúç\s]', '', text2.lower())
        
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Similaridade de Jaccard
        similarity = len(intersection) / len(union) if union else 0.0
        
        # Bonus para palavras-chave importantes de infraestrutura
        important_words = {
            'snmp', 'ping', 'tcp', 'udp', 'http', 'https', 'ssh', 'ftp',
            'servidor', 'rede', 'switch', 'router', 'firewall', 'load', 'balancer',
            'cpu', 'memoria', 'disco', 'bandwidth', 'latencia', 'throughput',
            'monitor', 'alert', 'threshold', 'metric', 'log', 'error', 'warning'
        }
        
        common_important = words1.intersection(words2).intersection(important_words)
        if common_important:
            similarity += len(common_important) * 0.1
        
        return min(similarity, 1.0)
    
    def _generate_id(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Gera um ID único para o conteúdo"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        timestamp = datetime.now().isoformat()
        return f"{content_hash}_{timestamp}"

    async def get_relevant_context(
        self, 
        query: str, 
        max_context_length: int = 1500,
        n_results: int = 3
    ) -> str:
        """Busca contexto relevante para a query"""
        
        if not query.strip():
            return ""
        
        try:
            # Busca documentos similares usando similaridade simples
            similar_docs = []
            
            for item in self.knowledge_base:
                if isinstance(item, dict) and 'content' in item:
                    content = item['content']
                    similarity = self._simple_similarity(query, content)
                    
                    if similarity > 0.1:  # Threshold mínimo
                        similar_docs.append({
                            'content': content,
                            'metadata': item.get('metadata', {}),
                            'similarity': similarity
                        })
            
            # Ordena por similaridade
            similar_docs.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Pega os top N resultados
            top_docs = similar_docs[:n_results]
            
            if not top_docs:
                return "Nenhum contexto relevante encontrado na base de conhecimento."
            
            # Constrói contexto respeitando o limite de tamanho
            context_parts = []
            current_length = 0
            
            for doc in top_docs:
                content = doc['content']
                if current_length + len(content) <= max_context_length:
                    context_parts.append(content)
                    current_length += len(content)
                else:
                    # Adiciona parte do documento se ainda há espaço
                    remaining_space = max_context_length - current_length
                    if remaining_space > 100:  # Só adiciona se tem espaço razoável
                        context_parts.append(content[:remaining_space] + "...")
                    break
            
            context = "\n\n---\n\n".join(context_parts)
            
            logger.info(f"Contexto encontrado: {len(top_docs)} documentos, {len(context)} caracteres")
            return context
            
        except Exception as e:
            logger.error(f"Erro ao buscar contexto relevante: {e}")
            return "Erro ao buscar contexto na base de conhecimento."

    async def add_document(
        self, 
        content: str, 
        metadata: Dict[str, Any] = None,
        document_id: Optional[str] = None
    ) -> str:
        """Adiciona um documento ao vector store (versão simplificada)"""
        
        if not content.strip():
            raise ValueError("Conteúdo não pode estar vazio")
        
        try:
            # Gera ID se não fornecido
            if not document_id:
                document_id = self._generate_id(content, metadata)
            
            # Adiciona à base de conhecimento em memória
            doc = {
                'id': document_id,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            self.knowledge_base.append(doc)
            
            logger.info(f"Documento adicionado: {document_id}")
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
            similar_docs = []
            
            for item in self.knowledge_base:
                if isinstance(item, dict) and 'content' in item:
                    content = item['content']
                    metadata = item.get('metadata', {})
                    
                    # Aplica filtro de metadata se fornecido
                    if filter_metadata:
                        if not all(metadata.get(k) == v for k, v in filter_metadata.items()):
                            continue
                    
                    similarity = self._simple_similarity(query, content)
                    
                    if similarity > 0.1:
                        similar_docs.append({
                            'id': item.get('id', ''),
                            'content': content,
                            'metadata': metadata,
                            'similarity': similarity
                        })
            
            # Ordena por similaridade
            similar_docs.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similar_docs[:n_results]
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos similares: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do vector store"""
        
        total_docs = len(self.knowledge_base)
        total_size = sum(len(item.get('content', '')) for item in self.knowledge_base)
        
        doc_types = {}
        for item in self.knowledge_base:
            metadata = item.get('metadata', {})
            doc_type = metadata.get('type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        return {
            "total_documents": total_docs,
            "total_content_size": total_size,
            "average_document_size": total_size // total_docs if total_docs > 0 else 0,
            "document_types": doc_types
        }
    
    def clear(self):
        """Limpa todos os documentos do vector store"""
        self.knowledge_base = []
        logger.info("Vector store limpo")
