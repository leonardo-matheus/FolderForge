"""
Analisador de estrutura de pastas - OTIMIZADO PARA PERFORMANCE.

Otimizações aplicadas:
- os.scandir() em vez de os.walk() (3-5x mais rápido)
- Generator-based para baixo uso de memória
- Regex compilado no config (evita recompilação)
- Processamento em uma única passada
- Cache de estatísticas de arquivo
- Detecção de pastas duplicadas/similares
- Leitura de conteúdo de arquivos para contexto
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional, Dict, Set, List, Tuple
from collections import defaultdict

from .models import FileItem, FolderAnalysis
from config import (
    PATTERN_CONFORMANT, PATTERN_EXTRACT_NUMBER,
    MAX_DEPTH, SYSTEM_FOLDERS, KEYWORD_PRIORITY_MAP, BANNED_CHARS,
    FILE_EXTENSION_MAP, FILE_KEYWORD_MAP, FOLDER_CONSOLIDATION_MAP
)


def normalize_folder_name(name: str) -> str:
    """
    Normaliza nome de pasta para comparação.
    Remove números, prefixos, acentos e padroniza.
    """
    # Remove padrão [NN] do início
    if '] ' in name:
        name = name.split('] ', 1)[1]
    
    # Remove números do início
    name = name.lstrip('0123456789[]- ')
    
    # Lowercase e remove acentos básicos
    name = name.lower().strip()
    
    # Normaliza variações comuns
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o',
        'ô': 'o', 'õ': 'o', 'ú': 'u', 'ç': 'c',
        '_': ' ', '-': ' ',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Remove múltiplos espaços
    name = ' '.join(name.split())
    
    return name


def read_file_preview(file_path: Path, max_bytes: int = 1024) -> str:
    """
    Lê preview do conteúdo de um arquivo para análise de contexto.
    Retorna string vazia se não conseguir ler.
    """
    try:
        # Extensões de texto que podemos ler
        text_extensions = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.xml', 
                          '.html', '.css', '.csv', '.log', '.ini', '.cfg',
                          '.yaml', '.yml', '.toml', '.sh', '.bat', '.ps1'}
        
        if file_path.suffix.lower() not in text_extensions:
            return ""
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(max_bytes)
            return content.lower()
    except Exception:
        return ""


class FolderAnalyzer:
    """
    Analisador de alta performance para estrutura de pastas.
    Numeracao sequencial por nivel (cada subpasta comeca em [01]).
    Detecta e mescla pastas duplicadas/similares.
    """
    __slots__ = ('root_path', 'max_depth', '_id_counter', '_used_numbers_by_parent', 
                 '_analysis', 'organize_files', '_duplicate_groups', '_canonical_folders')
    
    def __init__(self, root_path: str | Path, max_depth: int = MAX_DEPTH, organize_files: bool = True):
        self.root_path = Path(root_path).resolve()
        if not self.root_path.exists():
            raise FileNotFoundError(f"Caminho nao existe: {root_path}")
        if not self.root_path.is_dir():
            raise NotADirectoryError(f"Nao e um diretorio: {root_path}")
        
        self.max_depth = max_depth
        self.organize_files = organize_files
        self._id_counter = 0
        # Numeros usados POR PASTA PAI (para numeracao sequencial por nivel)
        self._used_numbers_by_parent: Dict[Path, Set[int]] = defaultdict(set)
        self._analysis: Optional[FolderAnalysis] = None
        # Grupos de pastas duplicadas (nome normalizado -> lista de pastas)
        self._duplicate_groups: Dict[str, List[FileItem]] = defaultdict(list)
        # Pasta canônica para cada nome normalizado (a que vai "ganhar")
        self._canonical_folders: Dict[str, FileItem] = {}
    
    def analyze(self) -> FolderAnalysis:
        """
        Executa analise completa da pasta.
        Retorna FolderAnalysis com todos os dados.
        """
        self._analysis = FolderAnalysis(root_path=self.root_path)
        self._id_counter = 0
        self._used_numbers_by_parent.clear()
        self._duplicate_groups.clear()
        self._canonical_folders.clear()
        
        # Primeira passada: coleta items e numeros usados
        items_list = list(self._scan_directory(self.root_path, depth=0))
        
        # Agrupa por profundidade e por pai para processamento eficiente
        folders_by_depth: Dict[int, list] = defaultdict(list)
        folders_by_parent: Dict[Path, list] = defaultdict(list)
        
        for item in items_list:
            self._analysis.items.append(item)
            self._analysis.total_items += 1
            self._analysis.total_size_bytes += item.size_bytes
            
            if item.item_type == 'folder':
                self._analysis.total_folders += 1
                folders_by_depth[item.depth].append(item)
                folders_by_parent[item.path.parent].append(item)
                
                # Agrupa pastas por nome normalizado para detectar duplicatas
                normalized = normalize_folder_name(item.name)
                self._duplicate_groups[normalized].append(item)
                
                if item.is_conformant:
                    self._analysis.conformant_count += 1
                    if item.current_number:
                        # Guarda numero usado POR PASTA PAI
                        self._used_numbers_by_parent[item.path.parent].add(item.current_number)
                else:
                    self._analysis.needs_rename_count += 1
            else:
                self._analysis.total_files += 1
            
            if item.depth > self._analysis.max_depth:
                self._analysis.max_depth = item.depth
        
        self._analysis.folders_by_depth = dict(folders_by_depth)
        
        # Detecta pastas duplicadas e escolhe a canônica
        self._resolve_duplicate_folders()
        
        # Segunda passada: sugere numeros SEQUENCIAIS por nivel
        # IMPORTANTE: Isso atualiza _used_numbers_by_parent com os números atribuídos
        self._assign_sequential_numbers(folders_by_parent)
        
        # Terceira passada: sugere destinos para arquivos
        # NOTA: Agora _used_numbers_by_parent já contém todos os números usados
        if self.organize_files:
            self._assign_file_destinations()
        
        return self._analysis
    
    def _resolve_duplicate_folders(self):
        """
        Resolve pastas duplicadas escolhendo qual manter.
        Critérios de prioridade:
        1. Pasta já conformante ([NN] Nome) tem prioridade
        2. Pasta com mais conteúdo (arquivos/subpastas)
        3. Pasta com nome mais completo
        """
        for normalized_name, folders in self._duplicate_groups.items():
            if len(folders) <= 1:
                # Não é duplicata
                if folders:
                    self._canonical_folders[normalized_name] = folders[0]
                continue
            
            # Filtra apenas pastas no mesmo nível (mesma pasta pai)
            folders_same_level = defaultdict(list)
            for f in folders:
                folders_same_level[f.path.parent].append(f)
            
            for parent, level_folders in folders_same_level.items():
                if len(level_folders) <= 1:
                    continue
                
                # Ordena por prioridade
                def folder_priority(f: FileItem) -> Tuple[int, int, int]:
                    # 1. Conformante primeiro (menor = melhor)
                    conformant_score = 0 if f.is_conformant else 1
                    # 2. Mais conteúdo (invertido: mais = melhor)
                    content_score = -f.children_count
                    # 3. Nome mais curto com número (provavelmente o "oficial")
                    name_score = len(f.name) if not f.is_conformant else -100
                    return (conformant_score, content_score, name_score)
                
                sorted_folders = sorted(level_folders, key=folder_priority)
                canonical = sorted_folders[0]
                
                # Marca as outras como "a serem mescladas" na canônica
                self._canonical_folders[normalized_name] = canonical
                
                for duplicate in sorted_folders[1:]:
                    # Marca duplicata para ser movida para dentro da canônica
                    duplicate.suggested_name = f"__MERGE_INTO__{canonical.path}"
    
    def _scan_directory(self, path: Path, depth: int) -> Generator[FileItem, None, None]:
        """
        Scanner otimizado usando os.scandir() - mais rápido que os.walk().
        Usa generator para baixo consumo de memória.
        """
        if depth > self.max_depth:
            return
        
        try:
            # os.scandir() é 3-5x mais rápido que os.listdir() + os.stat()
            with os.scandir(path) as entries:
                for entry in entries:
                    # Skip pastas do sistema
                    if entry.name.lower() in SYSTEM_FOLDERS:
                        continue
                    
                    try:
                        stat_info = entry.stat(follow_symlinks=False)
                        is_dir = entry.is_dir(follow_symlinks=False)
                        
                        self._id_counter += 1
                        
                        # Extrai número se já segue padrão
                        current_number = None
                        is_conformant = False
                        
                        if is_dir:
                            match = PATTERN_CONFORMANT.match(entry.name)
                            if match:
                                is_conformant = True
                                num_match = PATTERN_EXTRACT_NUMBER.match(entry.name)
                                if num_match:
                                    current_number = int(num_match.group(1))
                        
                        item = FileItem(
                            id=f"item_{self._id_counter:06d}",
                            name=entry.name,
                            path=Path(entry.path),
                            item_type='folder' if is_dir else 'file',
                            size_bytes=0 if is_dir else stat_info.st_size,
                            modified_ts=stat_info.st_mtime,
                            depth=depth,
                            is_conformant=is_conformant,
                            current_number=current_number,
                        )
                        
                        yield item
                        
                        # Recursão para subpastas
                        if is_dir:
                            yield from self._scan_directory(Path(entry.path), depth + 1)
                    
                    except (PermissionError, OSError):
                        # Ignora arquivos sem permissão
                        continue
        
        except PermissionError:
            pass  # Ignora pastas sem permissão
    
    def _assign_sequential_numbers(self, folders_by_parent: Dict[Path, list]):
        """
        Atribui numeros SEQUENCIAIS por nivel.
        Cada pasta pai tem seus filhos numerados a partir de [01].
        Ignora pastas marcadas para merge.
        """
        if not self._analysis:
            return
        
        # Processa cada pasta pai
        for parent_path, folders in folders_by_parent.items():
            # Referência direta ao set de números usados (NÃO fazer cópia!)
            # Isso garante que _assign_file_destinations veja os números atribuídos aqui
            used_in_parent = self._used_numbers_by_parent[parent_path]
            
            # Filtra pastas que precisam numerar (não conformes E não marcadas para merge)
            folders_to_number = [
                f for f in folders 
                if not f.is_conformant and not (f.suggested_name and f.suggested_name.startswith('__MERGE_INTO__'))
            ]
            folders_to_number.sort(key=lambda f: (self._get_priority_for_name(f.name), f.name.lower()))
            
            # Atribui numeros sequenciais
            next_num = 1
            for folder in folders_to_number:
                # Encontra proximo numero disponivel
                while next_num in used_in_parent:
                    next_num += 1
                
                if next_num > 99:
                    next_num = 1
                
                # Adiciona ao set ORIGINAL para que _assign_file_destinations veja
                used_in_parent.add(next_num)
                folder.suggested_number = next_num
                folder.suggested_name = self._format_new_name(folder.name, next_num)
                next_num += 1
    
    def _assign_file_destinations(self):
        """
        Sugere destinos para arquivos soltos baseado em:
        1. Palavras-chave no nome do arquivo (prioridade máxima)
        2. Conteúdo do arquivo (leitura inteligente)
        3. Extensão do arquivo (fallback)
        
        Cria pastas automaticamente se necessário.
        """
        if not self._analysis:
            return
        
        # Mapeia pastas existentes por nome normalizado (para encontrar destinos)
        folders_by_name: Dict[str, FileItem] = {}
        folders_by_normalized: Dict[str, FileItem] = {}
        
        for item in self._analysis.items:
            if item.item_type == 'folder':
                # Pula pastas marcadas para merge
                if item.suggested_name and item.suggested_name.startswith('__MERGE_INTO__'):
                    continue
                
                # Extrai nome sem numero
                name_clean = item.name.lower()
                if '] ' in name_clean:
                    name_clean = name_clean.split('] ', 1)[1]
                folders_by_name[name_clean] = item
                
                # Também mapeia por nome normalizado
                normalized = normalize_folder_name(item.name)
                folders_by_normalized[normalized] = item
        
        # Pastas que precisam ser criadas
        folders_to_create: Dict[str, Path] = {}
        
        # Para cada arquivo, sugere destino
        for item in self._analysis.items:
            if item.item_type != 'file':
                continue
            
            # Ignora executáveis do próprio programa
            if item.name.lower() in ('folderforge.exe', 'folderforge_reorganizar.ps1'):
                continue
            
            file_name_lower = item.name.lower()
            dest_folder = None
            dest_folder_name = None
            
            # 1. Primeiro tenta por PALAVRAS-CHAVE no nome do arquivo
            for keywords, target_folder in FILE_KEYWORD_MAP:
                for keyword in keywords:
                    if keyword in file_name_lower:
                        # Procura pasta existente
                        dest_folder = self._find_matching_folder(target_folder, folders_by_name, folders_by_normalized)
                        if dest_folder:
                            break
                        else:
                            # Pasta não existe - marcar para criar
                            dest_folder_name = target_folder
                            break
                if dest_folder or dest_folder_name:
                    break
            
            # 2. Se não encontrou, tenta ler CONTEÚDO do arquivo
            if not dest_folder and not dest_folder_name:
                content = read_file_preview(item.path)
                if content:
                    for keywords, target_folder in FILE_KEYWORD_MAP:
                        for keyword in keywords:
                            if keyword in content:
                                dest_folder = self._find_matching_folder(target_folder, folders_by_name, folders_by_normalized)
                                if dest_folder:
                                    break
                                else:
                                    dest_folder_name = target_folder
                                    break
                        if dest_folder or dest_folder_name:
                            break
            
            # 3. Se não encontrou, tenta por EXTENSÃO
            if not dest_folder and not dest_folder_name:
                ext = item.path.suffix.lower()
                if ext in FILE_EXTENSION_MAP:
                    category = FILE_EXTENSION_MAP[ext]
                    dest_folder = self._find_matching_folder(category, folders_by_name, folders_by_normalized)
                    if not dest_folder:
                        dest_folder_name = category
            
            # Define destino final
            if dest_folder:
                # Pasta existe - mover para lá
                item.suggested_name = str(dest_folder.path / item.name)
            elif dest_folder_name:
                # Pasta não existe - registrar para criação
                if dest_folder_name not in folders_to_create:
                    # Encontra próximo número disponível na raiz
                    used = self._used_numbers_by_parent[self.root_path]
                    next_num = 1
                    while next_num in used:
                        next_num += 1
                    used.add(next_num)
                    
                    new_folder_name = f"[{next_num:02d}] {dest_folder_name}"
                    new_folder_path = self.root_path / new_folder_name
                    folders_to_create[dest_folder_name] = new_folder_path
                
                item.suggested_name = str(folders_to_create[dest_folder_name] / item.name)
        
        # Registra pastas a serem criadas na análise
        if folders_to_create:
            if not hasattr(self._analysis, 'folders_to_create'):
                self._analysis.folders_to_create = []
            self._analysis.folders_to_create = list(folders_to_create.values())
    
    def _find_matching_folder(self, target_name: str, folders_by_name: Dict, folders_by_normalized: Dict) -> Optional[FileItem]:
        """Encontra pasta que melhor corresponde ao nome alvo."""
        target_lower = target_name.lower()
        target_normalized = normalize_folder_name(target_name)
        
        # Busca exata
        if target_lower in folders_by_name:
            return folders_by_name[target_lower]
        
        # Busca por nome normalizado
        if target_normalized in folders_by_normalized:
            return folders_by_normalized[target_normalized]
        
        # Busca parcial
        for folder_name, folder in folders_by_name.items():
            if target_lower in folder_name or folder_name in target_lower:
                return folder
        
        return None
    
    def _get_priority_for_name(self, name: str) -> int:
        """Determina prioridade baseada em palavras-chave no nome."""
        name_lower = name.lower()
        
        # Remove caracteres especiais para matching
        clean_name = ''.join(c for c in name_lower if c.isalnum() or c.isspace())
        words = clean_name.split()
        
        # Procura keywords no nome
        for word in words:
            if word in KEYWORD_PRIORITY_MAP:
                return KEYWORD_PRIORITY_MAP[word]
        
        # Default: retorna 50 (sera ajustado sequencialmente)
        return 50
    
    def _format_new_name(self, current_name: str, number: int) -> str:
        """Formata novo nome seguindo padrão [NN] Nome."""
        # Remove caracteres proibidos
        clean_name = ''.join(
            c if c not in BANNED_CHARS else '_'
            for c in current_name
        )
        # Remove números existentes no início se houver
        clean_name = clean_name.lstrip('0123456789[]- ')
        
        return f"[{number:02d}] {clean_name}"
    
    def get_report(self) -> str:
        """Gera relatório textual da análise."""
        if not self._analysis:
            return "[ERRO] Execute analyze() primeiro"
        
        a = self._analysis
        root_str = str(a.root_path)[:50]
        
        return f"""
+==============================================================+
|          RELATORIO DE ANALISE - ORGANIZACAO DE PASTAS        |
+==============================================================+
|  Caminho: {root_str:<50} |
|  Data:    {a.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<50} |
+--------------------------------------------------------------+
|  ESTATISTICAS                                                |
|  Total de items:     {a.total_items:<8}                              |
|  Pastas:             {a.total_folders:<8}                              |
|  Arquivos:           {a.total_files:<8}                              |
|  Tamanho total:      {a.total_size_mb:<8.2f} MB                        |
|  Profundidade max:   {a.max_depth:<8}                              |
+--------------------------------------------------------------+
|  CONFORMIDADE                                                |
|  [OK] Conformes:       {a.conformant_count:<8}                             |
|  [!!] Precisam ajuste: {a.needs_rename_count:<8}                             |
|  Score:                {a.organization_score:<8.1f}/100                      |
+==============================================================+
"""
    
    def get_non_conformant_folders(self) -> list[FileItem]:
        """Retorna lista de pastas que precisam renomeação."""
        if not self._analysis:
            return []
        return [
            item for item in self._analysis.items
            if item.item_type == 'folder' and not item.is_conformant
        ]
