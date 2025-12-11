#!/usr/bin/env python3
"""
⛏️ VideoMine - Extrae pepitas de conocimiento de videos
Uso: python videomine.py "URL_DEL_VIDEO" [--claude]

Metodología minerOS:
🔦 Tunnel    → yt-dlp (escanea el video)
⛏️  Pickaxe   → Subtítulos/Whisper (extrae transcripción)
💎 Gemcutter → LLM (clasifica, resume, estructura)
🏛️  Vault     → nuggets.json + *.html (almacenamiento)
🧭 Compass   → server.py (interfaz web)
"""

import sys
import os

# Agregar PATHs de usuario para yt-dlp y claude
os.environ["PATH"] = ":".join([
    os.path.expanduser("~/Library/Python/3.9/bin"),  # yt-dlp
    os.path.expanduser("~/.npm-global/bin"),          # claude CLI
    os.environ.get("PATH", "")
])

import json
from pathlib import Path
from datetime import datetime

# Importar módulos minerOS
from compass import OUTPUT_DIR, PENDING_DIR
from pickaxe import get_safe_filename
from tunnel import scan_video, extract_subtitles, transcribe_audio
from gemcutter import cut_with_ollama, cut_with_claude, cut_with_claude_code, parse_nugget
from vault import load_nuggets, save_nugget, forge_html, forge_index, delete_nugget

# Flags de línea de comandos
USE_CLAUDE = "--claude" in sys.argv
USE_CLAUDE_CODE = "--claude-code" in sys.argv
USE_MANUAL = "--manual" in sys.argv


def finish_nugget(video_id: str):
    """Completa un nugget pendiente con resumen desde stdin."""
    transcript_file = PENDING_DIR / f"{video_id}.txt"
    info_file = PENDING_DIR / f"{video_id}.json"

    if not transcript_file.exists():
        print(f"❌ No hay video pendiente con ID: {video_id}")
        print(f"   Videos pendientes: {list(PENDING_DIR.glob('*.txt'))}")
        return None

    video_info = json.loads(info_file.read_text())

    print(f"📝 Completando: {video_info['title']}")
    print("\nPega el JSON del resumen (termina con línea vacía):")

    lines = []
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass

    if not lines:
        print("❌ No se recibió resumen")
        return None

    summary = parse_nugget("\n".join(lines))

    # Generar HTML
    html = forge_html(video_info, summary)

    # Guardar
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / get_safe_filename(video_info['title'], video_id)
    output_file.write_text(html)

    # Actualizar índice
    nuggets = save_nugget(video_info, summary, output_file.name)
    forge_index(nuggets)

    # Limpiar pendientes
    transcript_file.unlink()
    info_file.unlink()

    print(f"\n✅ ¡Listo! {output_file}")
    return output_file


def dig(url: str):
    """
    Proceso principal de minería de un video.

    Args:
        url: URL del video de YouTube
    """
    print("⛏️  VideoMine - Extrayendo pepitas de conocimiento...")
    if USE_MANUAL:
        motor = "Manual (Claude Code)"
    elif USE_CLAUDE_CODE:
        motor = "Claude Code (suscripción)"
    elif USE_CLAUDE:
        motor = "Claude API (tokens)"
    else:
        motor = "Ollama (local)"
    print(f"   Motor: {motor}")

    # 1. TUNNEL: Escanear video
    print("\n🔦 [Tunnel] Escaneando video...")
    video_info = scan_video(url)
    video_id = video_info['id']
    print(f"   Título: {video_info['title']}")
    print(f"   Canal: {video_info.get('channel', 'N/A')}")

    # 2. PICKAXE: Extraer transcripción
    print("\n⛏️  [Pickaxe] Extrayendo transcripción...")
    transcript = extract_subtitles(url, video_id)

    if transcript:
        print(f"   ✅ Subtítulos encontrados ({len(transcript)} caracteres)")
    else:
        print("   ⚠️  No hay subtítulos, usando Whisper...")
        transcript = transcribe_audio(url, video_id)

    # 3. GEMCUTTER: Resumir con LLM
    if USE_MANUAL:
        # Modo manual: guardar transcripción y esperar JSON
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        transcript_file = PENDING_DIR / f"{video_id}.txt"
        info_file = PENDING_DIR / f"{video_id}.json"

        transcript_file.write_text(transcript)
        info_file.write_text(json.dumps(video_info, indent=2, ensure_ascii=False))

        print(f"\n📄 Transcripción guardada en: {transcript_file}")
        print(f"\n{'='*60}")
        print("MODO MANUAL - Pide a Claude que resuma esta transcripción")
        print("="*60)
        print(f"\nDile a Claude:")
        print(f"  'Resume el video {video_id}' o")
        print(f"  'Lee {transcript_file} y genera el resumen'")
        print(f"\nLuego ejecuta:")
        print(f"  python videomine.py --finish {video_id}")
        print(f"\nO pega el JSON del resumen ahora (termina con línea vacía):")

        # Leer JSON del stdin
        lines = []
        try:
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
        except EOFError:
            pass

        if lines:
            summary = parse_nugget("\n".join(lines))
        else:
            print("\n⏸️  Transcripción guardada. Usa --finish cuando tengas el resumen.")
            return None
    else:
        print("\n💎 [Gemcutter] Puliendo nugget...")
        if USE_CLAUDE_CODE:
            summary = cut_with_claude_code(transcript, video_info)
        elif USE_CLAUDE:
            summary = cut_with_claude(transcript, video_info)
        else:
            summary = cut_with_ollama(transcript, video_info)

    # 4. VAULT: Almacenar nugget
    print("\n🏛️  [Vault] Almacenando nugget...")
    html = forge_html(video_info, summary)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / get_safe_filename(video_info['title'], video_id)
    output_file.write_text(html)

    # 5. Actualizar índice
    print("📚 Actualizando índice...")
    nuggets = save_nugget(video_info, summary, output_file.name)
    forge_index(nuggets)

    print(f"\n✅ ¡Nugget extraído! Guardado en:")
    print(f"   {output_file}")
    print(f"\n   Abrir vault: open '{OUTPUT_DIR / 'index.html'}'")

    return output_file


def main():
    # Comando --server
    if "--server" in sys.argv:
        from compass_server import run_server
        run_server(port=5555)
        return

    # Comando --delete
    if "--delete" in sys.argv:
        idx = sys.argv.index("--delete")
        if idx + 1 < len(sys.argv):
            delete_nugget(sys.argv[idx + 1])
            return
        else:
            print("Uso: --delete VIDEO_ID")
            return

    # Comando --finish
    if "--finish" in sys.argv:
        idx = sys.argv.index("--finish")
        if idx + 1 < len(sys.argv):
            finish_nugget(sys.argv[idx + 1])
            return
        else:
            print("Uso: --finish VIDEO_ID")
            return

    # Comando --map (extraer conceptos de un video)
    if "--map" in sys.argv:
        import cartographer
        idx = sys.argv.index("--map")
        if idx + 1 < len(sys.argv):
            video_id = sys.argv[idx + 1]
            print(f"🗺️  Mapeando conceptos de {video_id}...")
            try:
                extraction = cartographer.map_video(video_id)
                print(f"   ✅ {len(extraction['concepts'])} conceptos extraídos")
                print(f"   ✅ {len(extraction['relations'])} relaciones")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            return
        else:
            print("Uso: --map VIDEO_ID")
            return

    # Comando --rebuild-graph (reconstruir grafo completo)
    if "--rebuild-graph" in sys.argv:
        import cartographer
        print("🗺️  Reconstruyendo grafo de conocimiento...")
        try:
            stats = cartographer.rebuild()
            print(f"   ✅ {stats['concepts']} conceptos")
            print(f"   ✅ {stats['relations']} relaciones")
            print(f"   ✅ {stats['videos']} videos procesados")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        return

    # Comando --graph (abrir grafo en navegador)
    if "--graph" in sys.argv:
        import webbrowser
        url = f"http://localhost:5555/vault/graph"
        print(f"🗺️  Abriendo grafo: {url}")
        webbrowser.open(url)
        return

    # Filtrar argumentos
    args = [a for a in sys.argv[1:] if not a.startswith('--')]

    if len(args) < 1:
        print("""
⛏️  VideoMine - Extrae pepitas de conocimiento de videos

Metodología minerOS:
  🔦 Tunnel    → Escanea el video (yt-dlp)
  ⛏️  Pickaxe   → Extrae transcripción (subtítulos/Whisper)
  💎 Gemcutter → Pule nugget (LLM resume y estructura)
  🏛️  Vault     → Almacena nugget (HTML + JSON)
  🧭 Compass   → Interfaz web (Flask)

Uso: python videomine.py URL [opciones]

Opciones:
  --claude-code     Usar Claude Code CLI (tu suscripción Pro/Max)
  --claude          Usar Claude API (requiere ANTHROPIC_API_KEY, paga tokens)
  --manual          Guarda transcripción para resumir manualmente
  --finish ID       Completar video pendiente con resumen JSON
  --delete ID       Eliminar nugget del vault
  --server          Iniciar interfaz web (Compass)
  --map ID          Extraer conceptos de un video al grafo
  --rebuild-graph   Reconstruir grafo completo desde todos los nuggets
  --graph           Abrir vista del grafo en navegador

Ejemplos:
  python videomine.py 'URL'                   # Usa Ollama (local)
  python videomine.py 'URL' --claude-code     # Usa tu suscripción
  python videomine.py 'URL' --claude          # Usa API (tokens)
  python videomine.py --server                # Abre el Vault web
  python videomine.py --delete abc123
""")
        sys.exit(1)

    url = args[0]
    dig(url)


if __name__ == "__main__":
    main()
