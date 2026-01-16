"""
Cliente de IA para integracao com Claude Opus 4.5 na Azure.
Permite analise inteligente e sugestoes avancadas de organizacao.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass

try:
    from anthropic import AnthropicFoundry
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    AnthropicFoundry = None  # type: ignore

if TYPE_CHECKING:
    from .models import FolderAnalysis, FileItem


@dataclass
class AIConfig:
    """Configuracao do cliente de IA."""
    api_key: str
    endpoint: str = "https://conta-ma6t6uyn-eastus2.services.ai.azure.com/anthropic/"
    model: str = "claude-opus-4-5"
    max_tokens: int = 4096
    temperature: float = 0.2


# Prompt do sistema para o agente de organizacao
SYSTEM_PROMPT = """Voce e um Agente de Organizacao de Arquivos Inteligente especializado em analise de estrutura de diretorios e reorganizacao seguindo um padrao hierarquico numerico padronizado.

PADRAO DE ORGANIZACAO:
- Formato: [NN] Nome_Descritivo (NN = numero 01-99)
- [01]-[30]: Pastas ativas/em uso frequente
- [31]-[70]: Pastas de suporte/referencia
- [71]-[98]: Pastas temporarias/em processamento
- [99]: Pastas arquivadas/inativas

PRIORIDADES POR PALAVRA-CHAVE:
- desenvolvimento, dev, trabalho, projetos -> [01]-[10]
- documentos, estudos, pessoal -> [11]-[30]
- softwares, ferramentas, recursos -> [31]-[50]
- backups, storage, midia -> [51]-[70]
- temp, temporario, downloads -> [71]-[90]
- arquivado, old -> [99]

REGRAS:
1. Analise o contexto de cada pasta pelo nome
2. Sugira numeros baseado na provavel frequencia de uso
3. Mantenha consistencia hierarquica
4. Evite conflitos de numeracao no mesmo nivel
5. Responda SEMPRE em JSON valido

Quando receber uma lista de pastas, responda com:
{
  "sugestoes": [
    {"nome_atual": "...", "numero_sugerido": NN, "nome_novo": "[NN] ...", "razao": "..."},
    ...
  ],
  "observacoes": "...",
  "score_potencial": N
}"""


def _extract_text_from_response(response: Any) -> str:
    """Extrai texto da resposta do Claude de forma segura."""
    if not response or not response.content:
        return ""
    
    for block in response.content:
        if hasattr(block, 'text'):
            return block.text
    
    return str(response.content[0]) if response.content else ""


class AIClient:
    """
    Cliente para comunicacao com Claude Opus 4.5 na Azure.
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config: Optional[AIConfig] = config
        self._client: Any = None
        self._enabled: bool = False
        
        if config and HAS_ANTHROPIC:
            self._init_client()
    
    def _init_client(self) -> None:
        """Inicializa cliente Anthropic."""
        if not self.config or not HAS_ANTHROPIC:
            return
        
        try:
            self._client = AnthropicFoundry(
                api_key=self.config.api_key,
                base_url=self.config.endpoint
            )
            self._enabled = True
            print("[AI] Cliente Claude Opus 4.5 inicializado")
        except Exception as e:
            print(f"[AI-ERRO] Falha ao inicializar cliente: {e}")
            self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._client is not None and self.config is not None
    
    def analyze_folders(self, folders: List[Any]) -> Dict[str, Any]:
        """
        Envia lista de pastas para analise inteligente pelo Claude.
        Retorna sugestoes de organizacao.
        """
        if not self.is_enabled or not self._client or not self.config:
            return {"error": "Cliente AI nao esta habilitado"}
        
        # Prepara dados para enviar
        folder_data = [
            {
                "nome": f.name,
                "profundidade": f.depth,
                "tamanho_mb": round(f.size_bytes / 1_048_576, 2),
                "filhos": f.children_count,
            }
            for f in folders
        ]
        
        user_message = f"""Analise estas pastas e sugira a melhor organizacao com numeracao [NN]:

PASTAS PARA ORGANIZAR:
{json.dumps(folder_data, indent=2, ensure_ascii=False)}

Responda em JSON com sugestoes de numeracao."""
        
        try:
            response = self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "user", "content": SYSTEM_PROMPT + "\n\n" + user_message}
                ]
            )
            
            content = _extract_text_from_response(response)
            
            # Tenta parsear JSON da resposta
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                return {"raw_response": content}
            
            return {"raw_response": content}
        
        except Exception as e:
            return {"error": str(e)}
    
    def get_smart_suggestion(self, folder_name: str, context: str = "") -> Dict[str, Any]:
        """
        Obtem sugestao inteligente para uma unica pasta.
        """
        if not self.is_enabled or not self._client or not self.config:
            return {"error": "Cliente AI nao esta habilitado"}
        
        user_message = f"""Sugira o melhor numero [NN] para esta pasta:

Nome: {folder_name}
Contexto: {context}

Responda em JSON:
{{"numero": NN, "nome_sugerido": "[NN] ...", "razao": "..."}}"""
        
        try:
            response = self._client.messages.create(
                model=self.config.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": SYSTEM_PROMPT + "\n\n" + user_message}
                ]
            )
            
            content = _extract_text_from_response(response)
            
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except Exception:
                pass
            
            return {"raw_response": content}
        
        except Exception as e:
            return {"error": str(e)}
    
    def generate_reorganization_plan(self, analysis: Any) -> Dict[str, Any]:
        """
        Gera plano de reorganizacao completo usando IA.
        """
        if not self.is_enabled or not self._client or not self.config:
            return {"error": "Cliente AI nao esta habilitado"}
        
        # Prepara resumo da analise
        summary = {
            "caminho_raiz": str(analysis.root_path),
            "total_pastas": analysis.total_folders,
            "total_arquivos": analysis.total_files,
            "profundidade_max": analysis.max_depth,
            "score_atual": analysis.organization_score,
            "pastas_nao_conformes": [
                {"nome": f.name, "profundidade": f.depth}
                for f in analysis.items
                if f.item_type == 'folder' and not f.is_conformant
            ][:50]
        }
        
        user_message = f"""Analise esta estrutura de pastas e gere um plano de reorganizacao completo:

ANALISE ATUAL:
{json.dumps(summary, indent=2, ensure_ascii=False)}

Gere um plano em JSON com:
{{
  "plano": [
    {{"pasta": "...", "acao": "renomear", "de": "...", "para": "[NN] ..."}},
    ...
  ],
  "ordem_execucao": ["pasta1", "pasta2", ...],
  "score_esperado": N,
  "observacoes": "..."
}}"""
        
        try:
            response = self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "user", "content": SYSTEM_PROMPT + "\n\n" + user_message}
                ]
            )
            
            content = _extract_text_from_response(response)
            
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except Exception:
                pass
            
            return {"raw_response": content}
        
        except Exception as e:
            return {"error": str(e)}


def create_ai_client_from_env() -> Optional[AIClient]:
    """
    Cria cliente AI a partir de variaveis de ambiente.
    """
    import os
    
    api_key = os.environ.get('AZURE_AI_KEY')
    endpoint = os.environ.get('AZURE_AI_ENDPOINT')
    
    if api_key:
        config = AIConfig(
            api_key=api_key,
            endpoint=endpoint or "https://conta-ma6t6uyn-eastus2.services.ai.azure.com/anthropic/"
        )
        return AIClient(config)
    
    return None
