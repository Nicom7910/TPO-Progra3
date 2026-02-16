#!/usr/bin/env python3
"""
Opcional 1 - Simulación de Bloqueos y Conexiones Alternativas
------------------------------------------------------------
Este script trabaja sobre el mismo dataset del TP (amistades.json, usuarios.json).

Idea:
1) "Bloqueo" = eliminar una arista (u,v) del grafo de amistades.
2) Ejecutar Kruskal  sobre el grafo resultante.
   - Si el bosque final tiene 1 componente => grafo conexo.
   - Si tiene k>1 componentes => NO conexo.
3) Si NO es conexo: proponer un conjunto mínimo de nuevas conexiones (k-1)
   conectando las componentes en cadena.

Criterio de selección de candidato por componente:
- Luego de Kruskal, cada componente queda como un subárbol (bosque).
- Para cada subárbol, elegimos como "candidato" un nodo que participa en la
  arista de menor costo dentro de ese subárbol (la conexión más barata del componente).
- Si una componente no tiene aristas (nodo aislado), se toma el menor id como candidato.

Uso:
  python3 bloqueos_kruskal.py --data-dir ./TPO-Progra3-main --block-u 0 --block-v 1

Si no se pasa bloqueo por parámetros, usa un caso demo.

Formato de datos (JSON)
- usuarios.json: lista de usuarios
    [
        {
            "id": int,
            "nombre": str,
            "apellido": str,
            "intereses": List[str],
            "tiempo_max": int
        },
        ...
    ]

- amistades.json: lista de amistades (aristas no dirigidas con costo)
    [
        { "u": int, "v": int, "costo": int },
        ...
    ]
    Nota: (u,v) se interpreta como arista no dirigida; el bloqueo elimina todas las ocurrencias del par.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Iterable, Set

# Alias de tipos para mayor claridad
# Mapa de componentes: root (representante DSU) -> lista de nodos (ids de usuario)
ComponentMap = Dict[int, List[int]]


@dataclass(frozen=True)
class Edge:
    """Estructura de datos para una arista no dirigida con costo.

    Campos:
    - u: id del usuario extremo 1
    - v: id del usuario extremo 2
    - cost: peso/costo de la conexión (clave 'costo' en amistades.json)

    Notas:
    - Se interpreta como arista no dirigida; las comparaciones usan normalize_pair(u, v).
    - El grafo se asume simple (sin multiaristas), pero el bloqueo elimina todas las ocurrencias del par.
    """
    u: int
    v: int
    cost: int


class DSU:
    """Disjoint Set Union (Union-Find) con path compression y union by rank."""
    def __init__(self, n: int):
        # Cada nodo comienza como su propio padre (representante de su conjunto)
        self.parent = list(range(n))
        # "rank" aproxima la altura del árbol para decidir la unión más eficiente
        self.rank = [0] * n
        self.components = n  # contador de componentes

    def find(self, x: int) -> int:
        """Devuelve el representante (root) del conjunto que contiene x.

        Inputs: x (int) nodo
        Output: root (int) identificador de la componente
        """
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        """Funde los conjuntos de a y b si están separados.

        Inputs: a, b (int)
        Output: True si se unieron; False si ya estaban en la misma componente
        Efecto: actualiza parent/rank y reduce el contador de componentes
        """
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.components -= 1
        return True


def load_edges(path: Path) -> List[Edge]:
    """Lee amistades desde JSON y retorna una lista de aristas Edge(u, v, cost).

    Inputs: path (Path) al archivo amistades.json
    Output: List[Edge]
    """
    # Formato esperado: [{"u": int, "v": int, "costo": int}, ...]
    data = json.loads(path.read_text(encoding="utf-8"))
    edges: List[Edge] = []
    for e in data:
        edges.append(Edge(int(e["u"]), int(e["v"]), int(e["costo"])))
    return edges


def load_users(path: Path) -> Dict[int, dict]:
    """Carga usuarios desde JSON y retorna un dict id -> datos de usuario.

    Inputs: path (Path) al archivo usuarios.json
    Output: Dict[int, dict]
    """
    # Formato esperado: [{"id": int, "nombre": str, "apellido": str, ...}, ...]
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(u["id"]): u for u in data}


def infer_n_vertices(users: Dict[int, dict], edges: List[Edge]) -> int:
    """Infere el número de vértices como max(id) observado + 1.

    Inputs: users (Dict), edges (List[Edge])
    Output: n (int) tamaño del grafo para DSU
    """
    # Nota: si los ids no son contiguos, esto crea un DSU de tamaño max_id+1.
    # En grafos muy dispersos, se podría mapear ids a índices compactos.
    max_id = -1
    if users:
        max_id = max(max_id, max(users.keys()))
    if edges:
        max_id = max(max_id, max(max(e.u, e.v) for e in edges))
    return max_id + 1


def normalize_pair(a: int, b: int) -> Tuple[int, int]:
    """Normaliza un par (a,b) de arista no dirigida para comparación: (min, max)."""
    return (a, b) if a <= b else (b, a)


def apply_block(edges: List[Edge], block_u: int, block_v: int) -> Tuple[List[Edge], bool]:
    """Elimina una arista no dirigida (u,v). Si hay múltiples con mismo par, elimina todas."""
    target = normalize_pair(block_u, block_v)
    out: List[Edge] = []
    removed = False
    for e in edges:
        # Eliminar TODAS las ocurrencias del par no dirigido (u,v)
        if normalize_pair(e.u, e.v) == target:
            removed = True
            continue
        out.append(e)
    # 'removed' indica si se eliminó al menos una arista del par bloqueado
    return out, removed


def kruskal_forest(n: int, edges: List[Edge]) -> Tuple[DSU, List[Edge]]:
    """Aplica Kruskal sobre todas las aristas y devuelve el DSU final y el bosque (ARM parcial).

    Inputs: n (int), edges (List[Edge])
    Output: (dsu, forest_edges)
    """
    dsu = DSU(n)
    selected: List[Edge] = []
    # Estrategia greedy: procesar aristas ordenadas por costo ascendente
    for e in sorted(edges, key=lambda x: x.cost):
        if dsu.union(e.u, e.v):
            # Solo se agregan aristas que conectan componentes distintas
            selected.append(e)
    return dsu, selected


def build_components(n: int, dsu: DSU) -> ComponentMap:
    """Construye el mapa de componentes a partir del DSU.

    Inputs: n (int), dsu (DSU)
    Output: Dict[root, List[nodos]]
    """
    comps: ComponentMap = {}
    for v in range(n):
        r = dsu.find(v)  # Representante (root) de la componente que contiene a v
        comps.setdefault(r, []).append(v)
    return comps


def pick_candidate_by_min_edge_in_tree(components: ComponentMap, forest_edges: List[Edge]) -> Dict[int, int]:
    """Selecciona un candidato por componente.

    Regla: nodo que participa en la arista de menor costo del subárbol; si no hay aristas, menor id.
    Inputs: components (Dict[root, List[int]]), forest_edges (List[Edge])
    Output: Dict[root -> candidate_id]
    """
    # Inicializar candidato por fallback: menor id
    cand: Dict[int, int] = {root: min(nodes) for root, nodes in components.items()}

    # Necesitamos poder saber a qué componente pertenece un nodo.
    node_to_root: Dict[int, int] = {v: root for root, nodes in components.items() for v in nodes}

    # 'best_cost' almacena el menor costo visto dentro de cada componente
    best_cost: Dict[int, int] = {root: 10**18 for root in components.keys()}

    for e in forest_edges:
        r = node_to_root[e.u]  # e.u y e.v están en la misma componente (por construcción)
        if e.cost < best_cost[r]:
            best_cost[r] = e.cost
            # Elegimos como candidato el extremo "más chico" para ser determinísticos
            cand[r] = min(e.u, e.v)

    return cand


def propose_min_new_connections(component_roots: List[int], candidates: Dict[int, int], components: ComponentMap) -> List[Tuple[int, int]]:
    """Construye k-1 nuevas conexiones conectando candidatos consecutivos.

    Inputs: component_roots (List[int]), candidates (Dict[root->id]), components (ComponentMap)
    Output: List[Tuple[u, v]] aristas nuevas sugeridas
    """
    if len(component_roots) <= 1:
        return []
    new_edges: List[Tuple[int, int]] = []
    # Conectar en "cadena": C1<->C2, C2<->C3, ..., C(k-1)<->Ck
    for i in range(len(component_roots) - 1):
        a_root = component_roots[i]
        b_root = component_roots[i + 1]
        a = candidates[a_root]
        b = candidates[b_root]
        if a == b:
            # Evitar candidatos duplicados: elegir un alternativo dentro de la componente b
            nodes_b = sorted(components.get(b_root, []))
            alt_b = None
            for nb in nodes_b:
                if nb != a:
                    alt_b = nb
                    break
            if alt_b is not None:
                b = alt_b
            # Si no hay alternativo (componente de un solo nodo igual a 'a'), se mantiene 'b'.
        new_edges.append((a, b))
    return new_edges


def pretty_user(users: Dict[int, dict], uid: int) -> str:
    """Devuelve una representación amigable del usuario por id."""
    u = users.get(uid)
    if not u:
        return f"Usuario#{uid}"
    return f'{u.get("nombre","?")} {u.get("apellido","?")} (id={uid})'


def run(data_dir: Path, block_u: Optional[int], block_v: Optional[int], simple: bool = False) -> None:
    """Orquesta la simulación completa.

    Inputs: data_dir (Path), block_u/block_v (Optional[int]), simple (bool)
    Output: imprime estado de conectividad y propuesta de reconexión (o versión resumida)
    """
    amist_path = data_dir / "amistades.json"
    users_path = data_dir / "usuarios.json"

    if not amist_path.exists():
        raise FileNotFoundError(f"No se encontró amistades.json en: {amist_path}")
    if not users_path.exists():
        raise FileNotFoundError(f"No se encontró usuarios.json en: {users_path}")

    # 1) Cargar datos
    edges = load_edges(amist_path)
    users = load_users(users_path)
    n = infer_n_vertices(users, edges)

    # Elegir bloqueo
    # 2) Elegir bloqueo (si no se especifica, usar demo con la primera arista)
    if block_u is None or block_v is None:
        if edges:
            block_u, block_v = edges[0].u, edges[0].v
        else:
            block_u, block_v = 0, 0
        if not simple:
            print(f"[DEMO] No se indicó bloqueo. Se bloquea la arista: ({block_u}, {block_v})")

    # Aplicar bloqueo
    # 3) Aplicar bloqueo
    edges_after, removed = apply_block(edges, block_u, block_v)

    if not simple:
        print("=== Opcional 1: Simulación de Bloqueos ===")
        print(f"Nodos (usuarios) detectados: {n}")
        print(f"Aristas originales: {len(edges)} | Aristas tras bloqueo: {len(edges_after)}")
        print(f"Bloqueo solicitado: ({block_u}, {block_v}) -> {'ELIMINADA' if removed else 'NO ENCONTRADA (sin cambios)'}")
        if removed:
            print(f"  Bloqueo entre: {pretty_user(users, block_u)}  <->  {pretty_user(users, block_v)}")

    # Kruskal sobre grafo resultante
    # 4) Ejecutar Kruskal/DSU sobre el grafo resultante
    dsu, forest = kruskal_forest(n, edges_after)
    comps = build_components(n, dsu)
    k = len(comps)

    if simple:
        # Modo resumido: reporta cantidad de componentes y sugerencias mínimas
        print(f"Componentes: {k}")
        if k == 1:
            print("Conexo")
            return
        candidates = pick_candidate_by_min_edge_in_tree(comps, forest)
        roots_sorted = sorted(comps.keys())
        new_edges = propose_min_new_connections(roots_sorted, candidates, comps)
        print(f"Nuevas conexiones sugeridas (k-1={k-1}): {new_edges}")
        return

    print("\n--- Resultado conectividad (via Kruskal/DSU) ---")
    print(f"Componentes encontradas: {k}")
    if k == 1:
        print("✅ El grafo sigue siendo completamente conexo.")
        return
    else:
        print("❌ El grafo NO es completamente conexo.")

    # Candidatos por componente (criterio: arista mínima dentro del subárbol)
    # 5) Elegir candidato por componente (arista mínima del subárbol)
    candidates = pick_candidate_by_min_edge_in_tree(comps, forest)

    # Orden determinístico de componentes por root
    # 6) Orden determinístico de componentes por root (DSU)
    roots_sorted = sorted(comps.keys())

    print("\n--- Componentes y candidato elegido ---")
    for root in roots_sorted:
        nodes = comps[root]
        cand = candidates[root]
        print(f"Componente root={root} | tamaño={len(nodes)} | candidato={cand} ({pretty_user(users, cand)}) | nodos={nodes}")

    # Proponer nuevas conexiones mínimas: k-1
    # 7) Proponer nuevas conexiones mínimas: k-1
    new_edges = propose_min_new_connections(roots_sorted, candidates, comps)

    print("\n--- Propuesta de nuevas conexiones mínimas (k-1) ---")
    print(f"Se requieren al menos {k-1} nuevas conexiones.")
    for (a, b) in new_edges:
        print(f" + Conectar {a} ({pretty_user(users, a)})  <->  {b} ({pretty_user(users, b)})")

    # Validación rápida (opcional)
    # 8) Validación rápida: unir las nuevas aristas al grafo y verificar que queda conexo
    dsu2 = DSU(n)
    for e in edges_after:
        dsu2.union(e.u, e.v)
    for (a, b) in new_edges:
        dsu2.union(a, b)
    if dsu2.components == 1:
        print("\n✅ Validación: agregando las conexiones propuestas, el grafo queda conexo.")
    else:
        print("\n⚠️ Validación: el grafo aún no quedó conexo (revisar candidatos o datos).")


def main() -> None:
    """Punto de entrada CLI. Parseo de argumentos y ejecución de run()."""
    parser = argparse.ArgumentParser(description="Opcional 1: Bloqueos + reconexión mínima (usando Kruskal).")
    parser.add_argument("--data-dir", type=str, default=".", help="Carpeta donde están usuarios.json y amistades.json.")
    parser.add_argument("--block-u", type=int, default=None, help="Extremo u de la arista a bloquear.")
    parser.add_argument("--block-v", type=int, default=None, help="Extremo v de la arista a bloquear.")
    parser.add_argument("--simple", action="store_true", help="Salida resumida para comprensión rápida.")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    run(data_dir, args.block_u, args.block_v, args.simple)


if __name__ == "__main__":
    main()
