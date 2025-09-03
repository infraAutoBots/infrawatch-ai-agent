import asyncio
from typing import Optional

from app.core.logging import get_logger
from app.services.infrawatch_client import InfraWatchClient

logger = get_logger("auth_service")


class AuthService:
    """Serviço de autenticação para o InfraWatch AI Agent"""
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self) -> Optional[InfraWatchClient]:
        """Retorna o cliente autenticado"""
        return self._client
    
    async def initialize(self) -> bool:
        """Inicializa o serviço de autenticação"""
        try:
            self._client = InfraWatchClient()
            
            logger.info("Iniciando autenticação com InfraWatch Backend...")
            success = await self._client.login()
            
            if success:
                logger.info("Autenticação realizada com sucesso!")
                return True
            else:
                logger.error("Falha na autenticação inicial")
                return False
                
        except Exception as e:
            logger.error(f"Erro durante inicialização da autenticação: {e}")
            return False
    
    async def ensure_authenticated(self) -> bool:
        """Garante que o cliente está autenticado"""
        if not self._client:
            return await self.initialize()
        
        return await self._client.ensure_authenticated()
    
    async def get_authenticated_client(self) -> Optional[InfraWatchClient]:
        """Retorna um cliente autenticado"""
        if await self.ensure_authenticated():
            return self._client
        return None


# Instância global do serviço de autenticação
auth_service = AuthService()


async def get_infrawatch_client() -> Optional[InfraWatchClient]:
    """Dependency para obter cliente autenticado"""
    return await auth_service.get_authenticated_client()
