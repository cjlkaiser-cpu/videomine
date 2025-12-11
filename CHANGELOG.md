# Changelog

Todos los cambios notables en VideoMine.

## [0.3.0] - 2024-12-11 "Cartographer"

### Nuevas Funciones

- **Knowledge Graph**: Sistema de conexion semantica entre videos estilo Obsidian
  - Grafo por conceptos (no por videos) - cada concepto es un nodo
  - Extraccion automatica de conceptos con Claude Code CLI
  - Unificacion de sinonimos ("Python 3" = "python" = "py")
  - Visualizacion D3.js force-directed interactiva
  - Nodos coloreados por tipo (lenguaje/libreria/herramienta/concepto/metodologia)
  - Tamaño de nodos segun cantidad de videos que lo mencionan
  - Panel lateral con info del concepto y videos fuente
  - Busqueda de conceptos en tiempo real
  - Videos relacionados por conceptos compartidos

- **Nuevo modulo `cartographer/`**:
  - `extractor.py`: Extrae conceptos de nuggets usando Claude Code
  - `graph.py`: KnowledgeGraph con persistencia JSON
  - `__init__.py`: API publica del modulo

- **Nuevos endpoints API**:
  - `GET /api/cartographer/graph` - Grafo en formato D3.js
  - `POST /api/cartographer/rebuild` - Reconstruir grafo completo
  - `POST /api/cartographer/extract/<id>` - Extraer conceptos de un video
  - `GET /api/cartographer/concept/<name>` - Info de un concepto
  - `GET /api/cartographer/related/<id>` - Videos relacionados
  - `GET /vault/graph` - Vista HTML del grafo

- **Nuevos comandos CLI**:
  - `--map ID`: Extraer conceptos de un video al grafo
  - `--rebuild-graph`: Reconstruir grafo completo desde todos los nuggets
  - `--graph`: Abrir vista del grafo en navegador

### Mejoras

- Link "Knowledge Graph" en header del Vault
- Leyenda de colores en vista del grafo

---

## [0.2.0] - 2024-12-11

### Nuevas Funciones

- **Mapa Conceptual Interactivo**: Visualiza relaciones entre puntos clave
  - Generado con Claude Code CLI para mayor calidad
  - Nodos coloreados por tipo (concepto/accion/herramienta)
  - Tamaño de nodos segun importancia
  - Grosor de conexiones segun fuerza de relacion
  - Agrupacion visual por clusters tematicos
  - Modal a pantalla completa con overlay
  - Cierra con ESC o click fuera

- **Explicame mas**: Boton junto a cada punto clave
  - Expande el concepto usando Ollama
  - Cache en localStorage para evitar llamadas repetidas
  - Estilo acordeon integrado

- **Exportar HTML imprimible**: Reemplaza exportacion Obsidian
  - Casillas de verificacion para puntos clave
  - Campos de texto para respuestas
  - Seccion de notas personales
  - Boton de impresion integrado
  - Diseno optimizado para impresion

### Mejoras

- Descarga directa de archivos (MD, HTML, Anki) sin cuarentena de macOS
- Mejoras de estilo en el template de nuggets
- Cache de mapas conceptuales en localStorage

### Correciones

- Archivos descargados ya no son bloqueados por Gatekeeper de macOS
- Eliminado endpoint obsoleto `/api/export-obsidian`

## [0.1.0] - 2024-12-01

### Funciones Iniciales

- Pipeline minerOS completo (Tunnel -> Pickaxe -> Gemcutter -> Vault -> Compass)
- Soporte para Ollama, Claude Code CLI y Claude API
- Modo manual para edicion de resumenes
- Interfaz web Compass con busqueda
- Exportacion a Markdown y Anki
- Traduccion de transcripciones con Ollama
