# Roadmap - VideoMine

Mejoras planificadas para VideoMine.

## Fase 4: Cartographer - Grafo de Conocimiento (Completada v0.3.0)

Sistema de conexión semántica entre videos, estilo Obsidian. Grafo por **conceptos** donde cada nodo es un concepto y los videos son fuentes que lo alimentan.

### Visión

```
        ┌─────────┐
        │ Python  │◄────── Video A, Video C, Video F
        └────┬────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌───────┐ ┌─────┐ ┌──────┐
│Pandas │ │Flask│ │Django│
└───┬───┘ └──┬──┘ └──┬───┘
    │        │       │
    ▼        ▼       ▼
┌──────────────────────┐
│   Machine Learning   │◄────── Video B, Video D
└──────────────────────┘
```

### Arquitectura

```
cartographer/
├── __init__.py         # Orquestador principal
├── extractor.py        # Extrae conceptos de nuggets (Claude Code)
├── graph.py            # Gestiona grafo NetworkX
├── similarity.py       # Calcula relaciones entre conceptos
└── data/
    ├── concepts.json   # Conceptos extraídos por video
    ├── graph.json      # Grafo completo (nodos + aristas)
    └── clusters.json   # Agrupaciones temáticas
```

### Flujo de trabajo

#### Fase 1: Extracción (al minar o batch)

```
Nugget ──► Claude Code ──► Lista de conceptos + relaciones

Prompt: "Extrae conceptos clave y sus relaciones jerárquicas"

Output:
{
  "concepts": [
    {"name": "Python", "type": "lenguaje", "importance": 1.0},
    {"name": "Pandas", "type": "libreria", "parent": "Python"},
    {"name": "DataFrame", "type": "concepto", "parent": "Pandas"}
  ],
  "relations": [
    {"from": "Pandas", "to": "Machine Learning", "type": "usado_en"}
  ]
}
```

#### Fase 2: Unificación

```
Problema: "Python" vs "python" vs "Python 3"

Solución: Claude Code normaliza y agrupa sinónimos

{
  "canonical": "Python",
  "aliases": ["python", "Python 3", "Python3", "py"],
  "sources": ["VIDEO_A", "VIDEO_C", "VIDEO_F"]
}
```

#### Fase 3: Grafo

- **Nodos**: Conceptos (tamaño = # de videos que lo mencionan)
- **Color por tipo**: lenguaje / librería / concepto / herramienta
- **Aristas jerárquicas** (parent-child): línea sólida
- **Aristas semánticas** (relacionado): línea punteada
- **Grosor** = fuerza de relación

#### Fase 4: Visualización (/vault/graph)

- Búsqueda de conceptos
- Filtro por tipo
- Click en nodo → Panel lateral con:
  - Definición del concepto
  - Videos que lo mencionan (links)
  - Conceptos relacionados

### Endpoints nuevos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/cartographer/extract/<id>` | POST | Extraer conceptos de un nugget |
| `/api/cartographer/rebuild` | POST | Reconstruir grafo completo |
| `/api/cartographer/graph` | GET | Obtener grafo JSON |
| `/api/cartographer/concept/<name>` | GET | Info de un concepto |
| `/vault/graph` | GET | Vista HTML del grafo |

### Comandos CLI nuevos

```bash
# Extraer conceptos de un video específico
python videomine.py --map VIDEO_ID

# Reconstruir grafo completo (todos los nuggets)
python videomine.py --rebuild-graph

# Abrir vista de grafo en navegador
python videomine.py --graph
```

### Fases de implementación

| Fase | Descripción | Dependencias |
|------|-------------|--------------|
| **4.1** | ~~Crear `cartographer/extractor.py` - Extracción con Claude Code~~ | ✅ |
| **4.2** | ~~Crear `cartographer/graph.py` - Gestión del grafo~~ | ✅ |
| **4.3** | ~~Endpoint `/api/cartographer/graph`~~ | ✅ |
| **4.4** | ~~Template `vault/graph.html` con D3.js~~ | ✅ |
| **4.5** | ~~Integrar en pipeline de minería~~ | ✅ |
| **4.6** | Panel lateral en nugget.html (relacionados) | Pendiente |

### Tecnologías

- **Extracción semántica**: Claude Code CLI
- **Grafo**: NetworkX + JSON
- **Visualización**: D3.js force-directed
- **Almacenamiento**: JSON (concepts.json, graph.json)

---

## Fase 3: Profundizar con IA (Pendiente)

Boton que genera una ficha de estudio completa para un punto clave:

### Estructura de la ficha
```json
{
  "definicion": "Explicacion clara del concepto",
  "ejemplo_practico": "Caso de uso concreto",
  "recursos": ["enlaces", "libros", "videos relacionados"],
  "preguntas": ["preguntas para autoevaluacion"],
  "conexiones": ["conceptos relacionados del video"]
}
```

### Implementacion propuesta
1. Endpoint `/api/deep-dive` (POST)
   - Recibe: `video_id`, `punto`
   - Usa Claude Code CLI para generar ficha estructurada
   - Devuelve JSON con los 5 campos

2. UI en nugget.html
   - Boton "Profundizar" junto a cada punto
   - Modal con la ficha formateada
   - Opcion de exportar ficha como PDF

---

## Otras Mejoras Futuras

### Interactividad
- [ ] Quiz autogenerado desde puntos clave
- [ ] Flashcards interactivas en la UI (no solo exportar a Anki)
- [ ] Modo repaso espaciado (spaced repetition)

### Mapa Conceptual
- [ ] Drag & drop para reorganizar nodos
- [ ] Zoom y pan en el mapa
- [ ] Exportar mapa como imagen PNG/SVG
- [ ] Guardar layout personalizado

### Transcripcion
- [ ] Timestamps clickeables que abren el video en ese momento
- [ ] Resaltado de terminos del glosario en la transcripcion
- [ ] Busqueda dentro de la transcripcion

### Organizacion
- [ ] Tags/categorias para nuggets
- [ ] Colecciones/playlists de nuggets
- [ ] Estadisticas de estudio (tiempo, nuggets revisados)

### Exportacion
- [ ] Exportar a Notion
- [ ] Exportar a Roam Research
- [ ] Exportar a PDF con formato profesional

### Integraciones
- [ ] Sync con Obsidian vault
- [ ] Plugin para navegador (Chrome/Firefox)
- [ ] API publica documentada

---

## Ideas Descartadas

- **Niveles de profundidad**: Descartado por complejidad. El boton "Explicame mas" cumple funcion similar de forma mas simple.

---

> Ultima actualizacion: 2024-12-11 (v0.3.0 Cartographer)
