# ⛏️ VideoMine

> Extrae pepitas de conocimiento de videos de YouTube usando IA.

## Stack

- **Backend**: Python 3.9 + Flask
- **LLM**: Ollama (local) / Claude Code / Claude API
- **Transcripción**: yt-dlp + Whisper
- **DB**: JSON (nuggets.json)
- **Templates**: Jinja2

## Metodología minerOS

```
🔦 Tunnel    → tunnel/__init__.py    (yt-dlp escanea video)
⛏️  Pickaxe   → pickaxe.py           (extrae transcripción)
💎 Gemcutter → gemcutter/__init__.py (LLM resume y estructura)
🏛️  Vault     → vault/__init__.py    (almacena nuggets)
🧭 Compass   → compass_server.py     (interfaz web Flask)
```

## Estructura

```
videomine/
├── videomine.py          # CLI principal
├── compass.py            # Configuración
├── compass_server.py     # Servidor Flask (API REST)
├── pickaxe.py            # Utilidades
├── tunnel/               # Scanner
├── gemcutter/            # Clasificador LLM
├── vault/                # DB + nuggets HTML
│   ├── nuggets.json
│   └── *.html
├── compass/templates/    # Templates Jinja2
│   ├── index.html        # Índice del vault
│   └── nugget.html       # Template de nugget (con mapa conceptual)
├── mine                  # Wrapper script
├── VideoMine.command     # Launcher macOS
├── CHANGELOG.md          # Historial de cambios
└── ROADMAP.md            # Mejoras pendientes
```

## Convenciones

- **Idioma código**: Inglés (nombres funciones/variables)
- **Idioma UI/docs**: Español
- **Nombres archivos**: snake_case
- **Vocabulario**: Usar terminología minerOS (nugget, vault, tunnel, pickaxe, gemcutter, compass)

## Comandos útiles

```bash
# Iniciar servidor web
python videomine.py --server

# Minar video con Ollama
python videomine.py "URL"

# Minar con Claude Code
python videomine.py "URL" --claude-code

# Eliminar nugget
python videomine.py --delete VIDEO_ID
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `VIDEOMINE_MODEL` | `llama3.2` | Modelo Ollama |
| `VIDEOMINE_PORT` | `5555` | Puerto servidor |
| `VIDEOMINE_TIMEOUT` | `300` | Timeout LLM (seg) |

## Reglas

1. Mantener vocabulario minerOS consistente
2. Los "videos" son "nuggets" (pepitas de conocimiento)
3. Color principal: dorado (#ffa500)
4. Modularidad: cada módulo tiene responsabilidad única
5. Local primero: Ollama por defecto, Claude como alternativa

## Endpoints Interactivos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/expand` | POST | Expandir punto clave con Ollama |
| `/api/concept-map/<id>` | GET | Mapa conceptual con Claude Code CLI |
| `/api/export-html/<id>` | GET | HTML imprimible con campos de notas |

## Contexto

Parte del ecosistema minerOS de Carlos:
- PhotoMine (fotos)
- DocMine (documentos)
- DocMine-Fiscal (fiscalidad)
- **VideoMine** (videos)
