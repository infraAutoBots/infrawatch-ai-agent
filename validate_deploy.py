#!/usr/bin/env python3
"""
Script de validação para deploy no Railway
Verifica se todas as configurações necessárias estão presentes
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_files():
    """Verifica se os arquivos necessários existem"""
    required_files = [
        'Procfile',
        'requirements.txt',
        'runtime.txt',
        'railway.json',
        '.env.example',
        'main.py',
        'app/main.py',
        'app/core/config.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Arquivos obrigatórios ausentes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Todos os arquivos obrigatórios estão presentes")
    return True

def check_procfile():
    """Verifica o conteúdo do Procfile"""
    try:
        with open('Procfile', 'r') as f:
            content = f.read().strip()
        
        if not content:
            print("❌ Procfile está vazio")
            return False
        
        if not content.startswith('web:'):
            print("❌ Procfile deve começar com 'web:'")
            return False
        
        print("✅ Procfile configurado corretamente")
        return True
    except Exception as e:
        print(f"❌ Erro ao ler Procfile: {e}")
        return False

def check_requirements():
    """Verifica as dependências no requirements.txt"""
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'pydantic',
            'httpx',
            'python-dotenv'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in content:
                missing_packages.append(package)
        
        if missing_packages:
            print("❌ Pacotes obrigatórios ausentes no requirements.txt:")
            for package in missing_packages:
                print(f"   - {package}")
            return False
        
        print("✅ Requirements.txt contém todas as dependências obrigatórias")
        return True
    except Exception as e:
        print(f"❌ Erro ao ler requirements.txt: {e}")
        return False

def check_runtime():
    """Verifica o arquivo runtime.txt"""
    try:
        with open('runtime.txt', 'r') as f:
            content = f.read().strip()
        
        if not content.startswith('python-'):
            print("❌ runtime.txt deve especificar versão do Python (ex: python-3.11.6)")
            return False
        
        print(f"✅ Runtime configurado: {content}")
        return True
    except Exception as e:
        print(f"❌ Erro ao ler runtime.txt: {e}")
        return False

def check_config():
    """Verifica se a configuração está correta para produção"""
    try:
        from app.core.config import settings
        
        issues = []
        
        # Verifica configurações importantes
        if settings.api_host != "0.0.0.0":
            issues.append("API_HOST deveria ser '0.0.0.0' para produção")
        
        if settings.debug:
            issues.append("DEBUG deveria ser False para produção")
        
        # Verifica se não há credenciais hardcoded
        if settings.google_api_key and settings.google_api_key != "":
            if "AIzaSy" in settings.google_api_key:
                issues.append("GOOGLE_API_KEY parece estar hardcoded - use variável de ambiente")
        
        if issues:
            print("⚠️  Problemas de configuração encontrados:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Configurações estão corretas para produção")
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar configurações: {e}")
        return False

def check_environment_variables():
    """Lista as variáveis de ambiente necessárias"""
    required_vars = [
        'GOOGLE_API_KEY',
        'INFRAWATCH_AGENT_EMAIL', 
        'INFRAWATCH_AGENT_PASSWORD'
    ]
    
    print("\n📋 Variáveis de ambiente necessárias no Railway:")
    for var in required_vars:
        print(f"   - {var}")
    
    print("\n💡 Configure essas variáveis no dashboard do Railway antes do deploy")
    return True

def main():
    """Executa todas as verificações"""
    print("🔍 Validando configuração para deploy no Railway...")
    print("=" * 60)
    
    checks = [
        check_files,
        check_procfile, 
        check_requirements,
        check_runtime,
        check_config,
        check_environment_variables
    ]
    
    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            all_passed = False
        print()
    
    print("=" * 60)
    if all_passed:
        print("🎉 Validação concluída! Projeto pronto para deploy no Railway")
        print("\n📚 Próximos passos:")
        print("1. Faça commit de todas as mudanças")
        print("2. Conecte o repositório ao Railway")
        print("3. Configure as variáveis de ambiente")
        print("4. Inicie o deploy")
        print("\n📖 Consulte RAILWAY_DEPLOY.md para instruções detalhadas")
    else:
        print("❌ Validação falhou! Corrija os problemas antes do deploy")
        sys.exit(1)

if __name__ == "__main__":
    main()
