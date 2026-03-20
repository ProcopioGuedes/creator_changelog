# 🤖 Agente ReAct — Gerador de Changelog GitHub

> **Trabalho Prático — Engenharia de Software com IA Generativa**  
> Implementação de um Agente ReAct (Reasoning + Acting) aplicado a Engenharia de Software  
> **Powered by:** Google Gemini 2.0 Flash ⚡

---

## � ⚠️ CONFIGURAÇÃO SEGURA DE CHAVES DE API

**Antes de usar, configure suas chaves de forma segura!**

### Opção 1: Script Interativo (Recomendado)
```bash
source venv/bin/activate
python3 setup_env.py
```

### Opção 2: Manual
1. Copie `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edite `.env` com suas chaves:
   ```
   GOOGLE_API_KEY=sua_chave_gemini_aqui
   GITHUB_TOKEN=seu_token_github_aqui
   ```

**Nunca commite o arquivo `.env` — ele está no `.gitignore`!**

---

## �📋 Visão Geral

Este projeto implementa um **Agente de IA baseado na técnica ReAct** que analisa automaticamente
os commits de um repositório GitHub e gera um `CHANGELOG.md` estruturado, categorizado e detalhado.

### Fluxo ReAct

```
┌─────────────────────────────────────────────────────────────┐
│                     CICLO ReAct                             │
│                                                             │
│   Pergunta ──► THOUGHT (raciocínio) ──► ACTION (ferramenta)│
│                     ▲                        │              │
│                     │                        ▼              │
│                     └──── OBSERVATION (resultado) ◄────────┘│
│                                                             │
│   Repete até ter informações suficientes para gerar o       │
│   CHANGELOG e salvá-lo em disco.                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Ferramentas do Agente

| Ferramenta | Descrição |
|---|---|
| `get_repo_info` | Metadados do repositório (linguagem, estrelas, etc.) |
| `get_releases` | Releases e tags para estruturar por versão |
| `get_commits` | Lista de commits com filtros por data/branch |
| `get_commit_detail` | Detalhes de um commit (arquivos, diff, estatísticas) |
| `save_changelog` | Salva o CHANGELOG.md gerado em disco |

---

## ⚙️ Instalação

### Pré-requisitos
- Python 3.10+
- Conta OpenAI (API Key)
- Token GitHub (opcional, mas recomendado para evitar rate limit)

### Passos

```bash
# 1. Clone ou copie os arquivos do projeto
cd changelog_agent

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
export OPENAI_API_KEY="sk-proj-..."
export OPENAI_MODEL="gpt-4.1"     # opcional
export GITHUB_TOKEN="ghp_..."        # opcional, mas evita rate limit
```

---

## 🚀 Uso

### Modo Interativo

```bash
python agent.py
```

O agente pedirá os dados do repositório:
```
GitHub owner/usuário: microsoft
Nome do repositório : vscode
Branch (Enter = main): main
Desde (ISO 8601, opcional): 2024-01-01T00:00:00Z
```

### Modo por Linha de Comando

```bash
python agent.py <owner> <repo> [branch] [since]

# Exemplos:
python agent.py microsoft vscode main
python agent.py facebook react main 2024-06-01T00:00:00Z
python agent.py torvalds linux master 2025-01-01T00:00:00Z
```

---

## 📄 Formato do CHANGELOG Gerado

O agente gera um `CHANGELOG.md` seguindo o padrão
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) com categorias baseadas
em [Conventional Commits](https://www.conventionalcommits.org/):

| Categoria | Prefixo de Commit |
|---|---|
| ✨ **Added** | `feat:` |
| 🐛 **Fixed** | `fix:` |
| 🔧 **Changed** | `refactor:`, `perf:`, `style:` |
| 🗑️ **Removed** | commits com breaking changes |
| 🔒 **Security** | `security:` ou patches CVE |
| 📦 **Dependencies** | `chore:`, `deps:` |
| 📝 **Docs** | `docs:` |

---

## 🏗️ Arquitetura

```
changelog_agent/
├── agent.py               # Agente ReAct principal
├── requirements.txt       # Dependências Python
├── README.md              # Esta documentação
├── CHANGELOG.example.md   # Exemplo de saída gerada
└── CHANGELOG.md           # Gerado na execução
```

### Componentes Principais

**`agent.py`** contém:
- `TOOLS` — Definição das ferramentas no formato JSON Schema (Anthropic Tool Use)
- `tool_*` — Implementações reais que chamam a GitHub REST API v3
- `run_tool()` — Dispatcher que mapeia nome → função
- `run_agent()` — Loop ReAct com histórico de mensagens
- `SYSTEM_PROMPT` — Instruções para o modelo seguir o padrão ReAct

---

## 🔬 Conceitos de IA Aplicados

### ReAct (Reasoning + Acting)
O agente intercala **pensamento** (`Thought`) com **ações** (`Action`) e analisa **observações** (`Observation`),
permitindo raciocínio encadeado e adaptativo.

### Tool Use / Function Calling
O modelo chama ferramentas externas (GitHub API) de forma estruturada, recebendo resultados
reais para embasar suas decisões — não há alucinações sobre dados do repositório.

### Chain of Thought
O `SYSTEM_PROMPT` induz o modelo a explicitar seu raciocínio antes de agir,
aumentando a qualidade e auditabilidade das decisões.

### Memória Conversacional
O histórico completo de `messages` é mantido a cada iteração, dando ao agente
contexto acumulado sobre tudo que já coletou.

---

## 📊 Exemplo de Saída no Terminal

```
============================================================
  🤖 Agente ReAct - Gerador de Changelog
  📦 Repositório : microsoft/vscode  (branch: main)
  📅 Desde       : 2025-01-01T00:00:00Z
============================================================

─── Iteração 1/15 ──────────────────────────────────────
💭 THOUGHT:
Preciso primeiro entender o repositório. Vou obter suas informações gerais.

⚡ ACTION: get_repo_info({"owner": "microsoft", "repo": "vscode"})
👁️  OBSERVATION: {"name": "vscode", "language": "TypeScript", "stars": 165000 ...}

─── Iteração 2/15 ──────────────────────────────────────
💭 THOUGHT:
Agora vou buscar as releases para estruturar o changelog por versão.

⚡ ACTION: get_releases({"owner": "microsoft", "repo": "vscode"})
...

✅ Agente concluiu após 8 iterações.
📄 Changelog salvo em: /path/to/CHANGELOG.md
```

---

## 📝 Observações Técnicas

- O agente usa o modelo **`claude-opus-4-5`** via API Anthropic
- A GitHub API tem rate limit de **60 req/hora** sem token e **5.000 req/hora** com token
- O `max_iterations=15` evita loops infinitos; ajuste conforme necessário
- Commits com diffs muito grandes são truncados a 500 caracteres por arquivo

---

*Projeto desenvolvido para a disciplina de Engenharia de Software com IA Generativa*

**Por:**

Fernanda Guimarães Costa

Monica de Faria Silva

Procópio Victor Lacerda Guedes

# creator_changelog
