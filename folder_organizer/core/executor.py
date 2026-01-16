"""
Executor de operações - Executa comandos no sistema de arquivos.

Características:
- Modo dry-run por padrão (segurança)
- Stack de undo para reversão
- Logging de todas operações
- Execução via PowerShell ou nativa
"""
from __future__ import annotations
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable
import json

from .models import Operation, OperationType, OperationStatus, ReorganizationPlan
from config import OUTPUT_DIR, LOG_FILE, BACKUP_DIR


class CommandExecutor:
    """
    Executor de operações no sistema de arquivos.
    """
    __slots__ = (
        'dry_run', 'use_powershell', '_executed', '_undo_stack',
        '_log_file', '_on_progress'
    )
    
    def __init__(
        self,
        dry_run: bool = True,
        use_powershell: bool = True,
        on_progress: Optional[Callable[[str], None]] = None
    ):
        self.dry_run = dry_run
        self.use_powershell = use_powershell
        self._executed: List[Operation] = []
        self._undo_stack: List[Operation] = []
        self._on_progress = on_progress or print
        self._log_file: Optional[Path] = None
        
        # Cria diretórios de output
        self._setup_output_dirs()
    
    def _setup_output_dirs(self):
        """Cria diretórios necessários."""
        OUTPUT_DIR.mkdir(exist_ok=True)
        BACKUP_DIR.mkdir(exist_ok=True)
        self._log_file = LOG_FILE
    
    def execute_plan(
        self,
        plan: ReorganizationPlan,
        phases: Optional[List[str]] = None
    ) -> tuple[int, int]:
        """
        Executa plano de reorganização.
        Retorna (sucesso, falhas).
        """
        success_count = 0
        failure_count = 0
        
        phases_to_run = phases or list(plan.phases.keys())
        
        for phase_name in phases_to_run:
            if phase_name not in plan.phases:
                continue
            
            self._on_progress(f"\n[EXECUTANDO] {phase_name}")
            
            for operation in plan.phases[phase_name]:
                result = self.execute_operation(operation)
                
                if result:
                    success_count += 1
                else:
                    failure_count += 1
        
        self._on_progress(f"\n[CONCLUÍDO] {success_count} sucesso, {failure_count} falhas")
        return success_count, failure_count
    
    def execute_operation(self, operation: Operation) -> bool:
        """Executa uma única operação."""
        self._log(f"Executando: {operation.op_type.name} - {operation.source}")
        
        if self.dry_run:
            self._on_progress(f"  [DRY-RUN] {operation.source.name} -> {operation.target.name}")
            operation.status = OperationStatus.SIMULATED
            return True
        
        try:
            if self.use_powershell:
                success = self._execute_powershell(operation.command)
            else:
                success = self._execute_native(operation)
            
            if success:
                operation.status = OperationStatus.EXECUTED
                self._executed.append(operation)
                self._undo_stack.append(operation)
                self._on_progress(f"  [OK] {operation.source.name} -> {operation.target.name}")
                return True
            else:
                operation.status = OperationStatus.FAILED
                return False
        
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.error_msg = str(e)
            self._on_progress(f"  [ERRO] {operation.source.name}: {e}")
            return False
    
    def _execute_powershell(self, command: str) -> bool:
        """Executa comando via PowerShell."""
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                self._on_progress(f"  [PS-ERRO] {result.stderr.strip()}")
                return False
            
            return True
        
        except subprocess.TimeoutExpired:
            self._on_progress("  [TIMEOUT] Comando excedeu tempo limite")
            return False
        except Exception as e:
            self._on_progress(f"  [ERRO-PS] {e}")
            return False
    
    def _execute_native(self, operation: Operation) -> bool:
        """Executa operação usando Python nativo (mais portável)."""
        try:
            if operation.op_type == OperationType.RENAME:
                operation.source.rename(operation.target)
            
            elif operation.op_type == OperationType.MOVE:
                shutil.move(str(operation.source), str(operation.target))
            
            elif operation.op_type == OperationType.CREATE:
                operation.target.mkdir(parents=True, exist_ok=True)
            
            elif operation.op_type == OperationType.DELETE:
                if operation.source.is_dir():
                    shutil.rmtree(operation.source)
                else:
                    operation.source.unlink()
            
            return True
        
        except Exception as e:
            operation.error_msg = str(e)
            return False
    
    def undo_last(self) -> bool:
        """Desfaz última operação."""
        if not self._undo_stack:
            self._on_progress("[INFO] Nenhuma operação para desfazer")
            return False
        
        operation = self._undo_stack.pop()
        self._on_progress(f"[DESFAZENDO] {operation.id}")
        
        # Cria operação inversa
        if operation.op_type == OperationType.RENAME:
            # Inverter: target volta a ser source
            try:
                if self.use_powershell:
                    cmd = f"Rename-Item -LiteralPath '{operation.target}' -NewName '{operation.source.name}' -Force"
                    success = self._execute_powershell(cmd)
                else:
                    operation.target.rename(operation.source)
                    success = True
                
                if success:
                    operation.status = OperationStatus.REVERTED
                    self._on_progress(f"  [REVERTIDO] {operation.target.name} -> {operation.source.name}")
                    return True
            
            except Exception as e:
                self._on_progress(f"  [ERRO] Falha ao reverter: {e}")
                return False
        
        elif operation.op_type == OperationType.MOVE:
            try:
                shutil.move(str(operation.target), str(operation.source))
                operation.status = OperationStatus.REVERTED
                return True
            except Exception as e:
                self._on_progress(f"  [ERRO] Falha ao reverter: {e}")
                return False
        
        return False
    
    def undo_all(self) -> int:
        """Desfaz todas as operações (em ordem reversa)."""
        count = 0
        while self._undo_stack:
            if self.undo_last():
                count += 1
        return count
    
    def _log(self, message: str):
        """Registra operação no log."""
        if not self._log_file:
            return
        
        try:
            # Cria diretório se não existir
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().isoformat()
            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            # Ignora erros de log silenciosamente
            pass
    
    def get_execution_report(self) -> str:
        """Retorna relatório de execução."""
        executed = len([op for op in self._executed if op.status == OperationStatus.EXECUTED])
        failed = len([op for op in self._executed if op.status == OperationStatus.FAILED])
        reverted = len([op for op in self._executed if op.status == OperationStatus.REVERTED])
        
        return f"""
[RELATORIO DE EXECUCAO]
=======================
Executadas com sucesso: {executed}
Falhas:                 {failed}
Revertidas:             {reverted}
Na pilha de undo:       {len(self._undo_stack)}
"""
    
    def export_log(self, output_path: Optional[Path] = None) -> Path:
        """Exporta log de operações para JSON."""
        path = output_path or (OUTPUT_DIR / f"execution_log_{datetime.now():%Y%m%d_%H%M%S}.json")
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'operations': [op.to_dict() for op in self._executed],
        }
        
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return path
