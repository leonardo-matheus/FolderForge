"""
Funções utilitárias otimizadas.
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Union

from config import BANNED_CHARS


def format_size(size_bytes: int) -> str:
    """Formata tamanho em bytes para formato legivel."""
    size: float = float(size_bytes)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_duration(seconds: float) -> str:
    """Formata duração em segundos para formato legível."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_path_name(name: str) -> str:
    """Remove caracteres inválidos de nome de arquivo/pasta."""
    # Remove caracteres proibidos
    clean = ''.join(c if c not in BANNED_CHARS else '_' for c in name)
    # Remove espaços extras
    clean = ' '.join(clean.split())
    # Limita tamanho
    return clean[:200] if len(clean) > 200 else clean


def get_terminal_width() -> int:
    """Retorna largura do terminal."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def normalize_path(path: Union[str, Path]) -> Path:
    """Normaliza caminho para formato consistente."""
    p = Path(path).resolve()
    return p


def is_hidden(path: Path) -> bool:
    """Verifica se arquivo/pasta é oculto."""
    try:
        # Windows: verifica atributo hidden
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        return attrs != -1 and bool(attrs & 2)
    except:
        # Fallback: verifica se começa com ponto
        return path.name.startswith('.')


def count_items(path: Path) -> tuple[int, int]:
    """
    Conta arquivos e pastas em um diretório (não recursivo).
    Retorna (arquivos, pastas).
    """
    files = folders = 0
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    files += 1
                elif entry.is_dir():
                    folders += 1
    except PermissionError:
        pass
    return files, folders


def validate_windows_path(path: str) -> bool:
    """Valida se caminho é válido no Windows."""
    # Verifica comprimento
    if len(path) > 260:
        return False
    
    # Verifica caracteres proibidos
    if any(c in path for c in '<>"|?*'):
        return False
    
    # Verifica nomes reservados
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3',
                'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    
    name = Path(path).stem.upper()
    if name in reserved:
        return False
    
    return True
