# ⛏️ VideoMine

Extrae pepitas de conocimiento de videos de YouTube usando IA. Metodología **minerOS**.

## Filosofía minerOS

```
🔦 Tunnel      → Scanner (yt-dlp descubre el video)
⛏️  Pickaxe     → Extractor (subtítulos/Whisper)
💎 Gemcutter   → Clasificador (LLM resume y estructura)
🏛️  Vault       → Base de datos (nuggets.json + HTML)
🧭 Compass     → Interfaz web (Flask)
🗺️  Cartographer → Grafo de conocimiento (conexiones semánticas)
```

## Instalación

```bash
# Clonar e instalar dependencias
pip install -r requirements.txt

# Dependencias del sistema (macOS)
brew install ffmpeg  # Requerido por whisper
```

### Requisitos

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Descarga de videos/subtítulos
- [Ollama](https://ollama.ai) - LLM local (opcional, recomendado)
- [Claude Code CLI](https://claude.ai/code) - Alternativa con suscripción Pro/Max

## Uso Rápido

```bash
# ⛏️ Minar un video con Ollama (local, gratuito)
python videomine.py "https://youtube.com/watch?v=VIDEO_ID"

# 💎 Minar con Claude Code (usa tu suscripción)
python videomine.py "https://youtube.com/watch?v=VIDEO_ID" --claude-code

# 💎 Minar con Claude API (paga por tokens)
python videomine.py "https://youtube.com/watch?v=VIDEO_ID" --claude

# 📝 Modo manual (guarda transcripción para resumir después)
python videomine.py "https://youtube.com/watch?v=VIDEO_ID" --manual
```

### 🧭 Interfaz Web (Compass)

```bash
# Iniciar servidor web
python videomine.py --server

# O usar el launcher (macOS)
./VideoMine.command
```

Abre http://localhost:5555 para acceder al Vault.

## Estructura del Proyecto

```
videomine/
├── videomine.py       # CLI principal (pipeline minerOS)
├── compass.py         # 🧭 Configuración
├── pickaxe.py         # ⛏️ Utilidades de extracción
├── compass_server.py  # 🧭 Servidor Flask
├── tunnel/            # 🔦 Scanner (yt-dlp)
│   └── __init__.py
├── gemcutter/         # 💎 Clasificador (LLM)
│   └── __init__.py
├── cartographer/      # 🗺️ Grafo de conocimiento
│   ├── __init__.py
│   ├── extractor.py   # Extrae conceptos con Claude Code
│   └── graph.py       # KnowledgeGraph
├── vault/             # 🏛️ Base de datos
│   └── __init__.py
├── compass/           # 🧭 Interfaz web
│   └── templates/
│       ├── index.html
│       └── nugget.html
├── vault/             # Output de nuggets
│   ├── index.html
│   ├── nuggets.json
│   └── nugget_*.html
├── requirements.txt
├── mine               # Wrapper script
└── VideoMine.command  # Launcher macOS
```

## API / Comandos

### CLI

| Comando | Descripción |
|---------|-------------|
| `python videomine.py URL` | ⛏️ Minar video con Ollama |
| `python videomine.py URL --claude-code` | 💎 Usar Claude Code CLI |
| `python videomine.py URL --claude` | 💎 Usar Claude API |
| `python videomine.py URL --manual` | 📝 Guardar transcripción sin resumir |
| `python videomine.py --server` | 🧭 Iniciar Compass (servidor web) |
| `python videomine.py --delete VIDEO_ID` | 🗑️ Eliminar nugget |
| `python videomine.py --finish VIDEO_ID` | ✅ Completar nugget pendiente |
| `python videomine.py --map VIDEO_ID` | 🗺️ Extraer conceptos al grafo |
| `python videomine.py --rebuild-graph` | 🗺️ Reconstruir grafo completo |
| `python videomine.py --graph` | 🗺️ Abrir Knowledge Graph en navegador |

### API REST

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/videos` | GET | Listar todos los nuggets |
| `/api/add` | POST | Minar video `{url, motor}` |
| `/api/progress/<id>` | GET | Progreso de minería |
| `/api/delete/<id>` | DELETE | Eliminar nugget |
| `/api/search?q=` | GET | Buscar en el Vault |
| `/api/export/<id>` | GET | Exportar a Markdown |
| `/api/export-html/<id>` | GET | Exportar HTML imprimible con campos de notas |
| `/api/export-anki/<id>` | GET | Exportar flashcards Anki (TSV) |
| `/api/transcript/<id>` | GET | Obtener transcripción |
| `/api/translate` | POST | Traducir texto con Ollama |
| `/api/expand` | POST | Expandir punto clave con IA `{video_id, punto}` |
| `/api/concept-map/<id>` | GET | Generar mapa conceptual con Claude Code |
| `/api/cartographer/graph` | GET | Obtener grafo de conocimiento (D3.js) |
| `/api/cartographer/rebuild` | POST | Reconstruir grafo completo |
| `/api/cartographer/extract/<id>` | POST | Extraer conceptos de un video |
| `/api/cartographer/concept/<name>` | GET | Info de un concepto |
| `/api/cartographer/related/<id>` | GET | Videos relacionados |
| `/vault/graph` | GET | Vista interactiva del Knowledge Graph |

## Configuración

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `VIDEOMINE_MODEL` | `llama3.2` | Modelo de Ollama |
| `VIDEOMINE_MAX_CHARS` | `12000` | Máx. caracteres de transcripción |
| `VIDEOMINE_TIMEOUT` | `300` | Timeout LLM en segundos |
| `VIDEOMINE_HOST` | `127.0.0.1` | Host del servidor |
| `VIDEOMINE_PORT` | `5555` | Puerto del servidor |

### Ejemplo

```bash
export VIDEOMINE_MODEL="mistral"
export VIDEOMINE_PORT="8080"
python videomine.py --server
```

## Pipeline minerOS

1. **🔦 Tunnel** - yt-dlp extrae metadatos del video
2. **⛏️ Pickaxe** - Busca subtítulos o usa Whisper
3. **💎 Gemcutter** - LLM genera resumen estructurado (JSON)
4. **🏛️ Vault** - Jinja2 genera HTML, guarda en DB
5. **🧭 Compass** - Actualiza índice web
6. **🗺️ Cartographer** - Extrae conceptos y construye grafo de conocimiento

## Knowledge Graph (Cartographer)

Sistema de conexión semántica entre videos estilo Obsidian:

- **Grafo por conceptos**: Cada concepto es un nodo, los videos son fuentes
- **Extracción automática**: Claude Code extrae conceptos de cada nugget
- **Unificación de sinónimos**: "Python 3" = "python" = "py"
- **Visualización D3.js**: Force-directed graph interactivo
- **Panel lateral**: Click en nodo muestra videos fuente y conceptos relacionados

```bash
# Construir grafo desde todos los nuggets
python videomine.py --rebuild-graph

# Abrir visualización
python videomine.py --graph
```

## Estructura de un Nugget

Cada nugget incluye:
- 💎 Idea principal
- 📋 Puntos clave (con botón "Explícame más" para expandir con IA)
- 🗺️ Mapa conceptual interactivo (genera relaciones entre conceptos)
- 🛠️ Código y comandos
- 📚 Recursos mencionados
- ❓ Preguntas para profundizar
- 📖 Glosario de términos

### Funciones Interactivas

- **Explícame más**: Click en "+ más" junto a cualquier punto clave para obtener una explicación detallada con Ollama
- **Mapa Conceptual**: Visualización SVG de relaciones entre puntos clave, generada con Claude Code CLI
  - Nodos coloreados por tipo (concepto/acción/herramienta)
  - Tamaño según importancia
  - Conexiones con grosor según fuerza de relación
  - Agrupación por clusters temáticos

## Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `ESC` | Cerrar mapa conceptual |
| `Enter` | Buscar (en campo de búsqueda) |

## Licencia

MIT

---

> **"Piano piano se arriva lontano"** - minerOS
