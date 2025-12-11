#!/usr/bin/env python3
"""
⛏️ VideoMine - Extractor (Pickaxe)
Herramientas para extraer información de videos.
"""

import re


def format_duration(seconds: int) -> str:
    """Formatea una duración en segundos a formato MM:SS."""
    return f"{seconds // 60}:{seconds % 60:02d}"


def get_safe_filename(title: str, video_id: str, extension: str = "html") -> str:
    """
    Genera un nombre de archivo seguro a partir del título del video.

    Args:
        title: Título del video
        video_id: ID del video de YouTube
        extension: Extensión del archivo (sin punto)

    Returns:
        Nombre de archivo seguro (nugget_TITLE_ID.ext)
    """
    safe_title = re.sub(r'[^\w\s-]', '', title)[:50].strip()
    return f"nugget_{safe_title}_{video_id}.{extension}"


def clean_vtt(vtt_content: str) -> str:
    """Limpia el formato VTT y devuelve texto plano."""
    lines = []
    for line in vtt_content.split('\n'):
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        if '-->' in line:
            continue
        if re.match(r'^\d+$', line.strip()):
            continue
        if line.strip():
            clean = re.sub(r'<[^>]+>', '', line)
            lines.append(clean.strip())

    # Eliminar duplicados consecutivos
    result = []
    prev = ""
    for line in lines:
        if line != prev:
            result.append(line)
            prev = line

    return ' '.join(result)
