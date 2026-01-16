#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           FOLDER FORGE - EXE                                 ║
║                    Organizador de Pastas Automático                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Coloque este executável na pasta que deseja organizar e execute.
O programa irá:
1. Analisar a estrutura da pasta
2. Gerar um plano de reorganização
3. Perguntar se deseja executar
4. Executar as mudanças (com backup automático)

"""
import sys
import os
import time
import argparse
from pathlib import Path

# Quando rodando como exe, ajusta o path
if getattr(sys, 'frozen', False):
    # Rodando como exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Rodando como script
    BASE_DIR = Path(__file__).parent

# Adiciona o diretório ao path para imports
sys.path.insert(0, str(BASE_DIR))

# Agora importa os módulos
try:
    from core import FolderAnalyzer, ReorganizationPlanner, CommandExecutor
    from core.models import FolderAnalysis, ReorganizationPlan
except ImportError as e:
    print(f"[ERRO] Falha ao importar modulos: {e}")
    input("Pressione ENTER para sair...")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# CORES PARA TERMINAL
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    OK = ''
    WARN = ''
    ERR = ''
    INFO = ''
    RESET = ''
    BOLD = ''

try:
    from colorama import init, Fore, Style
    init()
    Colors.OK = Fore.GREEN
    Colors.WARN = Fore.YELLOW
    Colors.ERR = Fore.RED
    Colors.INFO = Fore.CYAN
    Colors.RESET = Style.RESET_ALL
    Colors.BOLD = Style.BRIGHT
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES PRINCIPAIS
# ══════════════════════════════════════════════════════════════════════════════

def print_banner():
    """Exibe banner do programa."""
    print(f"""
{Colors.INFO}╔══════════════════════════════════════════════════════════════════╗
║                                                                    ║
║   ███████╗ ██████╗ ██╗     ██████╗ ███████╗██████╗                ║
║   ██╔════╝██╔═══██╗██║     ██╔══██╗██╔════╝██╔══██╗               ║
║   █████╗  ██║   ██║██║     ██║  ██║█████╗  ██████╔╝               ║
║   ██╔══╝  ██║   ██║██║     ██║  ██║██╔══╝  ██╔══██╗               ║
║   ██║     ╚██████╔╝███████╗██████╔╝███████╗██║  ██║               ║
║   ╚═╝      ╚═════╝ ╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝               ║
║                                                                    ║
║   ███████╗ ██████╗ ██████╗  ██████╗ ███████╗                      ║
║   ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝                      ║
║   █████╗  ██║   ██║██████╔╝██║  ███╗█████╗                        ║
║   ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝                        ║
║   ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗                      ║
║   ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝                      ║
║                                                                    ║
║              Organizador Inteligente de Pastas v1.0               ║
╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}
""")


def print_section(title: str):
    """Exibe título de seção."""
    print(f"\n{Colors.INFO}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.INFO}{'═' * 60}{Colors.RESET}")


def get_target_folder() -> Path:
    """
    Determina a pasta alvo para organização.
    Usa a pasta onde o exe está localizado.
    """
    if getattr(sys, 'frozen', False):
        # Exe: usa a pasta onde o exe está
        return Path(sys.executable).parent
    else:
        # Script: usa pasta atual
        return Path.cwd()


def analyze_folder(target_path: Path) -> tuple:
    """Analisa a pasta e retorna analyzer e analysis."""
    print(f"\n{Colors.INFO}[1/3] ANALISANDO PASTA...{Colors.RESET}")
    print(f"      Caminho: {target_path}")
    
    start_time = time.perf_counter()
    
    try:
        analyzer = FolderAnalyzer(str(target_path))
        analysis = analyzer.analyze()
        
        elapsed = time.perf_counter() - start_time
        print(f"{Colors.OK}      Análise concluída em {elapsed:.2f}s{Colors.RESET}")
        
        return analyzer, analysis
    
    except Exception as e:
        print(f"{Colors.ERR}[ERRO] Falha na análise: {e}{Colors.RESET}")
        return None, None


def generate_plan(analysis: FolderAnalysis) -> ReorganizationPlan:
    """Gera plano de reorganização."""
    print(f"\n{Colors.INFO}[2/3] GERANDO PLANO DE REORGANIZAÇÃO...{Colors.RESET}")
    
    try:
        planner = ReorganizationPlanner(analysis)
        plan = planner.generate_plan()
        
        print(f"{Colors.OK}      Plano gerado: {plan.total_operations} operações{Colors.RESET}")
        print(planner.get_plan_preview(max_items=15))
        
        return plan
    
    except Exception as e:
        print(f"{Colors.ERR}[ERRO] Falha ao gerar plano: {e}{Colors.RESET}")
        return None


def execute_plan(plan: ReorganizationPlan, target_path: Path, dry_run: bool = False):
    """Executa o plano de reorganização."""
    mode = "SIMULANDO" if dry_run else "EXECUTANDO"
    print(f"\n{Colors.INFO}[3/3] {mode} PLANO...{Colors.RESET}")
    
    try:
        # CommandExecutor recebe dry_run no construtor, não o plano
        executor = CommandExecutor(dry_run=dry_run, use_powershell=True)
        
        # execute_plan retorna (sucesso, falhas)
        success, failures = executor.execute_plan(plan)
        
        if dry_run:
            print(f"\n{Colors.OK}[SIMULAÇÃO CONCLUÍDA]{Colors.RESET}")
            print(f"  Operações simuladas: {success}")
        else:
            print(f"\n{Colors.OK}[EXECUÇÃO CONCLUÍDA]{Colors.RESET}")
            print(f"  Sucesso: {success}")
            print(f"  Falhas: {failures}")
            
            if failures > 0:
                print(f"\n{Colors.WARN}[AVISO] Algumas operações falharam.{Colors.RESET}")
            
            # Mostra relatório detalhado
            print(executor.get_execution_report())
        
        return True
    
    except Exception as e:
        print(f"{Colors.ERR}[ERRO] Falha na execução: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False


def export_script(plan: ReorganizationPlan, target_path: Path):
    """Exporta plano como script PowerShell."""
    script_path = target_path / "FolderForge_Reorganizar.ps1"
    
    try:
        planner = ReorganizationPlanner.__new__(ReorganizationPlanner)
        planner._plan = plan
        planner.export_plan_to_script(script_path)
        
        print(f"\n{Colors.OK}[EXPORTADO] Script salvo em:{Colors.RESET}")
        print(f"  {script_path}")
        return True
    except Exception as e:
        print(f"{Colors.ERR}[ERRO] Falha ao exportar: {e}{Colors.RESET}")
        return False


def confirm_action(message: str) -> bool:
    """Pede confirmação do usuário."""
    while True:
        response = input(f"\n{Colors.WARN}{message} (S/N): {Colors.RESET}").strip().upper()
        if response in ('S', 'SIM', 'Y', 'YES'):
            return True
        elif response in ('N', 'NAO', 'NO'):
            return False
        print("  Digite S para Sim ou N para Não")


def main():
    """Função principal."""
    print_banner()
    
    # Determina pasta alvo
    target_path = get_target_folder()
    
    print_section("PASTA ALVO")
    print(f"  {target_path}")
    
    # Análise
    print_section("ANÁLISE")
    analyzer, analysis = analyze_folder(target_path)
    
    if not analysis:
        input("\nPressione ENTER para sair...")
        return 1
    
    # Mostra relatório
    if analyzer:
        print(analyzer.get_report())
    
    # Verifica se há algo para fazer
    non_conformant = sum(1 for item in analysis.items if not item.is_conformant)
    
    if non_conformant == 0:
        print(f"\n{Colors.OK}[OK] Pasta já está organizada! Nada a fazer.{Colors.RESET}")
        input("\nPressione ENTER para sair...")
        return 0
    
    # Gerar plano
    print_section("PLANO DE REORGANIZAÇÃO")
    plan = generate_plan(analysis)
    
    if not plan or plan.total_operations == 0:
        print(f"\n{Colors.OK}[OK] Nenhuma operação necessária.{Colors.RESET}")
        input("\nPressione ENTER para sair...")
        return 0
    
    # Menu de opções
    print_section("OPÇÕES")
    print(f"""
  {Colors.BOLD}[1]{Colors.RESET} Simular execução (dry-run) - Ver o que aconteceria
  {Colors.BOLD}[2]{Colors.RESET} Executar reorganização - Aplicar mudanças
  {Colors.BOLD}[3]{Colors.RESET} Exportar script PowerShell - Salvar para revisar
  {Colors.BOLD}[0]{Colors.RESET} Sair sem fazer nada
""")
    
    while True:
        choice = input(f"{Colors.INFO}Escolha uma opção (0-3): {Colors.RESET}").strip()
        
        if choice == '0':
            print(f"\n{Colors.INFO}[INFO] Saindo sem modificações.{Colors.RESET}")
            break
        
        elif choice == '1':
            execute_plan(plan, target_path, dry_run=True)
        
        elif choice == '2':
            if confirm_action("ATENÇÃO: Isso irá modificar arquivos. Deseja continuar?"):
                execute_plan(plan, target_path, dry_run=False)
                print(f"\n{Colors.OK}[CONCLUÍDO] Reorganização finalizada!{Colors.RESET}")
                break
        
        elif choice == '3':
            export_script(plan, target_path)
        
        else:
            print(f"{Colors.WARN}  Opção inválida. Digite 0, 1, 2 ou 3.{Colors.RESET}")
    
    input("\nPressione ENTER para sair...")
    return 0


def parse_args():
    """Parse argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description='FolderForge - Organizador Inteligente de Pastas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos:
  FolderForge.exe                    # Modo interativo
  FolderForge.exe --auto             # Executa automaticamente sem perguntar
  FolderForge.exe --dry-run          # Apenas simula (não modifica nada)
  FolderForge.exe --export           # Exporta script PowerShell
'''
    )
    parser.add_argument('--auto', '-a', action='store_true',
                        help='Executa automaticamente sem confirmação')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Apenas simula, não modifica arquivos')
    parser.add_argument('--export', '-e', action='store_true',
                        help='Exporta plano como script PowerShell')
    parser.add_argument('--no-pause', action='store_true',
                        help='Não espera ENTER no final')
    return parser.parse_args()


def main_cli(args):
    """Execução via linha de comando (automática)."""
    print_banner()
    
    target_path = get_target_folder()
    
    print_section("PASTA ALVO")
    print(f"  {target_path}")
    
    # Análise
    print_section("ANÁLISE")
    analyzer, analysis = analyze_folder(target_path)
    
    if not analysis:
        if not args.no_pause:
            input("\nPressione ENTER para sair...")
        return 1
    
    # Mostra relatório
    if analyzer:
        print(analyzer.get_report())
    
    # Verifica se há algo para fazer
    non_conformant = sum(1 for item in analysis.items if not item.is_conformant)
    
    if non_conformant == 0:
        print(f"\n{Colors.OK}[OK] Pasta já está organizada! Nada a fazer.{Colors.RESET}")
        if not args.no_pause:
            input("\nPressione ENTER para sair...")
        return 0
    
    # Gerar plano
    print_section("PLANO DE REORGANIZAÇÃO")
    plan = generate_plan(analysis)
    
    if not plan or plan.total_operations == 0:
        print(f"\n{Colors.OK}[OK] Nenhuma operação necessária.{Colors.RESET}")
        if not args.no_pause:
            input("\nPressione ENTER para sair...")
        return 0
    
    # Exportar script?
    if args.export:
        export_script(plan, target_path)
    
    # Executar
    if args.auto or args.dry_run:
        execute_plan(plan, target_path, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"\n{Colors.OK}[CONCLUÍDO] Reorganização finalizada!{Colors.RESET}")
    
    if not args.no_pause:
        input("\nPressione ENTER para sair...")
    return 0


if __name__ == '__main__':
    try:
        args = parse_args()
        
        # Se tem argumentos de automação, usa modo CLI
        if args.auto or args.dry_run or args.export:
            sys.exit(main_cli(args))
        else:
            # Modo interativo
            sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARN}[CANCELADO] Operação cancelada pelo usuário.{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.ERR}[ERRO FATAL] {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para sair...")
        sys.exit(1)
