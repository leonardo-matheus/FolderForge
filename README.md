# FolderForge

Ferramenta em Python para analisar e reorganizar diretórios no Windows. Produz um plano de renomeação e movimentação para o padrão `[NN] Nome`, permite revisar operações em modo de simulação e pode consultar Claude via Azure AI Foundry para complementar regras locais.

## Escopo técnico

- varredura recursiva com `os.scandir` e coleta de metadados;
- classificação por nomes, extensões e prévia do conteúdo;
- numeração sequencial por diretório e detecção de conflitos;
- plano em fases de criação, renomeação e movimentação;
- execução por PowerShell ou APIs de filesystem do Python;
- `dry-run` habilitado por padrão no executor;
- exportação para PowerShell e JSON;
- integração opcional com Claude por `AnthropicFoundry`.

## Fluxo e arquitetura

`FolderAnalyzer` percorre a árvore e cria `FileItem` e `FolderAnalysis`. `ReorganizationPlanner` transforma a análise em operações ordenadas. `CommandExecutor` executa ou simula cada operação, registra resultados e mantém uma pilha de reversão durante o processo atual. `main.py` fornece o shell interativo; `folderforge_exe.py` concentra a interface do executável empacotado.

### Decisões observáveis

- a classificação determinística ocorre antes da consulta ao modelo, mantendo o fluxo básico utilizável sem IA;
- caminhos são passados ao PowerShell com `-LiteralPath`, reduzindo interpretação de curingas;
- a simulação usa o mesmo plano da execução e não altera o diretório de destino;
- há uma alternativa nativa com `pathlib` e `shutil`, embora a interface principal use PowerShell;
- o undo vive em memória e reverte renomeações e movimentos; não é transacional nem cobre todas as operações.

## Instalação

Requer Python 3.10 ou superior para a sintaxe de tipos utilizada no código.

```powershell
git clone https://github.com/leonardo-matheus/FolderForge.git
cd FolderForge\folder_organizer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "colorama>=0.4.6" "anthropic>=0.40.0" "python-dotenv>=1.0.0"
python main.py
```

O comando acima explicita as dependências porque `requirements.txt` contém o nome `anthopic` em vez de `anthropic`. A versão escolhida do SDK também precisa disponibilizar `AnthropicFoundry` para habilitar a integração com IA.

A integração com IA lê `AZURE_AI_KEY` e, opcionalmente, `AZURE_AI_ENDPOINT` do ambiente.

## Uso seguro

No shell interativo, o fluxo esperado é:

```text
ANALISAR C:\caminho\da\pasta
DIAGNOSTICO
PLANO
PREVIEW
SIMULAR
EXECUTAR
```

Use `SIMULAR` e revise os caminhos antes de `EXECUTAR`. A ferramenta modifica nomes e localizações com as permissões do usuário atual.

```powershell
python folderforge_exe.py --help
python folderforge_exe.py --path "C:\dados" --dry-run
python folderforge_exe.py --path "C:\dados" --export plano.ps1
.\build_exe.ps1
```

## Verificação

O repositório não contém uma suíte automatizada de testes. Antes de usar em dados relevantes, valide o plano contra uma cópia descartável e compare a saída do `dry-run`.

## Limites atuais

- o fluxo principal é orientado a Windows e PowerShell;
- a reversão não persiste entre execuções e não cobre criação ou exclusão;
- erros de permissão na varredura são ignorados, portanto a análise pode ser parcial;
- o limite de caminho considerado é o limite tradicional de 260 caracteres do Windows;
- sugestões de IA dependem de serviço externo e exigem revisão;
- `requirements.txt` registra `anthopic`, enquanto o código importa `anthropic`; a integração pode exigir corrigir o nome do pacote.

## Licença

MIT. Consulte [LICENSE](LICENSE).
