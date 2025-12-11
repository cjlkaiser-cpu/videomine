#!/usr/bin/env python3
"""
🏛️ VideoMine - Vault
Almacenamiento de nuggets (pepitas de conocimiento).
Base de datos y generación de HTML.
"""

import json
from datetime import datetime
from pathlib import Path

import jinja2

from compass import OUTPUT_DIR, TEMPLATE_DIR, DB_FILE, INDEX_FILE
from pickaxe import format_duration, get_safe_filename


def load_nuggets() -> list:
    """Carga la base de datos de nuggets."""
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return []


def save_nugget(video_info: dict, summary: dict, filename: str) -> list:
    """
    Guarda un nugget en el vault.

    Args:
        video_info: Metadatos del video
        summary: Resumen estructurado del video
        filename: Nombre del archivo HTML generado

    Returns:
        Lista actualizada de nuggets
    """
    nuggets = load_nuggets()

    entry = {
        "id": video_info['id'],
        "title": video_info.get('title', 'Sin título'),
        "channel": video_info.get('channel', 'Desconocido'),
        "duration": format_duration(video_info.get('duration', 0)),
        "url": video_info.get('webpage_url', '#'),
        "thumbnail": video_info.get('thumbnail', ''),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "file": filename,
        # Guardar resumen completo para exportar
        "idea_principal": summary.get('idea_principal', ''),
        "puntos_clave": summary.get('puntos_clave', []),
        "codigo_comandos": summary.get('codigo_comandos', []),
        "recursos_mencionados": summary.get('recursos_mencionados', []),
        "preguntas_profundizar": summary.get('preguntas_profundizar', []),
        "glosario": summary.get('glosario', {}),
        # Transcripción original
        "transcript": summary.get('transcript', '')
    }

    # Evitar duplicados
    nuggets = [n for n in nuggets if n['id'] != entry['id']]
    nuggets.append(entry)

    DB_FILE.write_text(json.dumps(nuggets, indent=2, ensure_ascii=False))
    return nuggets


def forge_html(video_info: dict, summary: dict) -> str:
    """
    Genera el HTML del nugget usando Jinja2.

    Args:
        video_info: Metadatos del video
        summary: Resumen estructurado

    Returns:
        HTML renderizado
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
        autoescape=True
    )
    template = env.get_template("nugget.html")

    return template.render(
        video_id=video_info.get('id', ''),
        titulo=video_info.get('title', 'Sin título'),
        canal=video_info.get('channel', 'Desconocido'),
        duracion=format_duration(video_info.get('duration', 0)),
        url=video_info.get('webpage_url', '#'),
        fecha=datetime.now().strftime('%Y-%m-%d'),
        thumbnail=video_info.get('thumbnail', ''),
        **summary
    )


def forge_index(nuggets: list):
    """
    Genera el índice HTML del vault.

    Args:
        nuggets: Lista de nuggets
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
        autoescape=True
    )
    template = env.get_template("index.html")
    html = template.render(videos=nuggets)
    INDEX_FILE.write_text(html)


def delete_nugget(video_id: str) -> bool:
    """
    Elimina un nugget del vault.

    Args:
        video_id: ID del video a eliminar

    Returns:
        True si se eliminó, False si no se encontró
    """
    nuggets = load_nuggets()

    # Buscar nugget
    nugget = next((n for n in nuggets if n['id'] == video_id), None)
    if not nugget:
        print(f"❌ Nugget no encontrado: {video_id}")
        print("\nNuggets disponibles:")
        for n in nuggets:
            print(f"   {n['id']} - {n['title'][:50]}")
        return False

    # Borrar archivo HTML
    html_file = OUTPUT_DIR / nugget['file']
    if html_file.exists():
        html_file.unlink()
        print(f"🗑️  Borrado: {html_file.name}")

    # Actualizar DB
    nuggets = [n for n in nuggets if n['id'] != video_id]
    DB_FILE.write_text(json.dumps(nuggets, indent=2, ensure_ascii=False))

    # Regenerar índice
    forge_index(nuggets)

    print(f"✅ Nugget eliminado: {nugget['title'][:50]}")
    print(f"   Quedan {len(nuggets)} nuggets")
    return True
