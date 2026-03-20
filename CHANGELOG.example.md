# Changelog

Todas as mudanças notáveis deste projeto serão documentadas aqui.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### ✨ Added
- Nenhuma adição pendente.

---

## [2.1.0] - 2025-03-10

### ✨ Added
- `feat: add user authentication module` — **João Silva** (`a3f8d21`) [2025-03-10]
  - Arquivos: `src/auth/login.py` (+142 linhas), `src/auth/jwt_handler.py` (+87 linhas)
  - Implementação de autenticação JWT com refresh token
- `feat: implement dark mode toggle` — **Maria Santos** (`b9c1e45`) [2025-03-09]
  - Arquivos: `src/ui/theme.css` (+56 linhas), `src/ui/settings.js` (+23 linhas)

### 🐛 Fixed
- `fix: resolve memory leak in WebSocket connections` — **Carlos Oliveira** (`d7a2f03`) [2025-03-08]
  - Arquivos: `src/network/ws_manager.py` (−34 linhas, +12 linhas)
  - Correção de referências circulares no gerenciador de conexões
- `fix: correct date parsing for PT-BR locale` — **Ana Lima** (`e1b8c92`) [2025-03-07]
  - Arquivos: `src/utils/date_parser.py` (+8 linhas)

### 🔧 Changed
- `refactor: migrate from SQLite to PostgreSQL` — **Pedro Costa** (`f5d3a18`) [2025-03-06]
  - Arquivos: `src/db/connection.py`, `src/db/models.py`, `migrations/001_postgres.sql`
  - Melhoria de performance em consultas complexas (~40% mais rápido)

### 📦 Dependencies
- `chore: bump anthropic to 0.45.0` — **João Silva** (`c4e7b30`) [2025-03-05]

---

## [2.0.1] - 2025-02-20

### 🐛 Fixed
- `fix: hotfix login redirect loop` — **Maria Santos** (`9a1d4f7`) [2025-02-20]
  - Correção crítica de loop infinito no fluxo de autenticação
- `fix: handle empty API response gracefully` — **Carlos Oliveira** (`8b2c5e1`) [2025-02-18]

### 🔒 Security
- `security: patch XSS vulnerability in comment renderer` — **Ana Lima** (`7f3e9a2`) [2025-02-17]
  - CVE-2025-1234: sanitização de HTML em campos de comentário

---

## [2.0.0] - 2025-02-01

> ⚠️ **Breaking Changes** — Veja o [Guia de Migração](docs/migration-v2.md)

### ✨ Added
- `feat!: complete API v2 redesign` — **Pedro Costa** (`2c8b4d9`) [2025-02-01]
  - Nova arquitetura REST com versionamento de endpoints
  - Documentação OpenAPI 3.0 gerada automaticamente
- `feat: add real-time notifications via WebSocket` — **João Silva** (`3d9e5c1`) [2025-01-30]
- `feat: multi-tenant support` — **Maria Santos** (`4e0f6d2`) [2025-01-28]

### 🗑️ Removed
- `feat!: remove deprecated v1 API endpoints` — **Pedro Costa** (`5f1a7e3`) [2025-02-01]
  - Endpoints removidos: `/api/v1/users`, `/api/v1/auth`, `/api/v1/data`

### 🔧 Changed
- `refactor: rewrite frontend in React 19` — **Carlos Oliveira** (`6a2b8f4`) [2025-01-25]
- `chore: update CI/CD pipeline to GitHub Actions` — **Ana Lima** (`7b3c9a5`) [2025-01-22]

---

## [1.5.2] - 2025-01-10

### 🐛 Fixed
- `fix: resolve race condition in async task queue` — **João Silva** (`1a2b3c4`) [2025-01-10]
- `fix: correct timezone offset calculation` — **Maria Santos** (`2b3c4d5`) [2025-01-08]

### 📦 Dependencies
- `chore: security updates for all dependencies` — **Carlos Oliveira** (`3c4d5e6`) [2025-01-07]

---

## [1.5.0] - 2024-12-15

### ✨ Added
- `feat: add export to PDF functionality` — **Ana Lima** (`4d5e6f7`) [2024-12-15]
- `feat: implement full-text search` — **Pedro Costa** (`5e6f7a8`) [2024-12-12]
- `docs: add API documentation in Portuguese` — **João Silva** (`6f7a8b9`) [2024-12-10]

### 🔧 Changed
- `perf: optimize database queries with indexing` — **Maria Santos** (`7a8b9c0`) [2024-12-08]
  - Redução de 60% no tempo de resposta das listagens principais

---

*Gerado automaticamente pelo **Agente ReAct Changelog** em 2025-03-17*  
*Repositório: [owner/repo](https://github.com/owner/repo)*
