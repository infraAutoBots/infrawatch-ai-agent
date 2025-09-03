import os
import sys
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.chat import router as chat_router
from app.api.insights import router as insights_router
from app.services.auth_service import auth_service


# Setup inicial
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    
    logger.info("🚀 Iniciando InfraWatch AI Agent...")
    
    # Inicialização
    try:
        # Inicializa o serviço de autenticação
        logger.info("🔐 Inicializando autenticação com InfraWatch Backend...")
        auth_success = await auth_service.initialize()
        
        if auth_success:
            logger.info("✅ Autenticação inicializada com sucesso")
        else:
            logger.warning("⚠️ Falha na inicialização da autenticação - algumas funcionalidades podem não funcionar")
        
        logger.info("✅ AI Agent inicializado com sucesso")
        
        yield
        
    finally:
        logger.info("🔄 Finalizando AI Agent...")
        # Cleanup aqui se necessário


# Criar aplicação FastAPI
app = FastAPI(
    title="InfraWatch AI Agent",
    description="Agente de IA especializado em análise de infraestrutura com RAG e Gemini",
    version="1.0.0",
    lifespan=lifespan
)


# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Incluir routers
app.include_router(chat_router)
app.include_router(insights_router)


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "service": "InfraWatch AI Agent",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    try:
        from app.services.infrawatch_client import InfraWatchClient
        
        # Testa conectividade com o backend
        infrawatch_client = InfraWatchClient()
        health_data = await infrawatch_client.get_system_health()
        
        backend_status = "connected" if health_data.get("status") != "unknown" else "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "ai_agent": "online",
                "infrawatch_backend": backend_status,
                "gemini_api": "configured" if settings.google_api_key else "not_configured",
                "vector_store": "online"
            },
            "config": {
                "gemini_model": settings.gemini_model,
                "vector_db_path": settings.chroma_db_path,
                "infrawatch_api_url": settings.infrawatch_api_url
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções"""
    
    logger.error(f"Erro não tratado: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
