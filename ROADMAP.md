# Roadmap - VideoMine

Mejoras planificadas para VideoMine.

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

> Ultima actualizacion: 2024-12-11
