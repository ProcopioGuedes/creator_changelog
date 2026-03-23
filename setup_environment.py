#!/usr/bin/env python3
"""
================================================================================
  🚀 Script de Configuração de Ambiente - Agente ReAct Changelog
  
  Este script configura um ambiente virtual Python completo e pronto para
  usar o agent em qualquer máquina (Windows, macOS, Linux).
  
  Uso: python setup_environment.py
================================================================================
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Tuple, Optional

# ANSI Color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    
    # Fallback para Windows
    @staticmethod
    def disable_on_windows():
        if platform.system() == 'Windows':
            Colors.RED = ''
            Colors.GREEN = ''
            Colors.YELLOW = ''
            Colors.BLUE = ''
            Colors.NC = ''

Colors.disable_on_windows()

# Funções de output
def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.NC}")

# =============================================================================
# 1. VERIFICAR PYTHON
# =============================================================================
def check_python() -> bool:
    """Verifica se Python 3.10+ está instalado"""
    print_header("1️⃣  Verificando Python")
    
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 10):
        print_warning(f"Python 3.10+ é recomendado. Você tem Python {version_str}")
        response = input("Deseja continuar mesmo assim? (s/n): ").lower().strip()
        if response != 's':
            return False
    
    print_success(f"Python {version_str} encontrado")
    return True

# =============================================================================
# 2. VERIFICAR VENV
# =============================================================================
def check_venv() -> bool:
    """Verifica se o módulo venv está disponível"""
    print_header("2️⃣  Verificando venv")
    
    try:
        import venv
        print_success("venv disponível")
        return True
    except ImportError:
        print_error("Módulo venv não disponível!")
        print("Instale com:")
        if platform.system() == "Windows":
            print("  Reinstale Python marcando 'pip' na instalação")
        else:
            print("  Ubuntu/Debian: sudo apt-get install python3-venv")
            print("  macOS: brew install python3")
        return False

# =============================================================================
# 3. PREPARAR DIRETÓRIO
# =============================================================================
def prepare_directory() -> bool:
    """Prepara o diretório para criar venv"""
    print_header("3️⃣  Preparando diretório")
    
    venv_dir = Path("venv")
    
    if venv_dir.exists():
        print_warning("Ambiente virtual existente encontrado")
        response = input("Deseja removê-lo e criar um novo? (s/n): ").lower().strip()
        
        if response == 's':
            try:
                print_info(f"Removendo {venv_dir}...")
                shutil.rmtree(venv_dir)
                print_success("Diretório removido")
            except Exception as e:
                print_error(f"Erro ao remover diretório: {e}")
                return False
        else:
            print_info("Usando ambiente existente")
    else:
        print_info("Nenhum ambiente virtual encontrado")
    
    return True

# =============================================================================
# 4. CRIAR VENV
# =============================================================================
def create_venv() -> bool:
    """Cria o ambiente virtual"""
    print_header("4️⃣  Criando ambiente virtual")
    
    venv_dir = Path("venv")
    
    if not venv_dir.exists():
        try:
            print_info("Criando virtual environment em venv/...")
            import venv as venv_module
            venv_module.create(str(venv_dir), with_pip=True)
            print_success("Ambiente virtual criado")
        except Exception as e:
            print_error(f"Erro ao criar venv: {e}")
            return False
    else:
        print_info("Usando ambiente virtual existente")
    
    return True

# =============================================================================
# 5. OBTER PATHS
# =============================================================================
def get_venv_paths() -> Tuple[str, str, str]:
    """Obtém os caminhos do venv para o sistema operacional"""
    venv_dir = Path("venv")
    
    if platform.system() == "Windows":
        python_exe = str(venv_dir / "Scripts" / "python.exe")
        pip_exe = str(venv_dir / "Scripts" / "pip.exe")
        activate_cmd = str(venv_dir / "Scripts" / "activate.bat")
    else:  # Linux e macOS
        python_exe = str(venv_dir / "bin" / "python")
        pip_exe = str(venv_dir / "bin" / "pip")
        activate_cmd = str(venv_dir / "bin" / "activate")
    
    return python_exe, pip_exe, activate_cmd

# =============================================================================
# 6. ATUALIZAR PIP
# =============================================================================
def upgrade_pip(pip_exe: str) -> bool:
    """Atualiza pip, setuptools e wheel"""
    print_header("5️⃣  Atualizando pip")
    
    try:
        print_info("Atualizando pip, setuptools e wheel...")
        subprocess.run(
            [pip_exe, "install", "--upgrade", "pip", "setuptools", "wheel"],
            check=True,
            capture_output=True
        )
        print_success("pip atualizado")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao atualizar pip: {e}")
        return False

# =============================================================================
# 7. INSTALAR REQUIREMENTS
# =============================================================================
def install_requirements(pip_exe: str) -> bool:
    """Instala as dependências do requirements.txt"""
    print_header("6️⃣  Instalando dependências")
    
    req_file = Path("requirements.txt")
    
    if not req_file.exists():
        print_error("Arquivo requirements.txt não encontrado!")
        return False
    
    try:
        print_info("Instalando pacotes de requirements.txt...")
        subprocess.run(
            [pip_exe, "install", "-r", str(req_file)],
            check=True
        )
        print_success("Dependências instaladas")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao instalar dependências: {e}")
        return False

# =============================================================================
# 8. VERIFICAR INSTALAÇÃO
# =============================================================================
def verify_installation(python_exe: str) -> bool:
    """Verifica se os pacotes críticos foram instalados"""
    print_header("7️⃣  Verificando instalação")
    
    packages = [
        ("google.generativeai", "google-generativeai"),
        ("requests", "requests"),
        ("dotenv", "python-dotenv"),
    ]
    
    print_info("Verificando imports críticos...")
    
    all_ok = True
    for import_name, package_name in packages:
        try:
            subprocess.run(
                [python_exe, "-c", f"import {import_name}"],
                check=True,
                capture_output=True
            )
            print(f"  {Colors.GREEN}✓ {package_name}{Colors.NC}")
        except subprocess.CalledProcessError:
            print(f"  {Colors.RED}✗ {package_name}{Colors.NC}")
            all_ok = False
    
    if all_ok:
        print_success("Todos os pacotes críticos estão instalados")
    else:
        print_error("Alguns pacotes não foram instalados corretamente")
    
    return all_ok

# =============================================================================
# 9. CONFIGURAR .ENV
# =============================================================================
def setup_env_file() -> bool:
    """Configura o arquivo .env"""
    print_header("8️⃣  Configurando .env")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_warning("Arquivo .env já existe")
        response = input("Deseja criar um novo .env (sobrescrevendo)? (s/n): ").lower().strip()
        
        if response != 's':
            print_info("Usando .env existente")
            print_info("Variáveis configuradas em .env:")
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key = line.split('=')[0]
                            print(f"  {key}=***")
            except:
                pass
            return True
    
    if env_example.exists():
        print_info("Copiando .env.example para .env...")
        try:
            shutil.copy(str(env_example), str(env_file))
            print_success(".env criado")
        except Exception as e:
            print_error(f"Erro ao copiar arquivo: {e}")
            return False
    else:
        print_info("Criando .env com template...")
        env_template = """# Configuração do Agente ReAct - Gerador de Changelog
# ⚠️  NUNCA commite este arquivo - ele está no .gitignore!

# Chave da API Google Gemini
# Obtenha em: https://aistudio.google.com/app/apikeys
GOOGLE_API_KEY=sua_chave_gemini_aqui

# Token GitHub (opcional, mas recomendado para evitar rate limit)
# Gere em: https://github.com/settings/tokens
GITHUB_TOKEN=seu_token_github_aqui
"""
        try:
            with open(env_file, 'w') as f:
                f.write(env_template)
            print_success(".env criado com template")
        except Exception as e:
            print_error(f"Erro ao criar .env: {e}")
            return False
    
    print()
    print_warning("⚠️  IMPORTANTE: Configure suas chaves em .env:")
    print("   GOOGLE_API_KEY=sua_chave_gemini_aqui")
    print("   GITHUB_TOKEN=seu_token_github_aqui (opcional)")
    print()
    
    return True

# =============================================================================
# 10. TESTAR AGENT
# =============================================================================
def test_agent(python_exe: str) -> bool:
    """Testa se o agent pode ser importado"""
    print_header("9️⃣  Testando agent")
    
    try:
        print_info("Testando importação do agent...")
        result = subprocess.run(
            [python_exe, "-c", "import agent; print('✓ Agent importado com sucesso')"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Agent está pronto para usar!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao importar agent: {e.stderr}")
        return False

# =============================================================================
# 11. RESUMO FINAL
# =============================================================================
def print_summary(activate_cmd: str):
    """Imprime resumo final com instruções"""
    print_header("✨ Configuração Completa!")
    
    print(f"{Colors.GREEN}Ambiente virtual criado e configurado com sucesso!{Colors.NC}\n")
    
    print(f"{Colors.BLUE}Próximos passos:{Colors.NC}\n")
    
    if platform.system() == "Windows":
        print("1️⃣  Ativar o ambiente virtual:")
        print(f"   {Colors.GREEN}venv\\Scripts\\activate.bat{Colors.NC}\n")
    else:
        print("1️⃣  Ativar o ambiente virtual:")
        print(f"   {Colors.GREEN}source venv/bin/activate{Colors.NC}\n")
    
    print("2️⃣  Configurar suas chaves de API no .env:")
    print(f"   {Colors.GREEN}nano .env{Colors.NC}\n")
    
    print("3️⃣  Executar o agent:")
    print(f"   {Colors.GREEN}python agent.py{Colors.NC}\n")
    
    print("4️⃣  Ou passar parâmetros:")
    print(f"   {Colors.GREEN}python agent.py microsoft vscode main{Colors.NC}\n")
    
    print(f"{Colors.YELLOW}Dicas:{Colors.NC}")
    print("• Para novos terminais, ative com: source venv/bin/activate (Linux/macOS)")
    print("                                    ou venv\\Scripts\\activate (Windows)")
    print("• Nunca commite o arquivo .env (está no .gitignore)")
    print("• Veja README.md para mais informações")
    print()

# =============================================================================
# MAIN
# =============================================================================
def main():
    """Função principal"""
    try:
        # 1. Verificar Python
        if not check_python():
            sys.exit(1)
        
        # 2. Verificar venv
        if not check_venv():
            sys.exit(1)
        
        # 3. Preparar diretório
        if not prepare_directory():
            sys.exit(1)
        
        # 4. Criar venv
        if not create_venv():
            sys.exit(1)
        
        # 5. Obter paths
        python_exe, pip_exe, activate_cmd = get_venv_paths()
        
        # 6. Atualizar pip
        if not upgrade_pip(pip_exe):
            sys.exit(1)
        
        # 7. Instalar requirements
        if not install_requirements(pip_exe):
            sys.exit(1)
        
        # 8. Verificar instalação
        verify_installation(python_exe)
        
        # 9. Configurar .env
        if not setup_env_file():
            sys.exit(1)
        
        # 10. Testar agent
        test_agent(python_exe)
        
        # 11. Resumo final
        print_summary(activate_cmd)
        
    except KeyboardInterrupt:
        print("\n")
        print_error("Configuração cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print("\n")
        print_error(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
