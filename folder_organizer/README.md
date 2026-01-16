# 📁 Agente de Organização de Pastas Inteligente

Ferramenta de linha de comando para reorganizar pastas seguindo o padrão `[NN] Nome`.

## 🚀 Instalação Rápida

```powershell
cd folder_organizer
pip install -r requirements.txt
python main.py
```

## 📋 Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `ANALISAR <caminho>` | Analisa estrutura da pasta |
| `DIAGNOSTICO` | Mostra relatório de conformidade |
| `PLANO` | Gera plano de reorganização |
| `PREVIEW` | Mostra preview das operações |
| `SIMULAR` | Executa dry-run (sem modificar) |
| `EXECUTAR` | Executa reorganização |
| `DESFAZER` | Reverte última operação |
| `EXPORTAR` | Exporta script PowerShell |
| `JSON` | Exporta análise em JSON |
| `AJUDA` | Mostra ajuda |
| `SAIR` | Encerra programa |

## 💻 Uso

### Modo Interativo
```powershell
python main.py
```

### Linha de Comando
```powershell
# Análise rápida
python main.py --analyze "C:\Users\Leonardo\Trabalho"

# Análise + exporta JSON
python main.py -a "C:\Users\Leonardo\Trabalho" --json analysis.json

# Gera plano + simula
python main.py -a . --plan --dry-run

# Exporta script PowerShell
python main.py -a . --plan --export-script reorganize.ps1
```

## 📊 Padrão de Numeração

```
[01] - [30]   Pastas ativas/frequentes
[31] - [70]   Pastas suporte/referência  
[71] - [98]   Pastas temporárias
[99]          Arquivados
```

## 🔧 Estrutura do Projeto

```
folder_organizer/
├── main.py          # Interface principal
├── config.py        # Configurações globais
├── core/
│   ├── analyzer.py  # Análise de estrutura
│   ├── planner.py   # Geração de planos
│   ├── executor.py  # Execução de operações
│   └── models.py    # Estruturas de dados
├── utils/
│   └── helpers.py   # Funções auxiliares
└── output/          # Logs e backups
```

## ⚡ Otimizações de Performance

- `os.scandir()` em vez de `os.walk()` (3-5x mais rápido)
- `__slots__` em dataclasses (40% menos memória)
- Regex pré-compilado
- Generators para processamento lazy
- Processamento bottom-up para evitar conflitos

## 🔒 Segurança

- Modo dry-run por padrão
- Confirmação antes de executar
- Stack de undo para reversão
- Log de todas operações
- Validação de caminhos Windows

## 📝 Exemplo de Fluxo

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

[AGENTE] Digite comando: SIMULAR

[SIMULAÇÃO] 32 operações
  [DRY-RUN] Desenvolvimento → [01] Desenvolvimento
  [DRY-RUN] Quest Consult → [02] Quest Consult
  ...

[AGENTE] Digite comando: EXECUTAR

⚠️  Confirma execução? (S/N): S
[EXECUTANDO] Fase 1...
  [OK] Desenvolvimento → [01] Desenvolvimento
  [OK] Quest Consult → [02] Quest Consult
  ...
[CONCLUÍDO] 32 sucesso, 0 falhas
```

## 📄 Licença

MIT License
