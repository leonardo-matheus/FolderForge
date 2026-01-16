"""
Configurações globais do Agente de Organização de Pastas.
Otimizado para performance e flexibilidade.
"""
from pathlib import Path
import re

# ══════════════════════════════════════════════════════════════════════════════
# PADRÃO DE NOMENCLATURA
# ══════════════════════════════════════════════════════════════════════════════

# Regex compilado (performance: compila uma vez, usa sempre)
PATTERN_CONFORMANT = re.compile(r'^\[(\d{2})\]\s+.+$')
PATTERN_EXTRACT_NUMBER = re.compile(r'^\[(\d{2})\]')

# Caracteres proibidos em nomes de pasta (Windows)
BANNED_CHARS = frozenset('<>:"|?*')

# ══════════════════════════════════════════════════════════════════════════════
# HIERARQUIA DE PRIORIDADES
# ══════════════════════════════════════════════════════════════════════════════

PRIORITY_RANGES = {
    'active': (1, 30),      # [01]-[30] Pastas ativas/frequentes
    'support': (31, 70),    # [31]-[70] Pastas suporte/referência
    'temp': (71, 98),       # [71]-[98] Pastas temporárias
    'archived': (99, 99),   # [99] Arquivados
}

# Mapeamento de palavras-chave para prioridades automáticas
KEYWORD_PRIORITY_MAP = {
    # Prioridade alta (01-10)
    'desenvolvimento': 1, 'dev': 1, 'trabalho': 2, 'projetos': 3,
    'atual': 4, 'urgente': 5, 'importante': 6,
    
    # Prioridade média (11-30)
    'documentos': 11, 'docs': 11, 'estudos': 12, 'estudo': 12,
    'pessoal': 15, 'compartilhar': 20,
    
    # Suporte (31-50)
    'softwares': 31, 'software': 31, 'ferramentas': 32, 'tools': 32,
    'recursos': 35, 'referencias': 40, 'templates': 45,
    
    # Backup/Storage (51-70)
    'backups': 51, 'backup': 51, 'storage': 55, 'midia': 60,
    
    # Temporário (71-98)
    'temp': 71, 'temporario': 71, 'downloads': 75, 'inbox': 80,
    'deletar': 90, 'lixo': 95,
    
    # Arquivado (99)
    'arquivado': 99, 'arquivados': 99, 'arquivo': 99, 'old': 99,
}

# ══════════════════════════════════════════════════════════════════════════════
# LIMITES E RESTRIÇÕES
# ══════════════════════════════════════════════════════════════════════════════

MAX_DEPTH = 4                    # Profundidade máxima de análise
MAX_PATH_LENGTH = 260            # Limite Windows (sem LongPath)
MAX_ITEMS_PER_BATCH = 1000       # Limite de operações por batch
SCAN_TIMEOUT_SECONDS = 300       # Timeout para scan (5 min)

# Pastas do sistema para ignorar
SYSTEM_FOLDERS = frozenset({
    '$recycle.bin', 'system volume information', 'windows',
    'program files', 'program files (x86)', 'programdata',
    'appdata', 'node_modules', '.git', '__pycache__', '.venv',
    'venv', '.idea', '.vscode', 'dist', 'build', '.cache'
})

# Extensoes de arquivo para ignorar no calculo de tamanho
IGNORE_EXTENSIONS = frozenset({'.tmp', '.log', '.bak'})

# Mapeamento de extensoes para categorias de pasta
FILE_EXTENSION_MAP = {
    # Programacao
    '.py': 'scripts python',
    '.js': 'scripts javascript', 
    '.ts': 'scripts typescript',
    '.java': 'scripts java',
    '.cs': 'scripts csharp',
    '.cpp': 'scripts cpp',
    '.c': 'scripts c',
    '.rs': 'scripts rust',
    '.go': 'scripts go',
    '.rb': 'scripts ruby',
    '.php': 'scripts php',
    '.sh': 'scripts shell',
    '.ps1': 'scripts powershell',
    '.bat': 'scripts batch',
    '.sql': 'scripts sql',
    
    # Documentos
    '.pdf': 'documentos',
    '.doc': 'documentos',
    '.docx': 'documentos',
    '.xls': 'planilhas',
    '.xlsx': 'planilhas',
    '.ppt': 'apresentacoes',
    '.pptx': 'apresentacoes',
    '.md': 'documentos',
    '.csv': 'dados',
    '.json': 'dados',
    '.xml': 'dados',
    
    # Imagens
    '.jpg': 'imagens',
    '.jpeg': 'imagens',
    '.png': 'imagens',
    '.gif': 'imagens',
    '.svg': 'imagens',
    '.ico': 'imagens',
    '.webp': 'imagens',
    
    # Audio/Video
    '.mp3': 'audio',
    '.wav': 'audio',
    '.mp4': 'videos',
    '.avi': 'videos',
    '.mkv': 'videos',
    '.mov': 'videos',
    
    # Compactados
    '.zip': 'compactados',
    '.rar': 'compactados',
    '.7z': 'compactados',
    '.tar': 'compactados',
    '.gz': 'compactados',
    
    # Executaveis
    '.exe': 'executaveis',
    '.msi': 'instaladores',
    '.dmg': 'instaladores',
}

# Mapeamento de PALAVRAS-CHAVE no nome do arquivo para pasta destino
# Prioridade: primeiro match ganha
FILE_KEYWORD_MAP = [
    # Financeiro/Impostos
    (['imposto', 'renda', 'irpf', 'receita'], 'imposto de renda'),
    (['nota fiscal', 'nf', 'nfe', 'danfe'], 'notas fiscais'),
    (['boleto', 'fatura', 'conta'], 'financeiro'),
    
    # Educacao
    (['diploma', 'certificado', 'certificacao'], 'escolaridade'),
    (['tcc', 'monografia', 'dissertacao', 'tese'], 'escolaridade'),
    (['historico', 'boletim', 'notas'], 'escolaridade'),
    
    # Trabalho
    (['curriculo', 'cv', 'resume'], 'trabalho'),
    (['contrato', 'acordo'], 'contratos'),
    (['projeto', 'proposta'], 'projetos'),
    
    # Pessoal
    (['rg', 'cpf', 'cnh', 'identidade', 'documento'], 'documentos pessoais'),
    (['foto', 'imagem', 'screenshot', 'print'], 'imagens'),
]

# Mapeamento de pastas que devem ser CONSOLIDADAS (subpastas -> pasta pai)
FOLDER_CONSOLIDATION_MAP = {
    'escolaridade': ['diplomas', 'tcc', 'certificados', 'historico', 'boletins'],
    'financeiro': ['impostos', 'boletos', 'faturas', 'contas'],
    'trabalho': ['projetos', 'clientes', 'freelance'],
    'documentos pessoais': ['rg', 'cpf', 'cnh', 'certidoes'],
}

# ══════════════════════════════════════════════════════════════════════════════
# OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

OUTPUT_DIR = Path('./output')
LOG_FILE = OUTPUT_DIR / 'operations.log'
BACKUP_DIR = OUTPUT_DIR / 'backups'
