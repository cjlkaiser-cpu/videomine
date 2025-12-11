#!/usr/bin/env python3
"""
Cartographer - Graph
Gestiona el grafo de conocimiento unificado.
"""

import json
from pathlib import Path
from typing import Optional
from collections import defaultdict


DATA_DIR = Path(__file__).parent / "data"


class KnowledgeGraph:
    """
    Grafo de conocimiento que unifica conceptos de todos los nuggets.
    """

    def __init__(self):
        self.concepts = {}  # {canonical_name: ConceptNode}
        self.relations = []  # [{from, to, type, strength, sources}]
        self.sources = {}  # {video_id: [concept_names]}

    def add_concepts_from_video(self, video_id: str, extraction: dict):
        """
        Agrega conceptos de un video al grafo.

        Args:
            video_id: ID del video fuente
            extraction: Resultado de extractor.extract_concepts_claude_code
        """
        video_concepts = []

        for concept in extraction.get('concepts', []):
            name = concept['name']
            canonical = self._canonicalize(name)

            if canonical in self.concepts:
                # Actualizar concepto existente
                existing = self.concepts[canonical]
                existing['sources'].add(video_id)
                existing['importance'] = max(existing['importance'], concept['importance'])
                # Agregar alias si es diferente
                if name != canonical:
                    existing['aliases'].add(name)
            else:
                # Crear nuevo concepto
                self.concepts[canonical] = {
                    'name': canonical,
                    'type': concept['type'],
                    'importance': concept['importance'],
                    'parent': concept.get('parent'),
                    'sources': {video_id},
                    'aliases': {name} if name != canonical else set()
                }

            video_concepts.append(canonical)

        # Agregar relaciones
        for rel in extraction.get('relations', []):
            from_canonical = self._canonicalize(rel['from'])
            to_canonical = self._canonicalize(rel['to'])

            # Solo si ambos conceptos existen
            if from_canonical in self.concepts and to_canonical in self.concepts:
                self._add_relation(
                    from_canonical,
                    to_canonical,
                    rel['type'],
                    rel['strength'],
                    video_id
                )

        self.sources[video_id] = video_concepts

    def _canonicalize(self, name: str) -> str:
        """
        Normaliza un nombre de concepto.

        Args:
            name: Nombre original

        Returns:
            Nombre canonicalizado
        """
        # Normalizar a Title Case
        canonical = name.strip()

        # Mapeo de sinónimos conocidos
        synonyms = {
            'python 3': 'Python',
            'python3': 'Python',
            'py': 'Python',
            'machine learning': 'Machine Learning',
            'ml': 'Machine Learning',
            'deep learning': 'Deep Learning',
            'dl': 'Deep Learning',
            'neural network': 'Neural Network',
            'neural networks': 'Neural Network',
            'redes neuronales': 'Neural Network',
            'git': 'Git',
            'github': 'GitHub',
            'ia': 'Artificial Intelligence',
            'ai': 'Artificial Intelligence',
            'inteligencia artificial': 'Artificial Intelligence',
            'llm': 'LLM',
            'llms': 'LLM',
            'large language model': 'LLM',
            'claude': 'Claude',
            'claude code': 'Claude Code',
            'mcp': 'MCP',
            'model context protocol': 'MCP',
        }

        lower = canonical.lower()
        if lower in synonyms:
            return synonyms[lower]

        # Buscar coincidencia parcial en conceptos existentes
        for existing in self.concepts:
            if existing.lower() == lower:
                return existing

        return canonical

    def _add_relation(self, from_name: str, to_name: str, rel_type: str, strength: float, source: str):
        """
        Agrega o actualiza una relación.
        """
        # Buscar relación existente
        for rel in self.relations:
            if rel['from'] == from_name and rel['to'] == to_name and rel['type'] == rel_type:
                rel['strength'] = max(rel['strength'], strength)
                rel['sources'].add(source)
                return

        # Nueva relación
        self.relations.append({
            'from': from_name,
            'to': to_name,
            'type': rel_type,
            'strength': strength,
            'sources': {source}
        })

    def get_related_videos(self, video_id: str) -> list:
        """
        Obtiene videos relacionados por conceptos compartidos.

        Args:
            video_id: ID del video

        Returns:
            Lista de {video_id, shared_concepts, score}
        """
        if video_id not in self.sources:
            return []

        my_concepts = set(self.sources[video_id])
        related = defaultdict(lambda: {'concepts': [], 'score': 0})

        for other_id, concepts in self.sources.items():
            if other_id == video_id:
                continue

            shared = my_concepts & set(concepts)
            if shared:
                related[other_id]['concepts'] = list(shared)
                # Score basado en cantidad y importancia
                score = sum(self.concepts[c]['importance'] for c in shared)
                related[other_id]['score'] = score

        # Ordenar por score
        result = [
            {'video_id': vid, **data}
            for vid, data in sorted(related.items(), key=lambda x: -x[1]['score'])
        ]

        return result[:10]  # Top 10

    def get_concept_info(self, name: str) -> Optional[dict]:
        """
        Obtiene información de un concepto.

        Args:
            name: Nombre del concepto

        Returns:
            dict con info del concepto o None
        """
        canonical = self._canonicalize(name)
        if canonical not in self.concepts:
            return None

        concept = self.concepts[canonical]
        return {
            'name': concept['name'],
            'type': concept['type'],
            'importance': concept['importance'],
            'aliases': list(concept['aliases']),
            'sources': list(concept['sources']),
            'parent': concept.get('parent'),
            'related': self._get_related_concepts(canonical)
        }

    def _get_related_concepts(self, name: str) -> list:
        """
        Obtiene conceptos relacionados directamente.
        """
        related = []
        for rel in self.relations:
            if rel['from'] == name:
                related.append({'name': rel['to'], 'type': rel['type'], 'strength': rel['strength']})
            elif rel['to'] == name:
                related.append({'name': rel['from'], 'type': rel['type'], 'strength': rel['strength']})
        return related

    def to_d3_format(self) -> dict:
        """
        Exporta el grafo en formato para D3.js.

        Returns:
            dict con nodes y links para D3 force-directed graph
        """
        nodes = []
        for name, concept in self.concepts.items():
            nodes.append({
                'id': name,
                'type': concept['type'],
                'importance': concept['importance'],
                'size': len(concept['sources']),  # Tamaño = videos que lo mencionan
                'sources': list(concept['sources'])
            })

        links = []
        for rel in self.relations:
            links.append({
                'source': rel['from'],
                'target': rel['to'],
                'type': rel['type'],
                'strength': rel['strength']
            })

        return {'nodes': nodes, 'links': links}

    def save(self, path: Optional[Path] = None):
        """
        Guarda el grafo a disco.
        """
        path = path or DATA_DIR / "graph.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convertir sets a listas para JSON
        data = {
            'concepts': {
                name: {
                    **{k: v for k, v in concept.items() if k not in ('sources', 'aliases')},
                    'sources': list(concept['sources']),
                    'aliases': list(concept['aliases'])
                }
                for name, concept in self.concepts.items()
            },
            'relations': [
                {**rel, 'sources': list(rel['sources'])}
                for rel in self.relations
            ],
            'sources': self.sources
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  Grafo guardado: {len(self.concepts)} conceptos, {len(self.relations)} relaciones")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'KnowledgeGraph':
        """
        Carga el grafo desde disco.
        """
        path = path or DATA_DIR / "graph.json"

        graph = cls()

        if not path.exists():
            return graph

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Restaurar concepts con sets
        for name, concept in data.get('concepts', {}).items():
            graph.concepts[name] = {
                **concept,
                'sources': set(concept.get('sources', [])),
                'aliases': set(concept.get('aliases', []))
            }

        # Restaurar relations con sets
        for rel in data.get('relations', []):
            graph.relations.append({
                **rel,
                'sources': set(rel.get('sources', []))
            })

        graph.sources = data.get('sources', {})

        return graph


def rebuild_graph(vault_path: str = "vault") -> KnowledgeGraph:
    """
    Reconstruye el grafo completo desde todos los nuggets.

    Args:
        vault_path: Ruta al vault

    Returns:
        KnowledgeGraph reconstruido
    """
    from cartographer.extractor import extract_all

    print("Reconstruyendo grafo de conocimiento...")

    # Extraer conceptos de todos los nuggets
    extractions = extract_all(vault_path)

    # Crear grafo
    graph = KnowledgeGraph()
    for video_id, extraction in extractions.items():
        graph.add_concepts_from_video(video_id, extraction)

    # Guardar
    graph.save()

    return graph
