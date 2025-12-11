# Changelog

Todos los cambios notables en VideoMine.

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
