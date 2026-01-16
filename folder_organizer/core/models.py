"""
Modelos de dados otimizados usando dataclasses e __slots__ para performance.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class OperationType(Enum):
    """Tipos de operação suportados."""
    RENAME = auto()
    MOVE = auto()
    CREATE = auto()
    DELETE = auto()


class OperationStatus(Enum):
    """Status de uma operação."""
    PENDING = auto()
    SIMULATED = auto()
    EXECUTED = auto()
    FAILED = auto()
    REVERTED = auto()


@dataclass(slots=True)
class FileItem:
    """
    Representa um arquivo ou pasta.
    Usa __slots__ para reduzir uso de memória em ~40%.
    """
    id: str
    name: str
    path: Path
    item_type: str  # 'file' ou 'folder'
    size_bytes: int
    modified_ts: float
    depth: int
    is_conformant: bool = False
    current_number: Optional[int] = None
    suggested_name: Optional[str] = None
    suggested_number: Optional[int] = None
    children_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para JSON)."""
        return {
            'id': self.id,
            'name': self.name,
            'path': str(self.path),
            'type': self.item_type,
            'size_mb': round(self.size_bytes / 1_048_576, 2),
            'modified': datetime.fromtimestamp(self.modified_ts).isoformat(),
            'depth': self.depth,
            'is_conformant': self.is_conformant,
            'current_number': self.current_number,
            'suggested_name': self.suggested_name,
            'suggested_number': self.suggested_number,
            'children_count': self.children_count,
        }


@dataclass(slots=True)
class Operation:
    """Operação atômica a ser executada."""
    id: str
    op_type: OperationType
    source: Path
    target: Path
    command: str = ''
    status: OperationStatus = OperationStatus.PENDING
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    error_msg: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.op_type.name,
            'source': str(self.source),
            'target': str(self.target),
            'command': self.command,
            'status': self.status.name,
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'error': self.error_msg,
        }


@dataclass
class FolderAnalysis:
    """Resultado da análise de uma pasta."""
    root_path: Path
    timestamp: datetime = field(default_factory=datetime.now)
    total_items: int = 0
    total_folders: int = 0
    total_files: int = 0
    total_size_bytes: int = 0
    max_depth: int = 0
    conformant_count: int = 0
    needs_rename_count: int = 0
    items: List[FileItem] = field(default_factory=list)
    folders_by_depth: Dict[int, List[FileItem]] = field(default_factory=dict)
    folders_to_create: List[Path] = field(default_factory=list)  # Pastas novas a criar
    
    @property
    def total_size_mb(self) -> float:
        return round(self.total_size_bytes / 1_048_576, 2)
    
    @property
    def organization_score(self) -> float:
        """Score de 0-100 baseado em conformidade."""
        if self.total_folders == 0:
            return 0.0
        score = (self.conformant_count / self.total_folders) * 100
        # Penalidade por profundidade excessiva
        if self.max_depth > 4:
            score *= 0.9
        return round(score, 1)
    
    def to_json(self, indent: int = 2) -> str:
        """Serializa para JSON."""
        return json.dumps({
            'analysis_timestamp': self.timestamp.isoformat(),
            'root_path': str(self.root_path),
            'scan_results': {
                'total_items': self.total_items,
                'total_folders': self.total_folders,
                'total_files': self.total_files,
                'total_size_mb': self.total_size_mb,
                'max_depth': self.max_depth,
            },
            'organization': {
                'conformant_folders': self.conformant_count,
                'needs_rename': self.needs_rename_count,
                'score': self.organization_score,
            },
            'folders': [f.to_dict() for f in self.items if f.item_type == 'folder'],
        }, indent=indent, ensure_ascii=False)


@dataclass
class ReorganizationPlan:
    """Plano de reorganização com operações em fases."""
    analysis: FolderAnalysis
    created_at: datetime = field(default_factory=datetime.now)
    phases: Dict[str, List[Operation]] = field(default_factory=dict)
    
    @property
    def total_operations(self) -> int:
        return sum(len(ops) for ops in self.phases.values())
    
    def add_operation(self, phase: str, operation: Operation):
        if phase not in self.phases:
            self.phases[phase] = []
        self.phases[phase].append(operation)
    
    def get_summary(self) -> str:
        """Retorna resumo do plano."""
        lines = ['PLANO DE REORGANIZAÇÃO', '=' * 50]
        for phase_name, ops in self.phases.items():
            lines.append(f'\n{phase_name}: {len(ops)} operações')
            for op in ops[:5]:  # Mostra primeiras 5
                lines.append(f'  • {op.op_type.name}: {op.source.name} → {op.target.name}')
            if len(ops) > 5:
                lines.append(f'  ... e mais {len(ops) - 5} operações')
        return '\n'.join(lines)
