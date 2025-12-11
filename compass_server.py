#!/usr/bin/env python3
"""
🧭 VideoMine - Compass Server
API local para gestionar el Vault de nuggets.
Uso: python compass_server.py o python videomine.py --server
"""

import json
import re
import subprocess
import threading
import queue
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

# Regex para validar URLs de YouTube
YOUTUBE_URL_REGEX = re.compile(
    r'^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)'
)

# Importar configuración
from compass import OUTPUT_DIR, TEMPLATE_DIR, DB_FILE, INDEX_FILE, PENDING_DIR, SERVER_HOST, SERVER_PORT

# Importar módulos minerOS
from tunnel import scan_video, extract_subtitles, transcribe_audio
from gemcutter import cut_with_ollama, cut_with_claude_code, parse_nugget
from vault import load_nuggets, save_nugget, forge_html, forge_index, delete_nugget
from pickaxe import format_duration, get_safe_filename

app = Flask(__name__, static_folder='vault')
CORS(app, origins=['http://localhost:5555', 'http://127.0.0.1:5555'])

# Cola de progreso para SSE
progress_queues = {}


def process_video_task(url: str, motor: str, task_id: str):
    """Procesa un video en background (pipeline minerOS)."""
    q = progress_queues.get(task_id, queue.Queue())

    try:
        # 1. TUNNEL: Escanear
        q.put({"step": "tunnel", "msg": "🔦 Escaneando video...", "progress": 10})
        video_info = scan_video(url)
        video_id = video_info['id']
        q.put({"step": "tunnel", "msg": f"Video: {video_info['title'][:50]}", "progress": 20})

        # 2. PICKAXE: Extraer transcripción
        q.put({"step": "pickaxe", "msg": "⛏️ Extrayendo transcripción...", "progress": 30})
        transcript = extract_subtitles(url, video_id)

        if not transcript:
            q.put({"step": "pickaxe", "msg": "⛏️ Usando Whisper...", "progress": 40})
            transcript = transcribe_audio(url, video_id)

        q.put({"step": "pickaxe", "msg": f"Transcripción: {len(transcript)} chars", "progress": 50})

        # 3. GEMCUTTER: Resumir según motor
        if motor == "ollama":
            q.put({"step": "gemcutter", "msg": "💎 Puliendo con Ollama...", "progress": 60})
            summary = cut_with_ollama(transcript, video_info)
            q.put({"step": "gemcutter", "msg": "💎 Nugget pulido", "progress": 80})
        elif motor == "claude-code":
            q.put({"step": "gemcutter", "msg": "💎 Puliendo con Claude Code...", "progress": 60})
            summary = cut_with_claude_code(transcript, video_info)
            q.put({"step": "gemcutter", "msg": "💎 Nugget pulido", "progress": 80})
        else:
            # Modo manual - guardar transcripción y esperar
            PENDING_DIR.mkdir(parents=True, exist_ok=True)
            (PENDING_DIR / f"{video_id}.txt").write_text(transcript)
            (PENDING_DIR / f"{video_id}.json").write_text(
                json.dumps(video_info, indent=2, ensure_ascii=False)
            )
            q.put({
                "step": "manual",
                "msg": "📄 Transcripción lista",
                "progress": 50,
                "video_id": video_id,
                "title": video_info['title'],
                "transcript": transcript[:5000] + "..." if len(transcript) > 5000 else transcript,
                "needs_summary": True
            })
            return

        # 4. VAULT: Almacenar
        q.put({"step": "vault", "msg": "🏛️ Guardando en Vault...", "progress": 90})
        html = forge_html(video_info, summary)

        OUTPUT_DIR.mkdir(exist_ok=True)
        output_file = OUTPUT_DIR / get_safe_filename(video_info['title'], video_id)
        output_file.write_text(html)

        # 5. Actualizar índice
        nuggets = save_nugget(video_info, summary, output_file.name)
        forge_index(nuggets)

        q.put({
            "step": "done",
            "msg": "✅ ¡Nugget extraído!",
            "progress": 100,
            "file": output_file.name,
            "title": video_info['title']
        })

    except Exception as e:
        q.put({"step": "error", "msg": str(e), "progress": 0})


@app.route('/')
def index():
    return send_from_directory(OUTPUT_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_file(filename):
    """Sirve archivos HTML desde vault/ con validación de path traversal."""
    if not filename.endswith('.html'):
        return "Not found", 404

    # Prevenir path traversal
    requested_path = (OUTPUT_DIR / filename).resolve()
    if not str(requested_path).startswith(str(OUTPUT_DIR.resolve())):
        return "Forbidden", 403

    if not requested_path.exists():
        return "Not found", 404

    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/api/videos', methods=['GET'])
def list_videos():
    nuggets = load_nuggets()
    return jsonify(nuggets)


@app.route('/api/add', methods=['POST'])
def add_video():
    data = request.json
    url = (data.get('url') or '').strip()
    motor = data.get('motor', 'ollama')

    if not url:
        return jsonify({"error": "URL requerida"}), 400

    # Validar que sea URL de YouTube
    if not YOUTUBE_URL_REGEX.match(url):
        return jsonify({"error": "URL de YouTube inválida"}), 400

    # Crear task ID
    task_id = datetime.now().strftime('%Y%m%d%H%M%S')
    progress_queues[task_id] = queue.Queue()

    # Procesar en background
    thread = threading.Thread(target=process_video_task, args=(url, motor, task_id))
    thread.start()

    return jsonify({"task_id": task_id})


@app.route('/api/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    q = progress_queues.get(task_id)
    if not q:
        return jsonify({"error": "Task no encontrada"}), 404

    updates = []
    while not q.empty():
        updates.append(q.get_nowait())

    return jsonify(updates)


@app.route('/api/finish', methods=['POST'])
def finish_video():
    """Completar video con resumen manual."""
    data = request.json
    video_id = data.get('video_id')
    summary_json = data.get('summary')

    transcript_file = PENDING_DIR / f"{video_id}.txt"
    info_file = PENDING_DIR / f"{video_id}.json"

    if not transcript_file.exists():
        return jsonify({"error": "Video pendiente no encontrado"}), 404

    video_info = json.loads(info_file.read_text())
    summary = parse_nugget(summary_json) if isinstance(summary_json, str) else summary_json

    # Generar HTML
    html = forge_html(video_info, summary)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / get_safe_filename(video_info['title'], video_id)
    output_file.write_text(html)

    # Actualizar índice
    nuggets = save_nugget(video_info, summary, output_file.name)
    forge_index(nuggets)

    # Limpiar pendientes
    transcript_file.unlink()
    info_file.unlink()

    return jsonify({"success": True, "file": output_file.name})


@app.route('/api/delete/<video_id>', methods=['DELETE'])
def api_delete_video(video_id):
    success = delete_nugget(video_id)
    return jsonify({"success": success})


@app.route('/api/export/<video_id>', methods=['GET'])
def export_markdown(video_id):
    """Exporta un nugget a Markdown completo (descarga directa)."""
    nuggets = load_nuggets()
    nugget = next((n for n in nuggets if n['id'] == video_id), None)

    if not nugget:
        return jsonify({"error": "Nugget no encontrado"}), 404

    md = f"""# {nugget['title']}

> **Canal:** {nugget['channel']} | **Duración:** {nugget['duration']} | **Fecha:** {nugget['date']}
>
> [Ver video en YouTube]({nugget['url']})

---

## Idea Principal

{nugget.get('idea_principal', 'N/A')}

---

## Puntos Clave

"""

    puntos = nugget.get('puntos_clave', [])
    if puntos:
        for punto in puntos:
            md += f"- {punto}\n"
    else:
        md += "- Ver nota HTML para detalles\n"

    md += """
---

## Código y Comandos

"""
    comandos = nugget.get('codigo_comandos', [])
    if comandos:
        for cmd in comandos:
            md += f"```\n{cmd}\n```\n\n"
    else:
        md += "_No hay comandos registrados_\n"

    md += """
---

## Recursos Mencionados

"""
    recursos = nugget.get('recursos_mencionados', [])
    if recursos:
        for recurso in recursos:
            md += f"- {recurso}\n"
    else:
        md += "_No hay recursos registrados_\n"

    md += """
---

## Preguntas para Profundizar

"""
    preguntas = nugget.get('preguntas_profundizar', [])
    if preguntas:
        for pregunta in preguntas:
            md += f"- {pregunta}\n"
    else:
        md += "_No hay preguntas registradas_\n"

    md += """
---

## Glosario

"""
    glosario = nugget.get('glosario', {})
    if glosario:
        for term, defn in glosario.items():
            md += f"**{term}**: {defn}\n\n"
    else:
        md += "_No hay términos en el glosario_\n"

    md += f"""
---

_Generado con VideoMine ⛏️_
"""

    safe_title = re.sub(r'[^\w\s-]', '', nugget['title'])[:50].strip()
    filename = f"{safe_title}.md"

    # Descarga directa con headers apropiados
    response = Response(
        md,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/plain; charset=utf-8'
        }
    )
    return response


@app.route('/api/transcript/<video_id>', methods=['GET'])
def get_transcript(video_id):
    """Obtiene la transcripción de un nugget."""
    nuggets = load_nuggets()
    nugget = next((n for n in nuggets if n['id'] == video_id), None)

    if not nugget:
        return jsonify({"error": "Nugget no encontrado"}), 404

    transcript = nugget.get('transcript', '')

    # Si no hay transcripción guardada, intentar leer del pending
    if not transcript:
        transcript_file = PENDING_DIR / f"{video_id}.txt"
        if transcript_file.exists():
            transcript = transcript_file.read_text()

    return jsonify({
        "transcript": transcript,
        "title": nugget.get('title', '')
    })


@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Traduce texto al español usando Ollama."""
    data = request.json
    text = data.get('text', '')[:8000]  # Limitar tamaño

    if not text:
        return jsonify({"error": "No hay texto"}), 400

    prompt = f"""Traduce el siguiente texto al español.
Mantén el formato y la estructura. Solo devuelve la traducción, sin explicaciones.

TEXTO:
{text}

TRADUCCIÓN AL ESPAÑOL:"""

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2", prompt],
            capture_output=True, text=True, timeout=120
        )
        translation = result.stdout.strip()
        return jsonify({"translation": translation})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Traducción tardó demasiado (timeout 2 min)"}), 500
    except Exception as e:
        return jsonify({"error": "Error en traducción"}), 500


@app.route('/api/export-html/<video_id>', methods=['GET'])
def export_html(video_id):
    """Exporta un nugget como HTML imprimible con campos para notas."""
    nuggets = load_nuggets()
    nugget = next((n for n in nuggets if n['id'] == video_id), None)

    if not nugget:
        return jsonify({"error": "Nugget no encontrado"}), 404

    # Generar puntos clave con checkboxes
    puntos_html = ""
    for punto in nugget.get('puntos_clave', []):
        puntos_html += f'<div class="punto"><label><input type="checkbox"> {punto}</label></div>\n'

    # Generar preguntas
    preguntas_html = ""
    for pregunta in nugget.get('preguntas_profundizar', []):
        preguntas_html += f'''<div class="pregunta">
            <p>{pregunta}</p>
            <textarea placeholder="Tu respuesta..."></textarea>
        </div>\n'''

    # Generar glosario
    glosario_html = ""
    for term, defn in nugget.get('glosario', {}).items():
        glosario_html += f'<div class="termino"><strong>{term}:</strong> {defn}</div>\n'

    # Generar código/comandos
    codigo_html = ""
    for cmd in nugget.get('codigo_comandos', []):
        codigo_html += f'<pre class="codigo">{cmd}</pre>\n'

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nugget['title']} - VideoMine</title>
    <style>
        @media print {{
            .no-print {{ display: none; }}
            body {{ padding: 15mm; }}
            .page-break {{ page-break-before: always; }}
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #000;
            padding: 20mm;
            max-width: 210mm;
            margin: 0 auto;
        }}

        h1 {{
            font-size: 16pt;
            margin-bottom: 5mm;
            border-bottom: 2px solid #000;
            padding-bottom: 3mm;
        }}

        h2 {{
            font-size: 13pt;
            margin: 8mm 0 4mm 0;
            border-bottom: 1px solid #ccc;
            padding-bottom: 2mm;
            color: #333;
        }}

        .header-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 3mm;
            margin-bottom: 8mm;
            padding: 4mm;
            background: #f5f5f5;
            border: 1px solid #ddd;
            font-size: 10pt;
        }}

        .header-info span {{
            color: #666;
        }}

        .header-info a {{
            color: #0066cc;
        }}

        .idea-principal {{
            background: #e8f5e9;
            padding: 5mm;
            border-left: 4px solid #4caf50;
            margin: 5mm 0;
            font-size: 12pt;
        }}

        .punto {{
            padding: 2mm 0;
            border-bottom: 1px dotted #ddd;
        }}

        .punto label {{
            display: flex;
            align-items: flex-start;
            gap: 3mm;
        }}

        .punto input[type="checkbox"] {{
            margin-top: 2px;
            width: 4mm;
            height: 4mm;
        }}

        .pregunta {{
            margin: 4mm 0;
            padding: 3mm;
            background: #fff3e0;
            border: 1px solid #ffcc80;
        }}

        .pregunta p {{
            font-weight: bold;
            margin-bottom: 2mm;
            font-size: 10pt;
        }}

        .pregunta textarea {{
            width: 100%;
            height: 20mm;
            border: 1px solid #ccc;
            padding: 2mm;
            font-family: inherit;
            font-size: 10pt;
        }}

        .termino {{
            padding: 2mm 0;
            border-bottom: 1px dotted #ddd;
            font-size: 10pt;
        }}

        .codigo {{
            background: #f5f5f5;
            padding: 3mm;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 9pt;
            overflow-x: auto;
            border: 1px solid #ddd;
            margin: 2mm 0;
        }}

        .notas-section {{
            margin-top: 8mm;
            padding: 5mm;
            border: 2px solid #000;
        }}

        .notas-section h2 {{
            border: none;
            margin-top: 0;
        }}

        .notas-section textarea {{
            width: 100%;
            height: 50mm;
            border: 1px solid #ccc;
            padding: 3mm;
            font-family: inherit;
        }}

        .fecha-estudio {{
            margin-top: 5mm;
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 3mm;
            align-items: center;
        }}

        .fecha-estudio input {{
            border: none;
            border-bottom: 1px solid #000;
            padding: 2mm;
            width: 40mm;
        }}

        footer {{
            margin-top: 10mm;
            padding-top: 5mm;
            border-top: 1px solid #ccc;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }}

        .btn-print {{
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 10px 20px;
            background: #ffa500;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }}

        .btn-print:hover {{
            background: #ff8c00;
        }}
    </style>
</head>
<body>
    <button class="btn-print no-print" onclick="window.print()">Imprimir</button>

    <h1>{nugget['title']}</h1>

    <div class="header-info">
        <div><strong>Canal:</strong> <span>{nugget['channel']}</span></div>
        <div><strong>Duracion:</strong> <span>{nugget['duration']}</span></div>
        <div><strong>Fecha:</strong> <span>{nugget['date']}</span></div>
        <div><strong>Video:</strong> <a href="{nugget['url']}" target="_blank">Ver en YouTube</a></div>
    </div>

    <h2>Idea Principal</h2>
    <div class="idea-principal">
        {nugget.get('idea_principal', 'N/A')}
    </div>

    <h2>Puntos Clave</h2>
    {puntos_html if puntos_html else '<p style="color:#666">Sin puntos clave registrados</p>'}

    {f'<h2>Codigo y Comandos</h2>{codigo_html}' if codigo_html else ''}

    <h2>Preguntas para Profundizar</h2>
    {preguntas_html if preguntas_html else '<p style="color:#666">Sin preguntas registradas</p>'}

    {f'<h2>Glosario</h2>{glosario_html}' if glosario_html else ''}

    <div class="notas-section">
        <h2>Mis Notas</h2>
        <textarea placeholder="Escribe aqui tus notas personales sobre este video..."></textarea>
        <div class="fecha-estudio">
            <label><strong>Fecha de estudio:</strong></label>
            <input type="text" placeholder="DD/MM/AAAA">
        </div>
    </div>

    <footer>
        Generado con VideoMine - {nugget['date']}
    </footer>
</body>
</html>'''

    safe_title = re.sub(r'[^\w\s-]', '', nugget['title'])[:50].strip()
    filename = f"{safe_title}.html"

    response = Response(
        html,
        mimetype='text/html',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/html; charset=utf-8'
        }
    )
    return response


@app.route('/api/search', methods=['GET'])
def search_videos():
    """Busca en títulos, transcripciones y contenido de nuggets."""
    query = request.args.get('q', '').lower().strip()

    if not query or len(query) < 2:
        return jsonify({"results": [], "query": query})

    nuggets = load_nuggets()
    results = []

    for nugget in nuggets:
        score = 0
        matches = []

        # Buscar en título (peso alto)
        if query in nugget.get('title', '').lower():
            score += 10
            matches.append("título")

        # Buscar en idea principal
        if query in nugget.get('idea_principal', '').lower():
            score += 5
            matches.append("idea principal")

        # Buscar en puntos clave
        for punto in nugget.get('puntos_clave', []):
            if query in punto.lower():
                score += 3
                matches.append("puntos clave")
                break

        # Buscar en transcripción
        transcript = nugget.get('transcript', '')
        if query in transcript.lower():
            score += 2
            matches.append(f"transcripción")

        # Buscar en glosario
        for term, defn in nugget.get('glosario', {}).items():
            if query in term.lower() or query in defn.lower():
                score += 4
                matches.append("glosario")
                break

        # Buscar en canal
        if query in nugget.get('channel', '').lower():
            score += 2
            matches.append("canal")

        if score > 0:
            results.append({
                "id": nugget['id'],
                "title": nugget['title'],
                "channel": nugget['channel'],
                "thumbnail": nugget.get('thumbnail', ''),
                "file": nugget['file'],
                "score": score,
                "matches": list(set(matches))
            })

    results.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({
        "results": results[:20],
        "query": query,
        "total": len(results)
    })


@app.route('/api/export-anki/<video_id>', methods=['GET'])
def export_anki(video_id):
    """Exporta flashcards en formato Anki (TSV) - descarga directa."""
    nuggets = load_nuggets()
    nugget = next((n for n in nuggets if n['id'] == video_id), None)

    if not nugget:
        return jsonify({"error": "Nugget no encontrado"}), 404

    cards = []
    source_tag = f"videomine::{nugget['id']}"

    # Cards del glosario
    for term, defn in nugget.get('glosario', {}).items():
        front = f"¿Qué es <b>{term}</b>?"
        back = f"{defn}<br><br><small>Fuente: {nugget['title']}</small>"
        cards.append(f"{front}\t{back}\t{source_tag}")

    # Card de idea principal
    idea = nugget.get('idea_principal', '')
    if idea:
        front = f"¿Cuál es la idea principal del video<br><i>{nugget['title'][:50]}</i>?"
        back = f"{idea}<br><br><small>Canal: {nugget['channel']}</small>"
        cards.append(f"{front}\t{back}\t{source_tag}")

    # Cards de comandos
    for cmd in nugget.get('codigo_comandos', [])[:5]:
        front = f"¿Para qué sirve este comando?<br><code>{cmd[:100]}</code>"
        back = f"Comando mencionado en: {nugget['title']}<br><br><small>Revisar video para contexto</small>"
        cards.append(f"{front}\t{back}\t{source_tag}")

    if not cards:
        return jsonify({"error": "No hay flashcards para este nugget", "card_count": 0}), 404

    tsv_content = "\n".join(cards)

    safe_title = re.sub(r'[^\w\s-]', '', nugget['title'])[:30].strip()
    filename = f"anki_{safe_title}.txt"

    response = Response(
        tsv_content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/plain; charset=utf-8'
        }
    )
    return response


@app.route('/api/concept-map/<video_id>', methods=['GET'])
def get_concept_map(video_id):
    """Genera un mapa conceptual de relaciones entre puntos clave."""
    nuggets = load_nuggets()
    nugget = next((n for n in nuggets if n['id'] == video_id), None)

    if not nugget:
        return jsonify({"error": "Nugget no encontrado"}), 404

    puntos = nugget.get('puntos_clave', [])
    if len(puntos) < 2:
        return jsonify({"error": "Se necesitan al menos 2 puntos clave"}), 400

    # Obtener contexto
    idea_principal = nugget.get('idea_principal', '')
    transcript = nugget.get('transcript', '')[:3000]

    # Crear lista numerada de puntos
    puntos_texto = "\n".join([f"{i}. {p}" for i, p in enumerate(puntos)])

    prompt = f"""Analiza estos puntos clave de un video educativo y genera un mapa conceptual rico.

IDEA PRINCIPAL: {idea_principal}

PUNTOS CLAVE:
{puntos_texto}

CONTEXTO (transcripción):
{transcript}

Tu tarea: Genera un mapa conceptual que muestre las relaciones entre conceptos.

Responde SOLO con un JSON válido:
{{
  "nodes": [
    {{"id": 0, "label": "etiqueta corta (max 25 chars)", "tipo": "concepto|accion|herramienta", "importancia": 1}}
  ],
  "edges": [
    {{"from": 0, "to": 1, "label": "relación (max 20 chars)", "fuerza": 2}}
  ],
  "clusters": [
    {{"nombre": "grupo temático", "nodos": [0, 1]}}
  ]
}}

Reglas:
- tipo: "concepto" (ideas abstractas), "accion" (pasos/procesos), "herramienta" (software/recursos)
- importancia: 1 (normal), 2 (importante), 3 (central)
- fuerza: 1 (débil), 2 (moderada), 3 (fuerte)
- clusters: agrupa nodos relacionados temáticamente
- Solo relaciones significativas
- Responde SOLO el JSON"""

    # Detectar si usar Claude Code o Ollama
    use_claude = request.args.get('engine', 'claude') == 'claude'

    try:
        if use_claude:
            # Usar Claude Code CLI
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "json"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                raise Exception(f"Claude Code error: {result.stderr}")

            # Parsear respuesta de Claude Code
            claude_response = json.loads(result.stdout)
            response = claude_response.get("result", result.stdout)
        else:
            # Fallback a Ollama
            result = subprocess.run(
                ["ollama", "run", "llama3.2", prompt],
                capture_output=True, text=True, timeout=60
            )
            response = result.stdout.strip()

        # Extraer JSON de la respuesta
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            map_data = json.loads(json_match.group())
            # Añadir puntos completos para tooltip
            for node in map_data.get('nodes', []):
                idx = node.get('id', 0)
                if idx < len(puntos):
                    node['full'] = puntos[idx]
            return jsonify(map_data)
        else:
            return jsonify({"error": "No se pudo generar el mapa"}), 500

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Error parseando JSON: {str(e)}"}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout - el LLM tardó demasiado"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/expand', methods=['POST'])
def expand_point():
    """Expande un punto clave usando Ollama."""
    data = request.json
    video_id = data.get('video_id')
    punto = data.get('punto', '')

    if not punto:
        return jsonify({"error": "Punto requerido"}), 400

    # Obtener contexto de la transcripción
    nuggets = load_nuggets()
    nugget = next((n for n in nuggets if n['id'] == video_id), None)

    transcript = ""
    if nugget:
        transcript = nugget.get('transcript', '')[:4000]  # Limitar contexto

    prompt = f"""Eres un asistente educativo. El usuario está estudiando un video y quiere entender mejor este punto clave:

PUNTO A EXPANDIR:
{punto}

CONTEXTO DEL VIDEO:
{transcript if transcript else "No disponible"}

Tu tarea:
1. Explica este concepto de forma clara y detallada
2. Da un ejemplo práctico si es posible
3. Menciona por qué es importante

Responde en español, de forma concisa pero completa (máximo 3-4 párrafos)."""

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2", prompt],
            capture_output=True, text=True, timeout=60
        )
        expansion = result.stdout.strip()
        return jsonify({"expansion": expansion, "punto": punto})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout - Ollama tardó demasiado"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_server(port=None, host=None):
    port = port or SERVER_PORT
    host = host or SERVER_HOST
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           ⛏️  VideoMine - Compass Server                   ║
╠═══════════════════════════════════════════════════════════╣
║  🧭 http://{host}:{port:<5}                                ║
║  🏛️  Vault: ./vault/                                       ║
║                                                           ║
║  Metodología minerOS:                                     ║
║    🔦 Tunnel → ⛏️ Pickaxe → 💎 Gemcutter → 🏛️ Vault        ║
║                                                           ║
║  Ctrl+C para detener                                      ║
╚═══════════════════════════════════════════════════════════╝
""")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    run_server()
