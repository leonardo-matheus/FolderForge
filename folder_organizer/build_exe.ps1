# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT DE BUILD - Gera o executável FolderForge.exe
# ══════════════════════════════════════════════════════════════════════════════
#
# Uso:
#   .\build_exe.ps1
#
# Requisitos:
#   - Python 3.8+
#   - pip install pyinstaller colorama
#
# ══════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║            FOLDER FORGE - BUILD EXECUTÁVEL                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verifica se está no diretório correto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Verifica Python
Write-Host "[1/4] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Python não encontrado!" -ForegroundColor Red
    exit 1
}
Write-Host "       $pythonVersion" -ForegroundColor Green

# Instala dependências
Write-Host "[2/4] Instalando dependências..." -ForegroundColor Yellow
pip install pyinstaller colorama --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Falha ao instalar dependências!" -ForegroundColor Red
    exit 1
}
Write-Host "       Dependências instaladas" -ForegroundColor Green

# Limpa builds anteriores
Write-Host "[3/4] Limpando builds anteriores..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }
Write-Host "       Limpeza concluída" -ForegroundColor Green

# Gera o executável
Write-Host "[4/4] Gerando executável..." -ForegroundColor Yellow

$pyInstallerArgs = @(
    "--onefile",                          # Um único arquivo exe
    "--console",                          # Mostra console (necessário para interação)
    "--name=FolderForge",                 # Nome do exe
    "--clean",                            # Limpa cache
    "--noconfirm",                        # Não pergunta confirmação
    "--add-data=core;core",               # Inclui módulo core
    "--add-data=config.py;.",             # Inclui config
    "--hidden-import=colorama",           # Importa colorama
    "--hidden-import=core.analyzer",      # Importa módulos core
    "--hidden-import=core.planner",
    "--hidden-import=core.executor",
    "--hidden-import=core.models",
    "--hidden-import=core.ai_client",
    "folderforge_exe.py"                  # Script principal
)

pyinstaller @pyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Falha ao gerar executável!" -ForegroundColor Red
    exit 1
}

# Verifica se exe foi criado
$exePath = "dist\FolderForge.exe"
if (Test-Path $exePath) {
    $fileSize = (Get-Item $exePath).Length / 1MB
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                    BUILD CONCLUÍDO!                          ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Executável: $exePath" -ForegroundColor Cyan
    Write-Host "  Tamanho: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  COMO USAR:" -ForegroundColor Yellow
    Write-Host "  1. Copie FolderForge.exe para a pasta que deseja organizar" -ForegroundColor White
    Write-Host "  2. Execute o FolderForge.exe" -ForegroundColor White
    Write-Host "  3. Siga as instruções na tela" -ForegroundColor White
    Write-Host ""
    
    # Abre a pasta dist
    explorer.exe "dist"
} else {
    Write-Host "[ERRO] Executável não foi criado!" -ForegroundColor Red
    exit 1
}
