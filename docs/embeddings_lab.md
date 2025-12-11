# 🧪 Laboratorio de Embeddings

Experimenta con embeddings usando `nomic-embed-text` antes de integrarlo en Cartographer.

## Setup (5 minutos)

```bash
# 1. Instalar el modelo de embeddings (270MB)
ollama pull nomic-embed-text

# 2. Instalar dependencias Python (opcional, solo para CLI)
pip install scikit-learn matplotlib

# 3. Verificar que funciona
ollama embeddings -m nomic-embed-text -p "test"
```

## Uso

### Interfaz Web (recomendado)

```bash
# Iniciar servidor
python videomine.py --server

# Abrir en navegador
open http://localhost:5555/lab
```

### CLI (para debugging)

```bash
# Ejecutar el laboratorio completo
cd cartographer
python embeddings_lab.py
```

## Qué hace

El laboratorio ejecuta 6 experimentos:

### 1️⃣ Verificación del modelo
Comprueba que `nomic-embed-text` está instalado y funcionando.

### 2️⃣ Carga de conceptos
Extrae conceptos de tus nuggets existentes (o usa ejemplos si no hay).

### 3️⃣ Similitudes
Calcula qué conceptos son similares automáticamente:
```
🔥 Flask      ↔ FastAPI     : 0.823 (MUY ALTA)
📊 pandas     ↔ numpy       : 0.715 (ALTA)
📌 Docker     ↔ Kubernetes  : 0.567 (MEDIA)
```

### 4️⃣ Búsqueda semántica
Encuentra conceptos relacionados sin usar palabras exactas:
```
Query: "crear servidor web"
  1. 🎯 Flask       : 0.782 ████████████████
  2. 🎯 FastAPI     : 0.769 ███████████████
  3. ✅ Django      : 0.654 █████████████
```

### 5️⃣ Clustering automático
Agrupa conceptos por temática:
```
📦 Cluster 1: Python, Flask, FastAPI, Django
📦 Cluster 2: Docker, Kubernetes, Nginx
📦 Cluster 3: React, Vue, JavaScript
```

### 6️⃣ Visualización 2D
Genera un gráfico que muestra las relaciones espacialmente:
- Conceptos cercanos = similares
- Conceptos lejanos = diferentes

## Interfaz Web

La UI incluye 4 secciones interactivas:

### 🔍 Búsqueda Semántica
- Escribe una query como "crear servidor web"
- Ve resultados con barras de similitud animadas
- No necesitas palabras exactas, busca por significado

### 🎮 Quiz de Similitud
- Mini-juego para entender embeddings
- "¿Qué concepto es más similar a X?"
- Confetti al acertar

### ⚖️ Comparador de Similitud
- Selecciona dos conceptos
- Ve la similitud en tiempo real
- Medidor visual de 0 a 1

### 📊 Mapa de Conceptos 2D
- Visualización espacial
- Conceptos cercanos = similares
- Colores por cluster

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/lab` | GET | Página del laboratorio |
| `/api/lab/concepts` | GET | Lista de conceptos |
| `/api/lab/search` | POST | Búsqueda semántica |
| `/api/lab/similarity` | POST | Similitud entre dos conceptos |
| `/api/lab/quiz` | GET | Nueva pregunta quiz |
| `/api/lab/quiz/check` | POST | Verificar respuesta |
| `/api/lab/visualization` | GET | Datos para gráfico 2D |

## Output esperado (CLI)

```
============================================================
🧪 LABORATORIO DE EMBEDDINGS - VideoMine
============================================================

1️⃣ Verificando nomic-embed-text...
   ✅ Modelo funcionando (768 dimensiones)

2️⃣ Cargando conceptos...
   ✅ 17 conceptos listos
   📝 Python, Flask, FastAPI, Django, JavaScript...

3️⃣ Búsqueda semántica...
   Query: "crear servidor web"
   🎯 Flask           0.782 ████████████████████
   🎯 FastAPI         0.769 ███████████████████
   ✅ Django          0.654 █████████████

4️⃣ Similitudes...
   🔥 Python       ↔ Flask        : 0.823
   🔥 Docker       ↔ Kubernetes   : 0.689

5️⃣ Quiz de similitud...
   ¿Cuál es más similar a "Python"?
   ✓ 1. Flask
     2. React
     3. Docker
     4. Kubernetes

6️⃣ Datos para visualización 2D...
   ✅ 17 puntos generados
   📦 3 clusters detectados

============================================================
✅ LABORATORIO LISTO
============================================================
```

## Troubleshooting

**Error: "ollama: command not found"**
```bash
# Instala Ollama
brew install ollama  # macOS
```

**Error: "Model 'nomic-embed-text' not found"**
```bash
ollama pull nomic-embed-text
```

**La búsqueda tarda mucho**
- La primera búsqueda genera embeddings (lento)
- Búsquedas posteriores usan cache (rápido)

**No aparecen conceptos**
- Primero necesitas minar algunos videos
- O usa los conceptos de ejemplo

## Próximos pasos

Una vez entiendas cómo funcionan los embeddings:

1. **Fase 1**: Integrar embeddings en el grafo de Cartographer
2. **Fase 2**: Búsqueda semántica global en el Vault
3. **Fase 3**: Detección de lagunas de conocimiento
4. **Fase 4**: Recomendaciones de videos relacionados

---

> "Piano piano se arriva lontano" - minerOS
