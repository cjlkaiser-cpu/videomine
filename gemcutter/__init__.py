#!/usr/bin/env python3
"""
💎 VideoMine - Gemcutter
Clasificador y resumidor con LLMs.
Convierte transcripciones en "gemas" de conocimiento estructurado.
"""

import json
import re
import subprocess
from typing import Optional

from compass import OLLAMA_MODEL, MAX_TRANSCRIPT_CHARS, LLM_TIMEOUT


def craft_prompt(transcript: str, video_info: dict) -> str:
    """
    Genera el prompt para el LLM.

    Args:
        transcript: Transcripción del video
        video_info: Metadatos del video

    Returns:
        Prompt estructurado para el LLM
    """
    return f"""Analiza esta transcripción de un video tutorial y genera un resumen estructurado.

TÍTULO: {video_info.get('title', 'Sin título')}
CANAL: {video_info.get('channel', 'Desconocido')}
DURACIÓN: {video_info.get('duration', 0)} segundos

TRANSCRIPCIÓN:
{transcript[:MAX_TRANSCRIPT_CHARS]}

Genera un JSON con esta estructura exacta (sin texto adicional, solo el JSON):
{{
    "idea_principal": "Una o dos oraciones con la idea central del video",
    "puntos_clave": ["punto 1", "punto 2", "punto 3"],
    "codigo_comandos": ["comando o código mencionado"],
    "recursos_mencionados": ["recurso o herramienta mencionada"],
    "preguntas_profundizar": ["pregunta para seguir aprendiendo"],
    "glosario": {{"término técnico": "definición breve"}}
}}

IMPORTANTE: Responde SOLO con el JSON válido, sin explicaciones."""


def cut_with_ollama(transcript: str, video_info: dict) -> dict:
    """
    Usa Ollama (local) para resumir.

    Args:
        transcript: Transcripción del video
        video_info: Metadatos del video

    Returns:
        dict con el resumen estructurado
    """
    prompt = craft_prompt(transcript, video_info)

    cmd = ["ollama", "run", OLLAMA_MODEL, prompt]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=LLM_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise Exception(f"Ollama tardó demasiado en responder (timeout {LLM_TIMEOUT}s)")

    if result.returncode != 0:
        raise Exception(f"Error con Ollama: {result.stderr}")

    return parse_nugget(result.stdout)


def cut_with_claude(transcript: str, video_info: dict) -> dict:
    """
    Usa Claude API para resumir (paga por tokens).

    Args:
        transcript: Transcripción del video
        video_info: Metadatos del video

    Returns:
        dict con el resumen estructurado
    """
    import anthropic

    client = anthropic.Anthropic()
    prompt = craft_prompt(transcript, video_info)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_nugget(response.content[0].text)


def cut_with_claude_code(transcript: str, video_info: dict) -> dict:
    """
    Usa Claude Code CLI (tu suscripción Pro/Max, sin pagar por tokens).

    Args:
        transcript: Transcripción del video
        video_info: Metadatos del video

    Returns:
        dict con el resumen estructurado
    """
    prompt = craft_prompt(transcript, video_info)

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=LLM_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        raise Exception(f"Claude Code tardó demasiado en responder (timeout {LLM_TIMEOUT}s)")

    if result.returncode != 0:
        raise Exception(f"Error con Claude Code: {result.stderr}")

    # El output es JSON con estructura {"result": "..."}
    response = json.loads(result.stdout)
    return parse_nugget(response.get("result", result.stdout))


def parse_nugget(text: str) -> dict:
    """
    Extrae JSON de la respuesta del LLM.
    El "nugget" es la pepita de conocimiento estructurado.

    Args:
        text: Respuesta del LLM

    Returns:
        dict con el resumen estructurado
    """
    # Intentar parsear directamente
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Buscar JSON en el texto
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: estructura vacía
    print("  ⚠️  No se pudo parsear JSON, usando estructura básica")
    return {
        "idea_principal": "Ver el video para más detalles",
        "puntos_clave": ["Revisar transcripción completa"],
        "codigo_comandos": [],
        "recursos_mencionados": [],
        "preguntas_profundizar": [],
        "glosario": {}
    }
