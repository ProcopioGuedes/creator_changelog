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
            types.FunctionDeclaration(
                name="analyze_commit_changes",
                description="Analisa os diffs reais de um commit para extrair um resumo inteligente das mudanças realizadas.",
                parameters={
                    "type": "object",
                    "properties": {
                        "commit_message": {"type": "string", "description": "Mensagem original do commit"},
                        "files_info": {"type": "string", "description": "Informações dos arquivos modificados (JSON serializado com nomes, status, adições/deletions, patches)"},
                        "stats": {"type": "string", "description": "Estatísticas do commit (JSON com total de linhas adicionadas/deletadas)"},
                    },
                    "required": ["commit_message", "files_info"]
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
    total_additions = 0
    total_deletions = 0
    
    for f in data.get("files", [])[:30]:   # aumentou de 20 para 30 arquivos
        patch_preview = f.get("patch", "")[:800]  # aumentou de 500 para 800 caracteres
        file_info = {
            "filename":  f["filename"],
            "status":    f["status"],  # added, modified, removed, renamed, etc.
            "additions": f["additions"],
            "deletions": f["deletions"],
            "changes":   f["changes"],
            "patch":     patch_preview,  # trecho do diff real
        }
        files.append(file_info)
        total_additions += f["additions"]
        total_deletions += f["deletions"]

    return {
        "sha":     data["sha"][:7],
        "sha_full": data["sha"],
        "message": data["commit"]["message"],
        "author":  data["commit"]["author"]["name"],
        "date":    data["commit"]["author"]["date"],
        "stats":   data.get("stats", {}),
        "files_changed": len(data.get("files", [])),
        "total_additions": total_additions,
        "total_deletions": total_deletions,
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


def tool_analyze_commit_changes(commit_message: str, files_info: str, stats: str = None) -> dict:
    """
    Analisa os diffs reais de um commit usando Gemini para extrair insights sobre as mudanças.
    Retorna um resumo estruturado das alterações realizadas.
    """
    analysis_prompt = f"""
Analise este commit do GitHub e forneça um resumo PRECISO e ACERTIVO das mudanças:

📝 Mensagem do Commit:
{commit_message}

📊 Arquivos Modificados:
{files_info}

{"📈 Estatísticas:" + stats if stats else ""}

Por favor, analise os diffs e forneça:
1. **Categoria**: feat (feature), fix (bug fix), refactor, docs, test, style, chore, perf
2. **Resumo Executivo**: Uma linha descrevendo exatamente o que foi mudado (baseado nos diffs, não só na mensagem)
3. **Detalhes Técnicos**: Quais arquivos foram impactados e como (seja específico)
4. **Impacto**: Se há breaking changes, dependências alteradas, ou mudanças críticas
5. **Confidence**: Nível de confiança na categorização (high/medium/low)

Responda em JSON estruturado.
"""
    
    try:
        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction="Você é um expert em análise de código. Analise commits GitHub baseado em diffs reais para extrair insights precisos."
        )
        
        response = model.generate_content(
            analysis_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1024,
            )
        )
        
        # Extrai JSON da resposta
        response_text = response.text.strip()
        
        # Tenta extrair JSON se houver markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        try:
            analysis = json.loads(response_text)
        except json.JSONDecodeError:
            # Se não conseguir parsear JSON, retorna o texto como resposta
            analysis = {"raw_analysis": response_text}
        
        return {"success": True, "analysis": analysis}
    
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ─────────────────────────────────────────────
# Dispatcher de Ferramentas
# ─────────────────────────────────────────────
TOOL_MAP = {
    "get_commits":           tool_get_commits,
    "get_commit_detail":     tool_get_commit_detail,
    "get_releases":          tool_get_releases,
    "get_repo_info":         tool_get_repo_info,
    "save_changelog":        tool_save_changelog,
    "analyze_commit_changes": tool_analyze_commit_changes,
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
Você é um Agente ReAct especializado em Engenharia de Software e Análise de Código.
Seu objetivo é analisar commits de repositórios GitHub E SEUS DIFFS REAIS, para gerar 
um CHANGELOG.md completo, bem estruturado, preciso e informativo.

## Ciclo ReAct que você deve seguir:
1. **Thought** – Raciocine sobre o que precisa fazer a seguir.
2. **Action** – Escolha e execute uma ferramenta.
3. **Observation** – Analise o resultado da ferramenta.
4. Repita até ter informações suficientes para gerar o changelog.

## ⚠️ IMPORTANTE - Análise de Diffs:
- NÃO confie apenas na mensagem do commit para categorizar mudanças
- SEMPRE use get_commit_detail para obter os diffs reais dos arquivos
- SEMPRE use analyze_commit_changes para analisar inteligentemente o que foi mudado
- A análise de diffs garante maior acertividade e qualidade do CHANGELOG

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
4. Para CADA commit, obtenha detalhes COMPLETOS (get_commit_detail) para analisar:
   - Arquivos modificados (filenames, status, additions/deletions)
   - Patches/diffs reais para entender EXATAMENTE o que mudou
   - Use essas informações para resumir as mudanças de forma precisa
5. Gere e salve o CHANGELOG.md (save_changelog)

## Análise de Diffs:
- Não confie apenas na mensagem do commit
- Analise os patches para identificar:
  - Funcionalidades realmente adicionadas (feat)
  - Bugs realmente corrigidos (fix)
  - Refatorações e melhorias de código
  - Impacto nas dependências
  - Mudanças de segurança
- Combine a mensagem + análise de diff para categorização precisa

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
