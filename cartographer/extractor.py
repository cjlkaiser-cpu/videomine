#!/usr/bin/env python3
"""
Cartographer - Extractor
Extrae conceptos y relaciones de nuggets usando Claude Code CLI.
"""

import json
import subprocess
from typing import Optional
from pathlib import Path

from compass import LLM_TIMEOUT


EXTRACTION_PROMPT = """Analiza este nugget de conocimiento y extrae los conceptos clave y sus relaciones.

TÍTULO: {title}
IDEA PRINCIPAL: {idea_principal}
PUNTOS CLAVE: {puntos_clave}
GLOSARIO: {glosario}

Genera un JSON con esta estructura exacta (sin texto adicional, solo el JSON):
{{
    "concepts": [
        {{
            "name": "Nombre del concepto (capitalizado, singular)",
            "type": "categoria",
            "importance": 0.8,
            "parent": "Concepto padre si existe o null"
        }}
    ],
    "relations": [
        {{
            "from": "Concepto origen",
            "to": "Concepto destino",
            "type": "tipo_relacion",
            "strength": 0.7
        }}
    ]
}}

REGLAS:
1. Tipos de concepto: "lenguaje", "libreria", "framework", "herramienta", "concepto", "metodologia", "patron"
2. Tipos de relación: "es_parte_de", "usa", "requiere", "relacionado", "alternativa", "implementa"
3. importance: 0.0-1.0 (qué tan central es el concepto en el video)
4. strength: 0.0-1.0 (qué tan fuerte es la relación)
5. Normaliza nombres: "Python 3" -> "Python", "machine learning" -> "Machine Learning"
6. Máximo 15 conceptos por video (los más importantes)
7. Solo relaciones significativas, no obvias

IMPORTANTE: Responde SOLO con el JSON válido."""


def extract_concepts_claude_code(nugget: dict) -> dict:
    """
    Extrae conceptos de un nugget usando Claude Code CLI.

    Args:
        nugget: Diccionario con datos del nugget

    Returns:
        dict con concepts y relations
    """
    # Preparar datos para el prompt
    puntos = nugget.get('puntos_clave', [])
    puntos_str = '\n'.join(f"- {p}" for p in puntos) if puntos else "No disponible"

    glosario = nugget.get('glosario', {})
    glosario_str = '\n'.join(f"- {k}: {v}" for k, v in glosario.items()) if glosario else "No disponible"

    prompt = EXTRACTION_PROMPT.format(
        title=nugget.get('title', 'Sin título'),
        idea_principal=nugget.get('idea_principal', 'No disponible'),
        puntos_clave=puntos_str,
        glosario=glosario_str
    )

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=LLM_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        raise Exception(f"Claude Code timeout ({LLM_TIMEOUT}s)")
    except FileNotFoundError:
        raise Exception("Claude Code CLI no encontrado. Instala con: npm install -g @anthropic-ai/claude-code")

    if result.returncode != 0:
        raise Exception(f"Error Claude Code: {result.stderr}")

    # Parsear respuesta
    response = json.loads(result.stdout)
    content = response.get("result", result.stdout)

    return parse_extraction(content)


def parse_extraction(text: str) -> dict:
    """
    Parsea la respuesta del LLM para extraer conceptos.

    Args:
        text: Respuesta del LLM

    Returns:
        dict con concepts y relations
    """
    import re

    # Intentar parsear directamente
    try:
        data = json.loads(text.strip())
        if 'concepts' in data:
            return validate_extraction(data)
    except json.JSONDecodeError:
        pass

    # Buscar JSON en el texto
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            data = json.loads(match.group())
            if 'concepts' in data:
                return validate_extraction(data)
        except json.JSONDecodeError:
            pass

    # Fallback: estructura vacía
    print("  No se pudieron extraer conceptos")
    return {"concepts": [], "relations": []}


def validate_extraction(data: dict) -> dict:
    """
    Valida y normaliza los datos extraídos.

    Args:
        data: Datos crudos del LLM

    Returns:
        Datos validados y normalizados
    """
    valid_concept_types = {"lenguaje", "libreria", "framework", "herramienta", "concepto", "metodologia", "patron"}
    valid_relation_types = {"es_parte_de", "usa", "requiere", "relacionado", "alternativa", "implementa"}

    # Validar conceptos
    concepts = []
    for c in data.get('concepts', []):
        if not c.get('name'):
            continue
        concepts.append({
            "name": c['name'].strip(),
            "type": c.get('type', 'concepto') if c.get('type') in valid_concept_types else 'concepto',
            "importance": min(1.0, max(0.0, float(c.get('importance', 0.5)))),
            "parent": c.get('parent')
        })

    # Validar relaciones
    relations = []
    concept_names = {c['name'] for c in concepts}
    for r in data.get('relations', []):
        if not r.get('from') or not r.get('to'):
            continue
        # Solo incluir relaciones entre conceptos existentes
        if r['from'] in concept_names and r['to'] in concept_names:
            relations.append({
                "from": r['from'],
                "to": r['to'],
                "type": r.get('type', 'relacionado') if r.get('type') in valid_relation_types else 'relacionado',
                "strength": min(1.0, max(0.0, float(r.get('strength', 0.5))))
            })

    return {"concepts": concepts, "relations": relations}


def extract_from_nugget(video_id: str, vault_path: str = "vault") -> dict:
    """
    Extrae conceptos de un nugget por su ID.

    Args:
        video_id: ID del video
        vault_path: Ruta al vault

    Returns:
        dict con concepts y relations
    """
    # Cargar nuggets.json
    nuggets_file = Path(vault_path) / "nuggets.json"
    if not nuggets_file.exists():
        raise Exception(f"No existe {nuggets_file}")

    with open(nuggets_file, 'r', encoding='utf-8') as f:
        nuggets = json.load(f)

    # Buscar nugget
    nugget = None
    for n in nuggets:
        if n.get('id') == video_id:
            nugget = n
            break

    if not nugget:
        raise Exception(f"Nugget {video_id} no encontrado")

    print(f"  Extrayendo conceptos de: {nugget.get('title', video_id)[:50]}...")

    return extract_concepts_claude_code(nugget)


def extract_all(vault_path: str = "vault") -> dict:
    """
    Extrae conceptos de todos los nuggets.

    Args:
        vault_path: Ruta al vault

    Returns:
        dict {video_id: {concepts, relations}}
    """
    nuggets_file = Path(vault_path) / "nuggets.json"
    if not nuggets_file.exists():
        raise Exception(f"No existe {nuggets_file}")

    with open(nuggets_file, 'r', encoding='utf-8') as f:
        nuggets = json.load(f)

    results = {}
    for nugget in nuggets:
        video_id = nugget.get('id')
        if not video_id:
            continue

        # Solo procesar nuggets con contenido suficiente
        if not nugget.get('puntos_clave') and not nugget.get('glosario'):
            print(f"  Saltando {video_id}: sin contenido suficiente")
            continue

        try:
            results[video_id] = extract_concepts_claude_code(nugget)
            print(f"  {video_id}: {len(results[video_id]['concepts'])} conceptos")
        except Exception as e:
            print(f"  Error en {video_id}: {e}")
            results[video_id] = {"concepts": [], "relations": []}

    return results
