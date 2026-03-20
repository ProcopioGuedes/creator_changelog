#!/usr/bin/env python3
"""
Script de configuração interativo para as chaves de API
Cria o arquivo .env de forma segura
"""

import os
import sys
from pathlib import Path

def setup_env():
    """Configura o arquivo .env de forma segura e interativa"""
    
    env_path = Path(".env")
    
    # Verifica se o arquivo já existe
    if env_path.exists():
        response = input("⚠️  O arquivo .env já existe. Deseja sobrescrevê-lo? (s/n): ").strip().lower()
        if response != 's':
            print("❌ Configuração cancelada.")
            return False
    
    print("\n" + "="*70)
    print("  🔐 Configuração Segura de Chaves de API")
    print("="*70)
    print("\nEste script cria um arquivo .env com suas chaves de forma segura.")
    print("O arquivo .env está no .gitignore e NÃO será enviado para o Git.\n")
    
    # Google Gemini
    print("1️⃣  GOOGLE GEMINI API KEY")
    print("-" * 70)
    print("   Obtenha em: https://aistudio.google.com/app/apikey")
    print("   Cole sua chave de API do Google:")
    gemini_key = input("   → ").strip()
    
    if not gemini_key:
        print("❌ Erro: Chave Gemini vazia!")
        return False
    
    # GitHub
    print("\n2️⃣  GITHUB TOKEN")
    print("-" * 70)
    print("   Obtenha em: https://github.com/settings/tokens")
    print("   Cole seu token (começará com 'ghp_' ou 'github_pat_'):")
    github_token = input("   → ").strip()
    
    if not github_token:
        print("❌ Erro: Token GitHub vazio!")
        return False
    
    # Cria o arquivo .env
    env_content = f"""# Chaves de API - NUNCA COMMITE ESTE ARQUIVO!
# Gerado automaticamente por setup_env.py

GOOGLE_API_KEY={gemini_key}
GITHUB_TOKEN={github_token}
"""
    
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        
        # Define permissões restritivas (apenas leitura/escrita do owner)
        os.chmod(env_path, 0o600)
        
        print("\n" + "="*70)
        print("✅ Arquivo .env criado com sucesso!")
        print("="*70)
        print(f"\n📁 Localização: {env_path.absolute()}")
        print("🔒 Permissões: Apenas leitura/escrita (600)")
        print("✓ Protegido no .gitignore")
        print("\nVocê pode executar o agente agora:")
        print("   python3 agent.py owner repo")
        print("\nOu instale as dependências primeiro:")
        print("   pip install -r requirements.txt\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar arquivo .env: {e}")
        return False

if __name__ == "__main__":
    try:
        success = setup_env()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Configuração cancelada pelo usuário.")
        sys.exit(1)
