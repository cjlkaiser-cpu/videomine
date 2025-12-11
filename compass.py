#!/usr/bin/env python3
"""
⛏️ VideoMine - Configuración (Compass)
La brújula que guía el sistema minerOS.

Variables de entorno:
- VIDEOMINE_MODEL: Modelo de Ollama (default: llama3.2)
- VIDEOMINE_MAX_CHARS: Máximo de caracteres de transcripción (default: 12000)
- VIDEOMINE_TIMEOUT: Timeout LLM en segundos (default: 300)
- VIDEOMINE_HOST: Host del servidor (default: 127.0.0.1)
- VIDEOMINE_PORT: Puerto del servidor (default: 5555)
"""

import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Compass:
    """Configuración de VideoMine - La brújula del sistema."""
    # Directorios
    base_dir: Path
    vault_dir: Path      # output/ → vault/ (almacenamiento)
    template_dir: Path
    pending_dir: Path

    # Archivos
    db_file: Path        # La base de datos del vault
    index_file: Path     # Índice del vault

    # LLM (Gemcutter)
    ollama_model: str
    max_transcript_chars: int
    llm_timeout: int

    # Server (Compass Web)
    server_host: str
    server_port: int

    @classmethod
    def load(cls, base_dir: Path = None) -> 'Compass':
        """Carga la configuración desde variables de entorno y valores por defecto."""
        base = base_dir or Path(__file__).parent
        vault = base / "vault"

        return cls(
            base_dir=base,
            vault_dir=vault,
            template_dir=base / "compass" / "templates",
            pending_dir=vault / "pending",
            db_file=vault / "nuggets.json",  # videos.json → nuggets.json
            index_file=vault / "index.html",
            ollama_model=os.environ.get("VIDEOMINE_MODEL", "llama3.2"),
            max_transcript_chars=int(os.environ.get("VIDEOMINE_MAX_CHARS", "12000")),
            llm_timeout=int(os.environ.get("VIDEOMINE_TIMEOUT", "300")),
            server_host=os.environ.get("VIDEOMINE_HOST", "127.0.0.1"),
            server_port=int(os.environ.get("VIDEOMINE_PORT", "5555")),
        )


# Instancia global de configuración
compass = Compass.load()

# Exportar constantes para compatibilidad
SCRIPT_DIR = compass.base_dir
OUTPUT_DIR = compass.vault_dir
TEMPLATE_DIR = compass.template_dir
PENDING_DIR = compass.pending_dir
DB_FILE = compass.db_file
INDEX_FILE = compass.index_file
OLLAMA_MODEL = compass.ollama_model
MAX_TRANSCRIPT_CHARS = compass.max_transcript_chars
LLM_TIMEOUT = compass.llm_timeout
SERVER_HOST = compass.server_host
SERVER_PORT = compass.server_port
