#!/usr/bin/env python3
"""
🔦 VideoMine - Tunnel
Scanner para descubrir y obtener información de videos.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from pickaxe import clean_vtt


def scan_video(url: str) -> dict:
    """
    Escanea un video de YouTube y obtiene sus metadatos.

    Args:
        url: URL del video de YouTube

    Returns:
        dict con metadatos del video (id, title, channel, duration, etc.)
    """
    cmd = ["yt-dlp", "--dump-json", "--no-download", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error escaneando video: {result.stderr}")
    return json.loads(result.stdout)


def extract_subtitles(url: str, video_id: str) -> Optional[str]:
    """
    Intenta extraer subtítulos existentes del video.

    Args:
        url: URL del video
        video_id: ID del video

    Returns:
        Texto de subtítulos o None si no hay disponibles
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Intentar subtítulos en español, luego inglés, luego auto-generados
        for lang in ["es", "en", "es-auto", "en-auto"]:
            is_auto = "-auto" in lang
            base_lang = lang.replace("-auto", "")

            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-sub" if not is_auto else "--write-auto-sub",
                "--sub-lang", base_lang,
                "--sub-format", "vtt",
                "-o", f"{tmpdir}/{video_id}.%(ext)s",
                url
            ]

            subprocess.run(cmd, capture_output=True)

            # Buscar archivo de subtítulos generado
            for f in Path(tmpdir).glob(f"{video_id}*.vtt"):
                content = f.read_text()
                return clean_vtt(content)

    return None


def transcribe_audio(url: str, video_id: str) -> str:
    """
    Descarga audio y transcribe con Whisper.

    Args:
        url: URL del video
        video_id: ID del video

    Returns:
        Texto transcrito
    """
    import whisper

    print("  ⏳ Descargando audio...")
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = f"{tmpdir}/{video_id}.mp3"
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", audio_path,
            url
        ]
        subprocess.run(cmd, capture_output=True)

        print("  ⏳ Transcribiendo con Whisper (puede tardar)...")
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]
