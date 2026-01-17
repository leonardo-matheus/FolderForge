<p align="center">
  <img src="docs/assets/logo.svg" alt="FolderForge Logo" width="200"/>
</p>

<h1 align="center">🗂️ FolderForge</h1>

<p align="center">
  <strong>Organizador Inteligente de Pastas com IA</strong>
</p>

<p align="center">
  <a href="#-recursos">Recursos</a> •
  <a href="#-instalação">Instalação</a> •
  <a href="#-uso">Uso</a> •
  <a href="#-documentação">Documentação</a> •
  <a href="#-licença">Licença</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/versão-1.0.0-blue.svg" alt="Versão"/>
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/plataforma-Windows-lightgrey.svg" alt="Windows"/>
  <img src="https://img.shields.io/badge/licença-MIT-yellow.svg" alt="Licença"/>
</p>

<p align="center">
  <img src="docs/assets/demo.gif" alt="FolderForge Demo" width="700"/>
</p>

---

## ✨ O que é o FolderForge?

**FolderForge** é uma ferramenta poderosa que transforma pastas desorganizadas em estruturas limpas e padronizadas, usando inteligência artificial para entender o contexto dos seus arquivos.

Chega de perder tempo procurando arquivos! O FolderForge analisa, planeja e reorganiza suas pastas seguindo o padrão `[NN] Nome`, mantendo tudo em ordem.

## 🚀 Recursos

<table>
<tr>
<td width="50%">

### 🤖 IA Integrada
Sugestões inteligentes usando **Claude AI** para categorização contextual de pastas

### 📊 Análise Profunda
Score de conformidade, diagnóstico detalhado e relatórios visuais

### 🔄 Operações Seguras
Modo dry-run, backups automáticos e sistema de undo

</td>
<td width="50%">

### ⚡ Alta Performance
3-5x mais rápido com `os.scandir()` e processamento lazy

### 📝 Exportação Flexível
Scripts PowerShell, JSON e relatórios para auditoria

### 🛡️ Validações
Proteção contra caminhos inválidos e conflitos de nomes

</td>
</tr>
</table>

## 📥 Instalação

### Opção 1: Executável (Recomendado)

1. **Baixe** o `FolderForge.exe` da [página de releases](https://github.com/seu-usuario/FolderForge/releases)
2. **Copie** para a pasta que deseja organizar
3. **Execute** e siga as instruções

### Opção 2: Python

```powershell
# Clone o repositório
git clone https://github.com/seu-usuario/FolderForge.git
cd FolderForge/folder_organizer

# Instale as dependências
pip install -r requirements.txt

# Execute
python main.py
```

### Opção 3: Build Local

```powershell
cd folder_organizer
.\build_exe.ps1
```

## 💻 Uso

### Modo Interativo

Execute o programa e use os comandos:

```
╔══════════════════════════════════════════════════════════════╗
║                    COMANDOS DISPONÍVEIS                      ║
╠══════════════════════════════════════════════════════════════╣
║  ANALISAR <caminho>  │  Analisa estrutura da pasta           ║
║  DIAGNOSTICO         │  Mostra relatório de conformidade     ║
║  PLANO               │  Gera plano de reorganização          ║
║  PREVIEW             │  Mostra preview das operações         ║
║  SIMULAR             │  Executa dry-run (sem modificar)      ║
║  EXECUTAR            │  Executa reorganização                ║
║  DESFAZER            │  Reverte última operação              ║
║  EXPORTAR            │  Exporta script PowerShell            ║
║  JSON                │  Exporta análise em JSON              ║
║  IA                  │  Sugestões inteligentes com Claude    ║
║  AJUDA               │  Mostra ajuda                         ║
║  SAIR                │  Encerra programa                     ║
╚══════════════════════════════════════════════════════════════╝
```

### Linha de Comando

```powershell
# Análise rápida
python main.py --analyze "C:\MinhaPasta"

# Análise + exporta JSON
python main.py -a "C:\MinhaPasta" --json analysis.json

# Gera plano + simula
python main.py -a . --plan --dry-run

# Exporta script PowerShell
python main.py -a . --plan --export-script reorganize.ps1
```

## 📊 Padrão de Numeração

O FolderForge segue um padrão de numeração semântico:

| Faixa | Categoria | Descrição |
|-------|-----------|-----------|
| `[01] - [30]` | 🟢 **Ativas** | Pastas de uso frequente e projetos ativos |
| `[31] - [70]` | 🟡 **Suporte** | Documentação, referências e recursos |
| `[71] - [98]` | 🟠 **Temporárias** | Downloads, testes e arquivos temporários |
| `[99]` | 🔴 **Arquivados** | Projetos finalizados e backups |

### Exemplo de Estrutura

```
📁 Meu Trabalho/
├── 📁 [01] Projetos Ativos/
├── 📁 [02] Clientes/
├── 📁 [03] Desenvolvimento/
├── 📁 [31] Documentação/
├── 📁 [32] Templates/
├── 📁 [71] Downloads/
├── 📁 [72] Temp/
└── 📁 [99] Arquivados/
```

## 🔧 Configuração da IA

Para usar as funcionalidades de IA, configure o arquivo `.env`:

```env
AZURE_AI_KEY=sua-chave-aqui
AZURE_AI_ENDPOINT=https://seu-endpoint.services.ai.azure.com/anthropic/
AZURE_AI_MODEL=claude-opus-4-5
```

## 📖 Exemplo de Uso

```
[AGENTE] Digite comando: ANALISAR C:\Users\Leonardo\Trabalho

[ANÁLISE] Escaneando C:\Users\Leonardo\Trabalho...
[OK] Análise concluída em 0.45s

╔══════════════════════════════════════════════════════════════╗
║          RELATÓRIO DE ANÁLISE - ORGANIZAÇÃO DE PASTAS        ║
╠══════════════════════════════════════════════════════════════╣
║  Total de items:     245                                     ║
║  Pastas:             45                                      ║
║  Score:              35.0/100                                ║
╚══════════════════════════════════════════════════════════════╝

[AGENTE] Digite comando: PLANO

[PLANO] Gerando plano de reorganização...
[OK] Plano gerado com 32 operações

[AGENTE] Digite comando: EXECUTAR

⚠️  Confirma execução? (S/N): S
[EXECUTANDO] Fase 1...
  [OK] Desenvolvimento → [01] Desenvolvimento
  [OK] Quest Consult → [02] Quest Consult
  ...
[CONCLUÍDO] 32 sucesso, 0 falhas
```

## 🏗️ Estrutura do Projeto

```
FolderForge/
├── folder_organizer/
│   ├── main.py              # Interface principal
│   ├── folderforge_exe.py   # Versão standalone
│   ├── config.py            # Configurações globais
│   ├── build_exe.ps1        # Script de build
│   ├── core/
│   │   ├── analyzer.py      # Análise de estrutura
│   │   ├── planner.py       # Geração de planos
│   │   ├── executor.py      # Execução de operações
│   │   ├── ai_client.py     # Cliente Azure AI
│   │   └── models.py        # Estruturas de dados
│   ├── utils/
│   │   └── helpers.py       # Funções auxiliares
│   └── output/
│       └── backups/         # Backups automáticos
└── docs/
    └── index.html           # Landing page
```

## ⚡ Performance

| Otimização | Impacto |
|------------|---------|
| `os.scandir()` vs `os.walk()` | **3-5x mais rápido** |
| `__slots__` em dataclasses | **40% menos memória** |
| Regex pré-compilado | **2x mais rápido** em validações |
| Generators para lazy loading | **Memória constante** |
| Processamento bottom-up | **Zero conflitos** |

## 🔒 Segurança

- ✅ Modo **dry-run** por padrão
- ✅ **Confirmação** antes de executar
- ✅ Stack de **undo** para reversão
- ✅ **Log** de todas operações
- ✅ **Validação** de caminhos Windows
- ✅ **Backup** automático antes de mudanças

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos:

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">
  Feito com ❤️ para organizar sua vida digital
</p>

<p align="center">
  <a href="https://github.com/seu-usuario/FolderForge">⭐ Star no GitHub</a> •
  <a href="https://github.com/seu-usuario/FolderForge/issues">🐛 Reportar Bug</a> •
  <a href="https://github.com/seu-usuario/FolderForge/discussions">💬 Discussões</a>
</p>
