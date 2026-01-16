"""
Planejador de reorganização - Gera planos de execução otimizados.

Estratégias:
- Processa bottom-up para evitar conflitos de caminho
- Agrupa operações por tipo para execução eficiente
- Valida cada operação antes de adicionar ao plano
- Detecta e mescla pastas duplicadas
- Cria pastas automaticamente quando necessário
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict, Set
from collections import defaultdict

from .models import (
    FileItem, FolderAnalysis, Operation, OperationType,
    OperationStatus, ReorganizationPlan
)
from config import MAX_PATH_LENGTH, BANNED_CHARS, FOLDER_CONSOLIDATION_MAP


class ReorganizationPlanner:
    """
    Gera planos de reorganizacao otimizados.
    """
    __slots__ = ('analysis', '_plan', '_op_counter', '_path_remap', '_folders_to_delete')
    
    def __init__(self, analysis: FolderAnalysis):
        self.analysis = analysis
        self._plan: Optional[ReorganizationPlan] = None
        self._op_counter = 0
    
    def generate_plan(self) -> ReorganizationPlan:
        """
        Gera plano completo de reorganizacao.
        Ordem: 
        1) Cria pastas necessárias
        2) Mescla pastas duplicadas
        3) Consolida pastas relacionadas
        4) Renomeia pastas (bottom-up)
        5) Move arquivos
        """
        self._plan = ReorganizationPlan(analysis=self.analysis)
        self._op_counter = 0
        
        # Mapa de caminhos antigos -> novos (para ajustar destinos de arquivos)
        self._path_remap: Dict[Path, Path] = {}
        
        # Pastas a serem deletadas após merge
        self._folders_to_delete: Set[Path] = set()
        
        # FASE -1: Cria pastas necessárias (detectadas na análise)
        if hasattr(self.analysis, 'folders_to_create') and self.analysis.folders_to_create:
            for folder_path in self.analysis.folders_to_create:
                operation = self._create_folder_operation(folder_path)
                if operation:
                    self._plan.add_operation("Fase 0 - Criar pastas", operation)
        
        # Mapeia pastas por nome para consolidacao
        folders_by_name: Dict[str, FileItem] = {}
        for item in self.analysis.items:
            if item.item_type == 'folder':
                name_clean = item.name.lower()
                if '] ' in name_clean:
                    name_clean = name_clean.split('] ', 1)[1]
                folders_by_name[name_clean] = item
        
        # FASE 0: Mescla pastas duplicadas (marcadas com __MERGE_INTO__)
        for item in self.analysis.items:
            if item.item_type == 'folder' and item.suggested_name and item.suggested_name.startswith('__MERGE_INTO__'):
                target_path_str = item.suggested_name.replace('__MERGE_INTO__', '')
                target_path = Path(target_path_str)
                
                # Move conteúdo da pasta duplicada para a canônica
                operation = self._create_merge_operation(item, target_path)
                if operation:
                    self._plan.add_operation("Fase 0.5 - Mesclar duplicatas", operation)
                    self._folders_to_delete.add(item.path)
        
        # FASE 1: Consolida pastas relacionadas (config)
        folders_to_consolidate: List[tuple] = []  # (source_folder, target_folder)
        for parent_name, children_names in FOLDER_CONSOLIDATION_MAP.items():
            parent_folder = folders_by_name.get(parent_name)
            if parent_folder:
                for child_name in children_names:
                    child_folder = folders_by_name.get(child_name)
                    if child_folder and child_folder.path.parent == parent_folder.path.parent:
                        # Mesma pasta pai - pode consolidar
                        # Não consolida se já está marcada para delete
                        if child_folder.path not in self._folders_to_delete:
                            folders_to_consolidate.append((child_folder, parent_folder))
        
        # Cria operacoes de consolidacao (mover pasta para dentro de outra)
        for source_folder, target_folder in folders_to_consolidate:
            operation = self._create_consolidation_operation(source_folder, target_folder)
            if operation:
                self._plan.add_operation("Fase 1 - Consolidar pastas", operation)
                self._path_remap[source_folder.path] = operation.target
        
        # FASE 2: Agrupa pastas nao conformes por profundidade
        folders_by_depth: Dict[int, List[FileItem]] = defaultdict(list)
        files_to_move: List[FileItem] = []
        
        # Pastas ja consolidadas ou marcadas para delete não devem ser renomeadas
        skip_paths = {src.path for src, _ in folders_to_consolidate} | self._folders_to_delete
        
        for item in self.analysis.items:
            if item.item_type == 'folder' and not item.is_conformant:
                # Pula pastas marcadas para merge ou consolidação
                if item.path not in skip_paths and not (item.suggested_name and item.suggested_name.startswith('__MERGE_INTO__')):
                    folders_by_depth[item.depth].append(item)
            elif item.item_type == 'file' and item.suggested_name:
                files_to_move.append(item)
        
        # Processa bottom-up (maior profundidade primeiro)
        for depth in sorted(folders_by_depth.keys(), reverse=True):
            for folder in folders_by_depth[depth]:
                operation = self._create_rename_operation(folder)
                if operation:
                    phase = f"Fase {depth + 2} - Renomear nivel {depth}"
                    self._plan.add_operation(phase, operation)
                    self._path_remap[folder.path] = operation.target
        
        # FASE FINAL: Move arquivos para pastas apropriadas
        for file_item in files_to_move:
            operation = self._create_move_operation(file_item)
            if operation:
                self._plan.add_operation("Fase Final - Organizar arquivos", operation)
        
        # FASE LIMPEZA: Remove pastas vazias (após merge)
        for folder_path in self._folders_to_delete:
            operation = self._create_delete_operation(folder_path)
            if operation:
                self._plan.add_operation("Fase Limpeza - Remover vazias", operation)
        
        return self._plan
    
    def _create_delete_operation(self, folder_path: Path) -> Optional[Operation]:
        """Cria operação de deletar pasta vazia."""
        self._op_counter += 1
        
        folder_str = str(folder_path).replace("'", "''")
        
        # Remove apenas se estiver vazia
        ps_command = f"if ((Get-ChildItem -LiteralPath '{folder_str}' -Force | Measure-Object).Count -eq 0) {{ Remove-Item -LiteralPath '{folder_str}' -Force }}"
        
        return Operation(
            id=f"op_{self._op_counter:06d}",
            op_type=OperationType.DELETE,
            source=folder_path,
            target=folder_path,
            command=ps_command,
        )
    
    def _create_folder_operation(self, folder_path: Path) -> Optional[Operation]:
        """Cria operação de criar nova pasta."""
        if folder_path.exists():
            return None
        
        self._op_counter += 1
        
        ps_command = self._generate_powershell_command(
            OperationType.CREATE, folder_path, folder_path
        )
        
        return Operation(
            id=f"op_{self._op_counter:06d}",
            op_type=OperationType.CREATE,
            source=folder_path,
            target=folder_path,
            command=ps_command,
        )
    
    def _create_merge_operation(self, source_folder: FileItem, target_path: Path) -> Optional[Operation]:
        """Cria operação de mesclar pasta duplicada na canônica."""
        source_path = source_folder.path
        
        if not source_path.exists():
            return None
        if not target_path.exists():
            return None
        
        self._op_counter += 1
        
        # Move todo conteúdo da pasta source para target
        # Usa comando PowerShell que move conteúdo
        source_str = str(source_path).replace("'", "''")
        target_str = str(target_path).replace("'", "''")
        
        ps_command = f"Get-ChildItem -LiteralPath '{source_str}' | Move-Item -Destination '{target_str}' -Force"
        
        return Operation(
            id=f"op_{self._op_counter:06d}",
            op_type=OperationType.MOVE,
            source=source_path,
            target=target_path,
            command=ps_command,
        )
    
    def _create_consolidation_operation(self, source: FileItem, target: FileItem) -> Optional[Operation]:
        """Cria operacao de mover pasta para dentro de outra (consolidacao)."""
        source_path = source.path
        target_path = target.path / source.name
        
        if not source_path.exists():
            return None
        if target_path.exists():
            return None
        
        self._op_counter += 1
        
        ps_command = self._generate_powershell_command(
            OperationType.MOVE, source_path, target_path
        )
        
        return Operation(
            id=f"op_{self._op_counter:06d}",
            op_type=OperationType.MOVE,
            source=source_path,
            target=target_path,
            command=ps_command,
        )
    
    def _get_updated_path(self, original_path: Path) -> Path:
        """Retorna o caminho atualizado apos TODAS as renomeacoes."""
        result_str = str(original_path)
        
        # Ordena por tamanho do caminho (mais longo primeiro) para evitar substituicoes parciais
        sorted_remap = sorted(self._path_remap.items(), key=lambda x: len(str(x[0])), reverse=True)
        
        # Aplica todas as substituicoes
        for old_path, new_path in sorted_remap:
            old_str = str(old_path)
            new_str = str(new_path)
            
            # Substitui se o caminho contem este path
            if old_str in result_str:
                result_str = result_str.replace(old_str, new_str)
        
        return Path(result_str)
    
    def _create_move_operation(self, file_item: FileItem) -> Optional[Operation]:
        """Cria operacao de mover arquivo."""
        if not file_item.suggested_name:
            return None
        
        original_source = file_item.path
        original_target = Path(file_item.suggested_name)
        
        # Atualiza AMBOS os caminhos considerando pastas renomeadas
        # O source pode ter mudado se a pasta pai foi renomeada
        source_path = self._get_updated_path(original_source)
        target_path = self._get_updated_path(original_target)
        
        # Valida - o source atualizado deve existir NO MOMENTO DA EXECUCAO (pastas ja renomeadas)
        # Mas no momento do planejamento, validamos apenas se o source ORIGINAL existe
        if not original_source.exists():
            return None
        # Nao valida se target existe porque pasta pode nao existir ainda
        
        self._op_counter += 1
        
        ps_command = self._generate_powershell_command(
            OperationType.MOVE, source_path, target_path
        )
        
        return Operation(
            id=f"op_{self._op_counter:06d}",
            op_type=OperationType.MOVE,
            source=source_path,
            target=target_path,
            command=ps_command,
        )
    
    def _create_rename_operation(self, folder: FileItem) -> Optional[Operation]:
        """Cria operação de renomeação validada."""
        if not folder.suggested_name:
            return None
        
        source_path = folder.path
        target_path = folder.path.parent / folder.suggested_name
        
        # Validações
        if not self._validate_operation(source_path, target_path):
            return None
        
        self._op_counter += 1
        
        # Gera comando PowerShell
        ps_command = self._generate_powershell_command(
            OperationType.RENAME, source_path, target_path
        )
        
        return Operation(
            id=f"op_{self._op_counter:06d}",
            op_type=OperationType.RENAME,
            source=source_path,
            target=target_path,
            command=ps_command,
        )
    
    def _validate_operation(self, source: Path, target: Path) -> bool:
        """Valida se operação é segura para executar."""
        # Verifica se source existe
        if not source.exists():
            return False
        
        # Verifica se target já existe
        if target.exists():
            return False
        
        # Verifica comprimento do caminho (Windows limit)
        if len(str(target)) > MAX_PATH_LENGTH:
            return False
        
        # Verifica caracteres proibidos no nome
        if any(c in target.name for c in BANNED_CHARS):
            return False
        
        return True
    
    def _generate_powershell_command(
        self,
        op_type: OperationType,
        source: Path,
        target: Path
    ) -> str:
        """Gera comando PowerShell para a operação."""
        source_str = str(source).replace("'", "''")
        target_str = str(target).replace("'", "''")
        target_name = target.name.replace("'", "''")
        
        if op_type == OperationType.RENAME:
            return f"Rename-Item -LiteralPath '{source_str}' -NewName '{target_name}' -Force"
        
        elif op_type == OperationType.MOVE:
            return f"Move-Item -LiteralPath '{source_str}' -Destination '{target_str}' -Force"
        
        elif op_type == OperationType.CREATE:
            return f"New-Item -Path '{target_str}' -ItemType Directory -Force"
        
        elif op_type == OperationType.DELETE:
            return f"Remove-Item -LiteralPath '{source_str}' -Recurse -Force"
        
        return ""
    
    def get_plan_preview(self, max_items: int = 20) -> str:
        """Retorna preview do plano em formato texto."""
        if not self._plan:
            return "[ERRO] Execute generate_plan() primeiro"
        
        lines = [
            "",
            "+==============================================================+",
            "|              PLANO DE REORGANIZACAO                          |",
            "+==============================================================+",
            f"|  Total de operacoes: {self._plan.total_operations:<40}|",
            f"|  Fases: {len(self._plan.phases):<51}|",
            "+--------------------------------------------------------------+",
        ]
        
        shown = 0
        for phase_name, operations in self._plan.phases.items():
            lines.append(f"|  {phase_name:<59}|")
            lines.append("|  " + "-" * 58 + "|")
            
            for op in operations:
                if shown >= max_items:
                    remaining = self._plan.total_operations - shown
                    lines.append(f"|    ... e mais {remaining} operacoes{' ' * 37}|")
                    break
                
                source_name = op.source.name[:25]
                target_name = op.target.name[:25]
                lines.append(f"|    {source_name:<25} -> {target_name:<25}|")
                shown += 1
            
            if shown >= max_items:
                break
            
            lines.append("|" + " " * 62 + "|")
        
        lines.append("+==============================================================+")
        
        return "\n".join(lines)
    
    def export_plan_to_script(self, output_path: Path) -> bool:
        """Exporta plano como script PowerShell."""
        if not self._plan:
            return False
        
        lines = [
            "# Folder Organizer - Script de Reorganização",
            f"# Gerado em: {self._plan.created_at.isoformat()}",
            f"# Total de operações: {self._plan.total_operations}",
            "",
            "# ATENÇÃO: Revise cada operação antes de executar!",
            "",
            "$ErrorActionPreference = 'Stop'",
            "",
        ]
        
        for phase_name, operations in self._plan.phases.items():
            lines.append(f"# === {phase_name} ===")
            for op in operations:
                lines.append(f"# {op.source.name} -> {op.target.name}")
                lines.append(op.command)
                lines.append("")
        
        lines.append("Write-Host 'Reorganização concluída!' -ForegroundColor Green")
        
        output_path.write_text("\n".join(lines), encoding='utf-8')
        return True
