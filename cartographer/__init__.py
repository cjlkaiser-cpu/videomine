#!/usr/bin/env python3
"""
Cartographer - Grafo de Conocimiento
Sistema de conexión semántica entre videos estilo Obsidian.
"""

from cartographer.extractor import extract_from_nugget, extract_all
from cartographer.graph import KnowledgeGraph, rebuild_graph, DATA_DIR


def map_video(video_id: str, vault_path: str = "vault") -> dict:
    """
    Extrae conceptos de un video y lo agrega al grafo.

    Args:
        video_id: ID del video
        vault_path: Ruta al vault

    Returns:
        dict con los conceptos extraídos
    """
    print(f"Mapeando video {video_id}...")

    # Extraer conceptos
    extraction = extract_from_nugget(video_id, vault_path)

    # Cargar grafo existente y agregar
    graph = KnowledgeGraph.load()
    graph.add_concepts_from_video(video_id, extraction)
    graph.save()

    return extraction


def get_related(video_id: str) -> list:
    """
    Obtiene videos relacionados por conceptos compartidos.

    Args:
        video_id: ID del video

    Returns:
        Lista de videos relacionados
    """
    graph = KnowledgeGraph.load()
    return graph.get_related_videos(video_id)


def get_concept(name: str) -> dict:
    """
    Obtiene información de un concepto.

    Args:
        name: Nombre del concepto

    Returns:
        dict con info del concepto
    """
    graph = KnowledgeGraph.load()
    return graph.get_concept_info(name)


def get_graph_data() -> dict:
    """
    Obtiene el grafo en formato D3.js.

    Returns:
        dict con nodes y links
    """
    graph = KnowledgeGraph.load()
    return graph.to_d3_format()


def rebuild(vault_path: str = "vault") -> dict:
    """
    Reconstruye el grafo completo desde cero.

    Args:
        vault_path: Ruta al vault

    Returns:
        Estadísticas del grafo
    """
    graph = rebuild_graph(vault_path)
    data = graph.to_d3_format()

    return {
        'concepts': len(data['nodes']),
        'relations': len(data['links']),
        'videos': len(graph.sources)
    }
