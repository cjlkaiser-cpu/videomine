"""
🧪 Laboratorio de Embeddings - VideoMine

Experimenta con embeddings semánticos usando nomic-embed-text.
Funciones para búsqueda, similitud, clustering y visualización.
"""

import json
import subprocess
import random
import urllib.request
from pathlib import Path
from typing import Optional

# Rutas
CARTOGRAPHER_DIR = Path(__file__).parent
DATA_DIR = CARTOGRAPHER_DIR / "data"
GRAPH_FILE = DATA_DIR / "graph.json"

# Configuración
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMS = 768
OLLAMA_API = "http://localhost:11434/api/embeddings"

# Cache de embeddings para evitar llamadas repetidas
_embeddings_cache: dict = {}


def verify_model() -> dict:
    """Verifica que nomic-embed-text esté instalado."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10
        )
        installed = EMBEDDING_MODEL in result.stdout

        if installed:
            # Verificar que funciona
            test = get_embedding("test")
            if test:
                return {
                    "status": "ok",
                    "model": EMBEDDING_MODEL,
                    "dimensions": len(test)
                }

        return {
            "status": "not_installed",
            "model": EMBEDDING_MODEL,
            "install_command": f"ollama pull {EMBEDDING_MODEL}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_embedding(text: str) -> Optional[list]:
    """Genera embedding para un texto usando Ollama API HTTP."""
    # Check cache
    if text in _embeddings_cache:
        return _embeddings_cache[text]

    try:
        # Usar API HTTP de Ollama (no hay comando CLI para embeddings)
        data = json.dumps({
            "model": EMBEDDING_MODEL,
            "prompt": text
        }).encode('utf-8')

        req = urllib.request.Request(
            OLLAMA_API,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            embedding = result.get("embedding", [])

            if embedding:
                # Cache it
                _embeddings_cache[text] = embedding
                return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")

    return None


def load_concepts() -> list:
    """Carga conceptos del grafo existente o usa ejemplos."""
    if GRAPH_FILE.exists():
        with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
            graph = json.load(f)

            # El grafo usa "concepts" (diccionario) no "nodes" (array)
            concepts_dict = graph.get("concepts", {})
            if concepts_dict:
                return list(concepts_dict.keys())

            # Fallback a formato nodes (por si acaso)
            nodes = graph.get("nodes", [])
            if nodes:
                return [node.get("id", node.get("name", "")) for node in nodes]

    # Conceptos de ejemplo si no hay grafo
    return [
        "Python", "JavaScript", "Flask", "FastAPI", "Django",
        "React", "Vue", "Docker", "Kubernetes", "PostgreSQL",
        "Machine Learning", "Neural Networks", "APIs", "REST",
        "Git", "Linux", "AWS", "Microservices"
    ]


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Calcula similitud coseno entre dos vectores."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def compute_similarity(concept_a: str, concept_b: str) -> dict:
    """Calcula similitud entre dos conceptos."""
    emb_a = get_embedding(concept_a)
    emb_b = get_embedding(concept_b)

    if not emb_a or not emb_b:
        return {"error": "No se pudo generar embedding"}

    similarity = cosine_similarity(emb_a, emb_b)

    # Clasificar nivel
    if similarity >= 0.8:
        level = "muy_alta"
        emoji = "🔥"
    elif similarity >= 0.6:
        level = "alta"
        emoji = "📊"
    elif similarity >= 0.4:
        level = "media"
        emoji = "📌"
    else:
        level = "baja"
        emoji = "📎"

    return {
        "concept_a": concept_a,
        "concept_b": concept_b,
        "similarity": round(similarity, 3),
        "level": level,
        "emoji": emoji
    }


def semantic_search(query: str, concepts: list = None, top_k: int = 5) -> list:
    """Búsqueda semántica: encuentra conceptos similares a una query."""
    if concepts is None:
        concepts = load_concepts()

    query_emb = get_embedding(query)
    if not query_emb:
        return []

    results = []
    for concept in concepts:
        concept_emb = get_embedding(concept)
        if concept_emb:
            sim = cosine_similarity(query_emb, concept_emb)
            results.append({
                "concept": concept,
                "similarity": round(sim, 3),
                "bar_width": int(sim * 100)
            })

    # Ordenar por similitud descendente
    results.sort(key=lambda x: x["similarity"], reverse=True)

    # Añadir emojis según posición
    for i, r in enumerate(results[:top_k]):
        if i == 0:
            r["emoji"] = "🎯"
        elif r["similarity"] >= 0.6:
            r["emoji"] = "🎯"
        else:
            r["emoji"] = "✅"

    return results[:top_k]


def get_all_embeddings(concepts: list = None) -> dict:
    """Genera embeddings para todos los conceptos."""
    if concepts is None:
        concepts = load_concepts()

    embeddings = {}
    for concept in concepts:
        emb = get_embedding(concept)
        if emb:
            embeddings[concept] = emb

    return embeddings


def compute_pca_2d(embeddings: dict) -> list:
    """Reduce embeddings a 2D usando PCA simple."""
    if not embeddings:
        return []

    concepts = list(embeddings.keys())
    vectors = list(embeddings.values())

    if len(vectors) < 2:
        return [{"concept": concepts[0], "x": 0, "y": 0}] if concepts else []

    # PCA simplificado (sin sklearn para evitar dependencia)
    # Centramos los datos
    n = len(vectors)
    dims = len(vectors[0])

    # Media por dimensión
    means = [sum(v[d] for v in vectors) / n for d in range(dims)]

    # Centrar
    centered = [[v[d] - means[d] for d in range(dims)] for v in vectors]

    # Tomar las dos primeras componentes principales (simplificado)
    # En realidad deberíamos calcular eigenvectors, pero para visualización
    # basta con proyectar en dos dimensiones con varianza alta

    # Calcular varianza por dimensión
    variances = []
    for d in range(min(dims, 100)):  # Solo primeras 100 dims
        var = sum(c[d] ** 2 for c in centered) / n
        variances.append((d, var))

    # Tomar las dos dimensiones con mayor varianza
    variances.sort(key=lambda x: x[1], reverse=True)
    dim1, dim2 = variances[0][0], variances[1][0]

    # Proyectar
    points = []
    for i, concept in enumerate(concepts):
        x = centered[i][dim1]
        y = centered[i][dim2]
        points.append({
            "concept": concept,
            "x": round(x * 100, 2),  # Escalar para visualización
            "y": round(y * 100, 2)
        })

    return points


def detect_clusters(embeddings: dict, n_clusters: int = 3) -> list:
    """Clustering simple de conceptos (k-means simplificado)."""
    if not embeddings or len(embeddings) < n_clusters:
        return [{"cluster": 0, "concepts": list(embeddings.keys())}]

    concepts = list(embeddings.keys())
    vectors = list(embeddings.values())

    # K-means simplificado
    # Inicializar centroides aleatorios
    random.seed(42)  # Reproducibilidad
    centroid_indices = random.sample(range(len(vectors)), n_clusters)
    centroids = [vectors[i][:] for i in centroid_indices]

    # Iterar
    for _ in range(10):  # Máximo 10 iteraciones
        # Asignar puntos a clusters
        assignments = []
        for vec in vectors:
            distances = [
                sum((a - b) ** 2 for a, b in zip(vec, c))
                for c in centroids
            ]
            assignments.append(distances.index(min(distances)))

        # Actualizar centroides
        new_centroids = []
        for k in range(n_clusters):
            cluster_vecs = [vectors[i] for i, a in enumerate(assignments) if a == k]
            if cluster_vecs:
                dims = len(cluster_vecs[0])
                new_centroid = [
                    sum(v[d] for v in cluster_vecs) / len(cluster_vecs)
                    for d in range(dims)
                ]
                new_centroids.append(new_centroid)
            else:
                new_centroids.append(centroids[k])
        centroids = new_centroids

    # Formar clusters
    clusters = []
    for k in range(n_clusters):
        cluster_concepts = [concepts[i] for i, a in enumerate(assignments) if a == k]
        if cluster_concepts:
            clusters.append({
                "cluster": k,
                "concepts": cluster_concepts,
                "size": len(cluster_concepts)
            })

    return clusters


def generate_quiz_question(concepts: list = None) -> dict:
    """Genera una pregunta de quiz sobre similitud."""
    if concepts is None:
        concepts = load_concepts()

    if len(concepts) < 4:
        return {"error": "Necesitas al menos 4 conceptos"}

    # Elegir concepto base
    base = random.choice(concepts)

    # Calcular similitudes con todos los demás
    similarities = []
    for c in concepts:
        if c != base:
            result = compute_similarity(base, c)
            if "similarity" in result:
                similarities.append((c, result["similarity"]))

    if len(similarities) < 4:
        return {"error": "No hay suficientes conceptos con embeddings"}

    # Ordenar por similitud
    similarities.sort(key=lambda x: x[1], reverse=True)

    # La respuesta correcta es el más similar
    correct = similarities[0][0]
    correct_similarity = similarities[0][1]

    # Elegir 3 distractores (menos similares)
    distractors = [s[0] for s in similarities[3:6]]

    # Mezclar opciones
    options = [correct] + distractors[:3]
    random.shuffle(options)

    return {
        "question": f"¿Cuál es más similar a \"{base}\"?",
        "base_concept": base,
        "options": options,
        "correct": correct,
        "correct_similarity": round(correct_similarity, 3)
    }


def check_quiz_answer(base: str, answer: str, correct: str) -> dict:
    """Verifica respuesta del quiz y da feedback."""
    is_correct = answer == correct

    # Calcular similitud de la respuesta dada
    result = compute_similarity(base, answer)
    answer_similarity = result.get("similarity", 0)

    # Calcular similitud correcta
    correct_result = compute_similarity(base, correct)
    correct_similarity = correct_result.get("similarity", 0)

    return {
        "correct": is_correct,
        "your_answer": answer,
        "correct_answer": correct,
        "your_similarity": round(answer_similarity, 3),
        "correct_similarity": round(correct_similarity, 3),
        "message": "¡Correcto! 🎉" if is_correct else f"Incorrecto. {correct} era más similar ({correct_similarity:.2f} vs {answer_similarity:.2f})"
    }


def get_visualization_data() -> dict:
    """Obtiene todos los datos necesarios para la visualización 2D."""
    concepts = load_concepts()
    embeddings = get_all_embeddings(concepts)

    if not embeddings:
        return {"error": "No se pudieron generar embeddings"}

    points = compute_pca_2d(embeddings)
    clusters = detect_clusters(embeddings)

    # Asignar color de cluster a cada punto
    concept_cluster = {}
    colors = ["#ffa500", "#3b82f6", "#10b981", "#8b5cf6", "#ef4444"]

    for cluster in clusters:
        for concept in cluster["concepts"]:
            concept_cluster[concept] = cluster["cluster"]

    for point in points:
        cluster_id = concept_cluster.get(point["concept"], 0)
        point["cluster"] = cluster_id
        point["color"] = colors[cluster_id % len(colors)]

    return {
        "points": points,
        "clusters": clusters,
        "total_concepts": len(concepts)
    }


# ============================================================
# CLI para pruebas directas
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 LABORATORIO DE EMBEDDINGS - VideoMine")
    print("=" * 60)

    # 1. Verificar modelo
    print("\n1️⃣ Verificando nomic-embed-text...")
    status = verify_model()
    if status["status"] == "ok":
        print(f"   ✅ Modelo funcionando ({status['dimensions']} dimensiones)")
    else:
        print(f"   ❌ {status}")
        print(f"   Ejecuta: {status.get('install_command', 'ollama pull nomic-embed-text')}")
        exit(1)

    # 2. Cargar conceptos
    print("\n2️⃣ Cargando conceptos...")
    concepts = load_concepts()
    print(f"   ✅ {len(concepts)} conceptos listos")
    print(f"   📝 {', '.join(concepts[:5])}...")

    # 3. Búsqueda semántica
    print("\n3️⃣ Búsqueda semántica...")
    query = "crear servidor web"
    results = semantic_search(query, concepts)
    print(f"   Query: \"{query}\"")
    for r in results[:3]:
        bar = "█" * (r["bar_width"] // 5) + "░" * (20 - r["bar_width"] // 5)
        print(f"   {r['emoji']} {r['concept']:15} {r['similarity']:.3f} {bar}")

    # 4. Similitud directa
    print("\n4️⃣ Similitudes...")
    pairs = [("Python", "Flask"), ("Docker", "Kubernetes"), ("Python", "JavaScript")]
    for a, b in pairs:
        result = compute_similarity(a, b)
        if "similarity" in result:
            print(f"   {result['emoji']} {a:12} ↔ {b:12} : {result['similarity']:.3f}")

    # 5. Quiz
    print("\n5️⃣ Quiz de similitud...")
    quiz = generate_quiz_question(concepts)
    if "question" in quiz:
        print(f"   {quiz['question']}")
        for i, opt in enumerate(quiz['options'], 1):
            marker = "✓" if opt == quiz['correct'] else " "
            print(f"   {marker} {i}. {opt}")

    # 6. Visualización
    print("\n6️⃣ Datos para visualización 2D...")
    viz = get_visualization_data()
    if "points" in viz:
        print(f"   ✅ {len(viz['points'])} puntos generados")
        print(f"   📦 {len(viz['clusters'])} clusters detectados")

    print("\n" + "=" * 60)
    print("✅ LABORATORIO LISTO")
    print("=" * 60)
