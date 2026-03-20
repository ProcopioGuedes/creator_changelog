"""
=============================================================
  Agente ReAct - Gerador de Changelog via GitHub API
  Disciplina: Engenharia de Software com IA Generativa
=============================================================

Implementa o ciclo ReAct (Reasoning + Acting):
  Thought → Action → Observation → Thought → ...

O agente percorre os commits de um repositório GitHub,
raciocina sobre as mudanças e gera um CHANGELOG.md estruturado.

Powered by: Google Gemini 2.0 Flash
"""

import os
import json
import requests
from typing import Any
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# ─────────────────────────────────────────────
# Cliente Google Gemini
# ─────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

MODEL = "models/gemini-2.5-flash"  # Modelo Gemini 2.5 Flash (rápido e eficiente)

# ─────────────────────────────────────────────
# Definição das Ferramentas (Tools)
# Usando o formato correto para API 0.8.3
# ─────────────────────────────────────────────
from google.generativeai import types

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_commits",
                description="Busca a lista de commits de um repositório GitHub. Retorna sha, mensagem, autor e data de cada commit.",
                parameters={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Dono do repositório (usuário ou org)"},
                        "repo": {"type": "string", "description": "Nome do repositório"},
                        "branch": {"type": "string", "description": "Branch alvo (padrão: main)"},
                        "since": {"type": "string", "description": "Data ISO 8601 de início (opcional)"},
                        "until": {"type": "string", "description": "Data ISO 8601 de fim (opcional)"},
                        "per_page": {"type": "integer", "description": "Commits por página (máx 100, padrão 30)"},
                    },
                    "required": ["owner", "repo"]
                },
            ),
            types.FunctionDeclaration(
                name="get_commit_detail",
                description="Retorna os detalhes completos de um commit específico, incluindo arquivos modificados.",
                parameters={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Dono do repositório"},
                        "repo": {"type": "string", "description": "Nome do repositório"},
                        "sha": {"type": "string", "description": "SHA completo ou abreviado do commit"},
                    },
                    "required": ["owner", "repo", "sha"]
                },
            ),
            types.FunctionDeclaration(
                name="get_releases",
                description="Busca as releases/tags do repositório para estruturar o changelog por versão.",
                parameters={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Dono do repositório"},
                        "repo": {"type": "string", "description": "Nome do repositório"},
                    },
                    "required": ["owner", "repo"]
                },
            ),
            types.FunctionDeclaration(
                name="get_repo_info",
                description="Retorna metadados do repositório: descrição, linguagem principal, estrelas, etc.",
                parameters={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Dono do repositório"},
                        "repo": {"type": "string", "description": "Nome do repositório"},
                    },
                    "required": ["owner", "repo"]
                },
            ),
            types.FunctionDeclaration(
                name="save_changelog",
                description="Salva o conteúdo Markdown do changelog em um arquivo local.",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Conteúdo Markdown do changelog"},
                        "filename": {"type": "string", "description": "Nome do arquivo (padrão: CHANGELOG.md)"},
                    },
                    "required": ["content"]
                },
            ),
        ]
    )
]


# ─────────────────────────────────────────────
# Implementação das Ferramentas
# ─────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def tool_get_commits(owner: str, repo: str, branch: str = "main",
                     since: str = None, until: str = None,
                     per_page: int = 30) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "per_page": min(per_page, 100)}
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    resp = requests.get(url, headers=_github_headers(), params=params, timeout=15)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

    commits = []
    for c in resp.json():
        commits.append({
            "sha":     c["sha"][:7],
            "sha_full": c["sha"],
            "message": c["commit"]["message"],
            "author":  c["commit"]["author"]["name"],
            "date":    c["commit"]["author"]["date"],
            "url":     c["html_url"],
        })
    return {"commits": commits, "total": len(commits)}


def tool_get_commit_detail(owner: str, repo: str, sha: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    resp = requests.get(url, headers=_github_headers(), timeout=15)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

    data = resp.json()
    files = []
    for f in data.get("files", [])[:20]:   # limita a 20 arquivos
        files.append({
            "filename":  f["filename"],
            "status":    f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "patch":     f.get("patch", "")[:500],  # trecho do diff
        })

    return {
        "sha":     data["sha"][:7],
        "message": data["commit"]["message"],
        "author":  data["commit"]["author"]["name"],
        "date":    data["commit"]["author"]["date"],
        "stats":   data.get("stats", {}),
        "files":   files,
    }


def tool_get_releases(owner: str, repo: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    resp = requests.get(url, headers=_github_headers(), timeout=15)
    if resp.status_code != 200:
        return {"releases": []}

    releases = []
    for r in resp.json()[:10]:
        releases.append({
            "tag":        r["tag_name"],
            "name":       r["name"],
            "published":  r["published_at"],
            "prerelease": r["prerelease"],
            "body":       (r.get("body") or "")[:300],
        })
    return {"releases": releases}


def tool_get_repo_info(owner: str, repo: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    resp = requests.get(url, headers=_github_headers(), timeout=15)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}"}

    d = resp.json()
    return {
        "name":        d["name"],
        "full_name":   d["full_name"],
        "description": d.get("description", ""),
        "language":    d.get("language", ""),
        "stars":       d["stargazers_count"],
        "forks":       d["forks_count"],
        "default_branch": d["default_branch"],
        "topics":      d.get("topics", []),
        "url":         d["html_url"],
    }


def tool_save_changelog(content: str, filename: str = "CHANGELOG.md") -> dict:
    path = os.path.join(os.getcwd(), filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"saved": True, "path": path, "size_bytes": len(content.encode())}


# ─────────────────────────────────────────────
# Dispatcher de Ferramentas
# ─────────────────────────────────────────────
TOOL_MAP = {
    "get_commits":      tool_get_commits,
    "get_commit_detail": tool_get_commit_detail,
    "get_releases":     tool_get_releases,
    "get_repo_info":    tool_get_repo_info,
    "save_changelog":   tool_save_changelog,
}

def run_tool(name: str, inputs: dict) -> Any:
    fn = TOOL_MAP.get(name)
    if not fn:
        return {"error": f"Ferramenta '{name}' não encontrada."}
    try:
        return fn(**inputs)
    except Exception as exc:
        return {"error": str(exc)}


# ─────────────────────────────────────────────
# System Prompt do Agente ReAct
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """
Você é um Agente ReAct especializado em Engenharia de Software.
Seu objetivo é analisar commits de repositórios GitHub e gerar um CHANGELOG.md
completo, bem estruturado e informativo.

## Ciclo ReAct que você deve seguir:
1. **Thought** – Raciocine sobre o que precisa fazer a seguir.
2. **Action** – Escolha e execute uma ferramenta.
3. **Observation** – Analise o resultado da ferramenta.
4. Repita até ter informações suficientes para gerar o changelog.

## Diretrizes para o CHANGELOG:
- Use o padrão [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
- Categorize as mudanças em: ✨ Added, 🐛 Fixed, 🔧 Changed, 🗑️ Removed, 🔒 Security, 📦 Dependencies
- Classifique commits usando Conventional Commits quando possível (feat, fix, chore, docs, refactor, test, ci)
- Inclua data, autor e SHA de cada commit
- Se houver releases/tags, agrupe os commits por versão
- O documento final deve estar 100% em Markdown válido

## Estratégia recomendada:
1. Obtenha informações do repositório (get_repo_info)
2. Busque releases para estruturar por versão (get_releases)
3. Liste os commits recentes (get_commits)
4. Para commits importantes, obtenha detalhes (get_commit_detail)
5. Gere e salve o CHANGELOG.md (save_changelog)

Seja detalhado nos pensamentos (Thought) e explique cada decisão.
"""


# ─────────────────────────────────────────────
# Loop Principal do Agente ReAct
# ─────────────────────────────────────────────
def run_agent(owner: str, repo: str, branch: str = "main",
              since: str = None, max_iterations: int = 15) -> str:
    """
    Executa o agente ReAct usando Google Gemini.
    Retorna o caminho do CHANGELOG.md gerado.
    """
    print(f"\n{'='*60}")
    print(f"  🤖 Agente ReAct - Gerador de Changelog  [Gemini {MODEL}]")
    print(f"  📦 Repositório : {owner}/{repo}  (branch: {branch})")
    print(f"  📅 Desde       : {since or 'início'}")
    print(f"{'='*60}\n")

    user_msg = (
        f"Analise o repositório GitHub '{owner}/{repo}' na branch '{branch}'"
        + (f" a partir de {since}" if since else "")
        + " e gere um CHANGELOG.md completo e detalhado seguindo as diretrizes."
        + " Salve o arquivo ao final."
    )

    iteration = 0
    changelog_path = None
    messages = []
    last_response_text = None  # Rastreia o último texto gerado

    while iteration < max_iterations:
        iteration += 1
        print(f"─── Iteração {iteration}/{max_iterations} ───────────────────────")

        # Primeira iteração: envia o prompt inicial
        if iteration == 1:
            messages.append({
                "role": "user",
                "parts": [user_msg]
            })
        
        # Chama o modelo com as ferramentas
        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
        )
        
        response = model.generate_content(
            messages,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=4096,
            ),
            stream=False
        )
        
        # Exibe o raciocínio (Thought) se houver texto
        try:
            if response.text:
                last_response_text = response.text.strip()
                print(f"\n💭 THOUGHT:\n{last_response_text}\n")
        except:
            # Se houver erro ao extrair texto, continua
            pass
        
        # Adiciona resposta ao histórico (formato correto para API 0.8.3)
        messages.append({
            "role": "model",
            "parts": response.parts
        })

        # Verifica se há chamadas de ferramenta
        tool_calls_made = False
        tool_results = []
        
        for part in response.parts:
            if part.function_call:
                tool_calls_made = True
                fn_name = part.function_call.name
                fn_inputs = dict(part.function_call.args)

                print(f"⚡ ACTION: {fn_name}({json.dumps(fn_inputs, ensure_ascii=False)[:120]})")

                result = run_tool(fn_name, fn_inputs)

                result_preview = json.dumps(result, ensure_ascii=False)[:300]
                print(f"👁️  OBSERVATION: {result_preview}{'...' if len(str(result)) > 300 else ''}\n")

                # Detecta se o changelog foi salvo
                if fn_name == "save_changelog" and result.get("saved"):
                    changelog_path = result["path"]
                
                # Adiciona resultado ao histórico
                tool_results.append({
                    "name": fn_name,
                    "response": result
                })
        
        # Se houve tool calls, adiciona os resultados ao histórico
        if tool_calls_made and tool_results:
            # Adiciona respostas das ferramentas no formato correto para API 0.8.3
            for tr in tool_results:
                messages.append({
                    "role": "user",
                    "parts": [{
                        "function_response": {
                            "name": tr["name"],
                            "response": tr["response"]
                        }
                    }]
                })
        
        # Condição de parada: modelo terminou sem chamar ferramentas
        if not tool_calls_made:
            print(f"\n✅ Agente concluiu após {iteration} iterações.")
            
            # Se o agente gerou um CHANGELOG mas não salvou, salvamos automaticamente
            if last_response_text and "CHANGELOG" in last_response_text and not changelog_path:
                print("\n⚠️  Agente não chamou save_changelog. Salvando automaticamente...")
                changelog_path = tool_save_changelog(last_response_text, "CHANGELOG.md")
                print(f"📄 Arquivo salvo em: {changelog_path['path']}")
            
            break

    # Retorna o caminho do arquivo ou mensagem padrão
    if isinstance(changelog_path, dict):
        return changelog_path.get("path", "CHANGELOG.md")
    return changelog_path or "CHANGELOG.md"


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    # Leitura dos parâmetros
    if len(sys.argv) >= 3:
        OWNER  = sys.argv[1]
        REPO   = sys.argv[2]
        BRANCH = sys.argv[3] if len(sys.argv) > 3 else "main"
        SINCE  = sys.argv[4] if len(sys.argv) > 4 else None
    else:
        # Valores padrão para demonstração
        OWNER  = input("GitHub owner/usuário: ").strip()
        REPO   = input("Nome do repositório : ").strip()
        BRANCH = input("Branch (Enter = main): ").strip() or "main"
        SINCE  = input("Desde (ISO 8601, opcional): ").strip() or None

    path = run_agent(OWNER, REPO, BRANCH, SINCE)
    print(f"\n📄 Changelog salvo em: {path}")
