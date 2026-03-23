# 📋 Documentação Simplificada

## 🚀 Setup Rápido

Para configurar o ambiente, execute:

```bash
python setup_environment.py
```

Isso irá:
1. Criar ambiente virtual (venv)
2. Instalar dependências
3. Criar arquivo `.env`
4. Validar instalação

**Tempo total:** ~30 segundos

---

## 📝 Configurar Chaves

Após o setup, edite o arquivo `.env`:

```bash
nano .env
```

Adicione suas chaves:
- `GOOGLE_API_KEY` - Obtenha em https://aistudio.google.com/app/apikeys
- `GITHUB_TOKEN` - Obtenha em https://github.com/settings/tokens (opcional)

---

## 🐍 Usar o Agent

1. Ative o ambiente:
   ```bash
   source venv/bin/activate     # Linux/macOS
   venv\Scripts\activate.bat     # Windows
   ```

2. Execute:
   ```bash
   python agent.py
   ```

3. Ou com parâmetros:
   ```bash
   python agent.py microsoft vscode main 2024-01-01T00:00:00Z
   ```

---

## 📚 Documentação Completa

- **README.md** - Documentação principal do projeto
- **INSTALL.md** - Guia de instalação rápido
- Outras documentações em arquivos `.md` específicos

---

**Status:** ✅ Pronto para usar
