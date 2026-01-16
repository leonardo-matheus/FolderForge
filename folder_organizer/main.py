#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
+==============================================================================+
|                    AGENTE DE ORGANIZACAO DE PASTAS                           |
|                         Versao Otimizada v1.0                                |
+==============================================================================+

Uso:
    python main.py                      # Modo interativo
    python main.py --analyze <caminho>  # Análise direta
    python main.py --help               # Ajuda

Autor: Agente IA
"""
from __future__ import annotations
import sys
import os
import argparse
import time
from pathlib import Path
from typing import Optional

# Carrega variaveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setup de cores para Windows
class Colors:
    """Cores para terminal."""
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

from core import FolderAnalyzer, ReorganizationPlanner, CommandExecutor
from core.models import FolderAnalysis, ReorganizationPlan
from core.ai_client import AIClient, AIConfig


class FolderOrganizerAgent:
    """
    Agente principal de organização de pastas.
    Interface interativa e de linha de comando.
    """
    
    COMMANDS = {
        'ANALISAR': 'Analisa uma pasta e gera relatorio',
        'DIAGNOSTICO': 'Mostra diagnostico da ultima analise',
        'PLANO': 'Gera plano de reorganizacao',
        'PREVIEW': 'Mostra preview das operacoes',
        'EXECUTAR': 'Executa o plano (com confirmacao)',
        'SIMULAR': 'Simula execucao (dry-run)',
        'DESFAZER': 'Desfaz ultima operacao',
        'EXPORTAR': 'Exporta plano como script PowerShell',
        'JSON': 'Exporta analise como JSON',
        'IA': 'Usa Claude AI para sugestoes inteligentes',
        'AJUDA': 'Mostra esta ajuda',
        'SAIR': 'Encerra o programa',
    }
    
    def __init__(self):
        self._analysis: Optional[FolderAnalysis] = None
        self._plan: Optional[ReorganizationPlan] = None
        self._executor: Optional[CommandExecutor] = None
        self._analyzer: Optional[FolderAnalyzer] = None
        self._ai_client: Optional[AIClient] = None
        self._init_ai_client()
    
    def _init_ai_client(self):
        """Inicializa cliente de IA se credenciais disponiveis."""
        api_key = os.environ.get('AZURE_AI_KEY')
        endpoint = os.environ.get('AZURE_AI_ENDPOINT')
        model = os.environ.get('AZURE_AI_MODEL', 'claude-opus-4-5')
        
        if api_key:
            try:
                config = AIConfig(
                    api_key=api_key,
                    endpoint=endpoint or "https://conta-ma6t6uyn-eastus2.services.ai.azure.com/anthropic/",
                    model=model
                )
                self._ai_client = AIClient(config)
            except Exception as e:
                print(f"{Colors.WARN}[AI] Falha ao inicializar: {e}{Colors.RESET}")
    
    def run_interactive(self):
        """Modo interativo com menu de comandos."""
        self._print_banner()
        
        while True:
            try:
                cmd_input = input(f"\n{Colors.INFO}[AGENTE]{Colors.RESET} Digite comando: ").strip()
                
                if not cmd_input:
                    continue
                
                parts = cmd_input.split(maxsplit=1)
                command = parts[0].upper()
                args = parts[1] if len(parts) > 1 else None
                
                if command == 'SAIR' or command == 'EXIT':
                    print(f"{Colors.INFO}[AGENTE] Encerrando...{Colors.RESET}")
                    break
                
                self._handle_command(command, args)
            
            except KeyboardInterrupt:
                print(f"\n{Colors.WARN}[INTERROMPIDO]{Colors.RESET}")
                continue
            
            except Exception as e:
                print(f"{Colors.ERR}[ERRO] {e}{Colors.RESET}")
    
    def _handle_command(self, command: str, args: Optional[str]):
        """Processa comando do usuário."""
        
        if command == 'ANALISAR':
            if not args:
                args = input("  Caminho da pasta: ").strip()
            self._cmd_analyze(args)
        
        elif command == 'DIAGNOSTICO':
            self._cmd_diagnostico()
        
        elif command == 'PLANO':
            self._cmd_gerar_plano()
        
        elif command == 'PREVIEW':
            self._cmd_preview()
        
        elif command == 'EXECUTAR':
            self._cmd_executar(dry_run=False)
        
        elif command == 'SIMULAR':
            self._cmd_executar(dry_run=True)
        
        elif command == 'DESFAZER':
            self._cmd_desfazer()
        
        elif command == 'EXPORTAR':
            self._cmd_exportar(args)
        
        elif command == 'JSON':
            self._cmd_json(args)
        
        elif command == 'IA':
            self._cmd_ia(args)
        
        elif command == 'AJUDA' or command == 'HELP':
            self._cmd_ajuda()
        
        else:
            print(f"{Colors.WARN}[AVISO] Comando desconhecido: {command}{Colors.RESET}")
            print("  Digite AJUDA para ver comandos disponíveis")
    
    def _cmd_analyze(self, path: str):
        """Comando: ANALISAR <caminho>"""
        if not path:
            print(f"{Colors.ERR}[ERRO] Caminho não especificado{Colors.RESET}")
            return
        
        # Expande ~ para home directory
        path = str(Path(path).expanduser())
        
        print(f"{Colors.INFO}[ANÁLISE] Escaneando {path}...{Colors.RESET}")
        
        start_time = time.perf_counter()
        
        try:
            self._analyzer = FolderAnalyzer(path)
            self._analysis = self._analyzer.analyze()
            self._plan = None  # Reset plano anterior
            
            elapsed = time.perf_counter() - start_time
            
            print(f"{Colors.OK}[OK] Análise concluída em {elapsed:.2f}s{Colors.RESET}")
            print(self._analyzer.get_report())
        
        except FileNotFoundError as e:
            print(f"{Colors.ERR}[ERRO] {e}{Colors.RESET}")
        except PermissionError:
            print(f"{Colors.ERR}[ERRO] Sem permissão para acessar pasta{Colors.RESET}")
    
    def _cmd_diagnostico(self):
        """Comando: DIAGNOSTICO"""
        if not self._analysis:
            print(f"{Colors.WARN}[AVISO] Execute ANALISAR primeiro{Colors.RESET}")
            return
        
        if self._analyzer:
            print(self._analyzer.get_report())
        
        # Lista pastas não conformes
        non_conformant = self._analyzer.get_non_conformant_folders() if self._analyzer else []
        
        if non_conformant:
            print(f"\n{Colors.WARN}[PASTAS QUE PRECISAM AJUSTE]{Colors.RESET}")
            print("-" * 60)
            
            for i, folder in enumerate(non_conformant[:15], 1):
                print(f"  {i:2}. {folder.name:<30} → {folder.suggested_name}")
            
            if len(non_conformant) > 15:
                print(f"  ... e mais {len(non_conformant) - 15} pastas")
    
    def _cmd_gerar_plano(self):
        """Comando: PLANO"""
        if not self._analysis:
            print(f"{Colors.WARN}[AVISO] Execute ANALISAR primeiro{Colors.RESET}")
            return
        
        print(f"{Colors.INFO}[PLANO] Gerando plano de reorganização...{Colors.RESET}")
        
        if not self._analysis:
            return
        planner = ReorganizationPlanner(self._analysis)
        self._plan = planner.generate_plan()
        
        print(f"{Colors.OK}[OK] Plano gerado com {self._plan.total_operations} operações{Colors.RESET}")
        print(planner.get_plan_preview())
    
    def _cmd_preview(self):
        """Comando: PREVIEW"""
        if not self._plan:
            print(f"{Colors.WARN}[AVISO] Execute PLANO primeiro{Colors.RESET}")
            return
        
        if not self._analysis:
            return
        planner = ReorganizationPlanner(self._analysis)
        planner._plan = self._plan
        print(planner.get_plan_preview(max_items=50))
    
    def _cmd_executar(self, dry_run: bool = True, auto: bool = False):
        """Comando: EXECUTAR ou SIMULAR"""
        if not self._plan:
            print(f"{Colors.WARN}[AVISO] Execute PLANO primeiro{Colors.RESET}")
            return
        
        mode = "SIMULACAO" if dry_run else "EXECUCAO"
        
        print(f"\n{Colors.BOLD}[{mode}] {self._plan.total_operations} operacoes{Colors.RESET}")
        
        if not dry_run and not auto:
            confirm = input(f"{Colors.WARN}[ATENCAO] Confirma execucao? (S/N): {Colors.RESET}").strip().upper()
            if confirm != 'S':
                print(f"{Colors.INFO}[CANCELADO]{Colors.RESET}")
                return
        
        self._executor = CommandExecutor(dry_run=dry_run, use_powershell=True)
        
        start_time = time.perf_counter()
        success, failures = self._executor.execute_plan(self._plan)
        elapsed = time.perf_counter() - start_time
        
        print(f"\n{Colors.OK}[CONCLUIDO] em {elapsed:.2f}s{Colors.RESET}")
        print(self._executor.get_execution_report())
    
    def _cmd_desfazer(self):
        """Comando: DESFAZER"""
        if not self._executor:
            print(f"{Colors.WARN}[AVISO] Nenhuma operação para desfazer{Colors.RESET}")
            return
        
        self._executor.undo_last()
    
    def _cmd_exportar(self, output_path: Optional[str]):
        """Comando: EXPORTAR [caminho]"""
        if not self._plan:
            print(f"{Colors.WARN}[AVISO] Execute PLANO primeiro{Colors.RESET}")
            return
        
        path = Path(output_path) if output_path else Path('./reorganize_script.ps1')
        
        planner = ReorganizationPlanner(self._analysis)
        planner._plan = self._plan
        
        if planner.export_plan_to_script(path):
            print(f"{Colors.OK}[OK] Script exportado: {path}{Colors.RESET}")
        else:
            print(f"{Colors.ERR}[ERRO] Falha ao exportar{Colors.RESET}")
    
    def _cmd_json(self, output_path: Optional[str]):
        """Comando: JSON [caminho]"""
        if not self._analysis:
            print(f"{Colors.WARN}[AVISO] Execute ANALISAR primeiro{Colors.RESET}")
            return
        
        path = Path(output_path) if output_path else Path('./analysis.json')
        
        path.write_text(self._analysis.to_json(), encoding='utf-8')
        print(f"{Colors.OK}[OK] JSON exportado: {path}{Colors.RESET}")
    
    def _cmd_ia(self, mode: Optional[str] = None):
        """Comando: IA [analise|plano|sugestao]"""
        if not self._ai_client or not self._ai_client.is_enabled:
            print(f"{Colors.ERR}[ERRO] Cliente AI nao configurado{Colors.RESET}")
            print(f"  Configure AZURE_AI_KEY no arquivo .env")
            return
        
        if not self._analysis:
            print(f"{Colors.WARN}[AVISO] Execute ANALISAR primeiro{Colors.RESET}")
            return
        
        mode = (mode or 'analise').lower()
        
        if mode == 'analise':
            print(f"{Colors.INFO}[IA] Analisando com Claude Opus 4.5...{Colors.RESET}")
            
            # Pega pastas nao conformes
            folders = self._analyzer.get_non_conformant_folders() if self._analyzer else []
            
            if not folders:
                print(f"{Colors.OK}[IA] Todas as pastas ja estao organizadas!{Colors.RESET}")
                return
            
            result = self._ai_client.analyze_folders(folders[:20])  # Limita a 20
            
            if 'error' in result:
                print(f"{Colors.ERR}[IA-ERRO] {result['error']}{Colors.RESET}")
                return
            
            if 'sugestoes' in result:
                print(f"\n{Colors.OK}[IA] Sugestoes de organizacao:{Colors.RESET}")
                print("-" * 60)
                for sug in result['sugestoes']:
                    nome_atual = sug.get('nome_atual', '?')
                    nome_novo = sug.get('nome_novo', '?')
                    razao = sug.get('razao', '')
                    print(f"  {nome_atual:<25} -> {nome_novo}")
                    if razao:
                        print(f"    Razao: {razao}")
                
                if 'score_potencial' in result:
                    print(f"\n  Score potencial: {result['score_potencial']}/100")
            else:
                print(f"{Colors.INFO}[IA] Resposta:{Colors.RESET}")
                print(result.get('raw_response', str(result))[:500])
        
        elif mode == 'plano':
            print(f"{Colors.INFO}[IA] Gerando plano inteligente...{Colors.RESET}")
            result = self._ai_client.generate_reorganization_plan(self._analysis)
            
            if 'error' in result:
                print(f"{Colors.ERR}[IA-ERRO] {result['error']}{Colors.RESET}")
            elif 'plano' in result:
                print(f"\n{Colors.OK}[IA] Plano gerado:{Colors.RESET}")
                for item in result['plano'][:10]:
                    print(f"  {item.get('de', '?')} -> {item.get('para', '?')}")
            else:
                print(result.get('raw_response', str(result))[:500])
        
        else:
            print(f"{Colors.WARN}[AVISO] Modo invalido. Use: IA analise | IA plano{Colors.RESET}")
    
    def _cmd_ajuda(self):
        """Comando: AJUDA"""
        print(f"\n{Colors.BOLD}COMANDOS DISPONIVEIS:{Colors.RESET}")
        print("-" * 50)
        
        for cmd, desc in self.COMMANDS.items():
            print(f"  {Colors.INFO}{cmd:<12}{Colors.RESET} {desc}")
        
        print(f"\n{Colors.BOLD}EXEMPLOS:{Colors.RESET}")
        print("  ANALISAR C:\\Users\\Leonardo\\Trabalho")
        print("  ANALISAR ~/Documents")
        print("  IA analise    (usa Claude para sugestoes)")
        print("  IA plano      (gera plano com IA)")
        print("  SIMULAR")
        print("  EXECUTAR")
    
    def _print_banner(self):
        """Imprime banner inicial."""
        ai_status = f"{Colors.OK}[AI OK]{Colors.RESET}" if (self._ai_client and self._ai_client.is_enabled) else f"{Colors.WARN}[AI OFF]{Colors.RESET}"
        
        print(f"""
{Colors.BOLD}+==============================================================+
|     {Colors.INFO}AGENTE DE ORGANIZACAO DE PASTAS INTELIGENTE{Colors.RESET}{Colors.BOLD}           |
|                    Versao Otimizada v1.0                     |
+--------------------------------------------------------------+
|  Padrao: [NN] Nome_Pasta                                     |
|  [01]-[30] Ativas | [31]-[70] Suporte | [71]-[99] Temp/Arq   |
+--------------------------------------------------------------+
|  Claude Opus 4.5: {ai_status:<43}{Colors.BOLD}|
+==============================================================+{Colors.RESET}

{Colors.INFO}Digite AJUDA para ver comandos disponiveis.{Colors.RESET}
""")


def run_cli():
    """Execucao via linha de comando."""
    parser = argparse.ArgumentParser(
        description='Agente de Organizacao de Pastas Inteligente',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py                                    # Modo interativo
  python main.py -a "C:\\pasta" --auto              # AUTOMATICO: analisa e organiza
  python main.py -a "C:\\pasta" --plan --dry-run    # Simula sem executar
  python main.py -a "C:\\pasta" --plan --execute    # Executa com confirmacao
        """
    )
    
    parser.add_argument(
        '-a', '--analyze',
        metavar='PATH',
        help='Caminho da pasta para analisar'
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='AUTOMATICO: analisa, planeja e executa sem confirmacao'
    )
    
    parser.add_argument(
        '--json',
        metavar='FILE',
        help='Exporta analise para arquivo JSON'
    )
    
    parser.add_argument(
        '--plan',
        action='store_true',
        help='Gera plano de reorganizacao'
    )
    
    parser.add_argument(
        '--export-script',
        metavar='FILE',
        help='Exporta plano como script PowerShell'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula execucao sem modificar arquivos'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Executa reorganizacao (CUIDADO!)'
    )
    
    args = parser.parse_args()
    
    # Se nenhum argumento, modo interativo
    if len(sys.argv) == 1:
        agent = FolderOrganizerAgent()
        agent.run_interactive()
        return
    
    # Modo CLI
    if args.analyze:
        agent = FolderOrganizerAgent()
        agent._cmd_analyze(args.analyze)
        
        if args.json:
            agent._cmd_json(args.json)
        
        # MODO AUTOMATICO: faz tudo sem perguntar
        if args.auto:
            agent._cmd_gerar_plano()
            if agent._plan and agent._plan.total_operations > 0:
                agent._cmd_executar(dry_run=False, auto=True)
            else:
                print(f"{Colors.OK}[OK] Nenhuma operacao necessaria{Colors.RESET}")
            return
        
        if args.plan:
            agent._cmd_gerar_plano()
            
            if args.export_script:
                agent._cmd_exportar(args.export_script)
            
            if args.dry_run:
                agent._cmd_executar(dry_run=True)
            
            elif args.execute:
                agent._cmd_executar(dry_run=False)


if __name__ == '__main__':
    run_cli()
