#!/usr/bin/env python3
"""
Red de Amistades: Mínima Conectividad
-------------------------------------
Determina el conjunto mínimo de conexiones necesarias para asegurar que todos
los usuarios de un campus estén conectados entre sí, minimizando el costo total.

Estrategia: Algoritmo de Kruskal
- Ordena todas las conexiones posibles por costo (de menor a mayor)
- Añade conexiones una por una, siempre que NO creen ciclos/redundancias
- Utiliza Union-Find (DSU) para detectar ciclos eficientemente
- El resultado es un Árbol de Expansión Mínima (MST)

Propiedades del MST:
- Conecta todos los nodos con exactamente n-1 aristas
- Tiene el menor costo total posible
- No contiene ciclos (es un árbol)

Uso:
  python3 red_minima_kruskal.py --data-dir .

Formato de datos (JSON):
- usuarios.json: [{"id": int, "nombre": str, "apellido": str, ...}, ...]
- amistades.json: [{"u": int, "v": int, "costo": int}, ...]
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Edge:
    """Representa una conexión (arista) entre dos usuarios con un costo asociado."""
    u: int
    v: int
    cost: int


class DSU:
    """
    Disjoint Set Union (Union-Find) .
    
    Permite:
    - Verificar si dos nodos están en la misma componente (mismo conjunto)
    - Unir dos componentes de forma eficiente
    - Detectar si agregar una arista crearía un ciclo
    """
    
    def __init__(self, n: int):
        self.parent = list(range(n))  # Cada nodo es su propio padre inicialmente
        self.rank = [0] * n           # Altura aproximada del árbol
        self.components = n           # Número de componentes conexas
    
    def find(self, x: int) -> int:
        """
        Encuentra el representante (raíz) del conjunto que contiene a x.
        Aplica path compression para optimizar futuras búsquedas.
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, a: int, b: int) -> bool:
        """
        Une los conjuntos de a y b si están separados.
        
        Returns:
            True si se unieron (estaban en componentes distintas)
            False si ya estaban conectados (agregar arista crearía ciclo)
        """
        ra, rb = self.find(a), self.find(b)
        
        if ra == rb:
            return False  # Ya están conectados → agregar arista crearía ciclo
        
        # Union by rank: el árbol más pequeño se une al más grande
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        
        self.components -= 1
        return True
    
    def connected(self, a: int, b: int) -> bool:
        """Verifica si a y b están en la misma componente."""
        return self.find(a) == self.find(b)


def load_edges(path: Path) -> List[Edge]:
    """Carga las conexiones posibles desde amistades.json."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Edge(int(e["u"]), int(e["v"]), int(e["costo"])) for e in data]


def load_users(path: Path) -> Dict[int, dict]:
    """Carga usuarios desde usuarios.json."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(u["id"]): u for u in data}


def infer_n_vertices(users: Dict[int, dict], edges: List[Edge]) -> int:
    """Determina el número de vértices (max_id + 1)."""
    max_id = -1
    if users:
        max_id = max(max_id, max(users.keys()))
    if edges:
        max_id = max(max_id, max(max(e.u, e.v) for e in edges))
    return max_id + 1


def pretty_user(users: Dict[int, dict], uid: int) -> str:
    """Formato legible para un usuario."""
    u = users.get(uid)
    if not u:
        return f"Usuario#{uid}"
    return f'{u.get("nombre", "?")} {u.get("apellido", "")} (id={uid})'


def kruskal_mst(n: int, edges: List[Edge], users: Dict[int, dict], verbose: bool = True) -> Tuple[List[Edge], int]:
    """
    Algoritmo de Kruskal para encontrar el Árbol de Expansión Mínima (MST).
    
    Estrategia Greedy:
    1. Ordenar todas las aristas por costo ascendente
    2. Para cada arista (de menor a mayor costo):
       - Si conecta dos componentes distintas → AGREGAR al MST
       - Si conecta nodos ya conectados → DESCARTAR (crearía ciclo)
    3. Terminar cuando tengamos n-1 aristas (árbol completo)
    """
    dsu = DSU(n)
    mst: List[Edge] = []
    costo_total = 0
    
    # Paso 1: Ordenar aristas por costo (greedy: las más baratas primero)
    sorted_edges = sorted(edges, key=lambda e: e.cost)
    
    if verbose:
        print("\n" + "=" * 70)
        print("ALGORITMO DE KRUSKAL - Construcción del Árbol de Expansión Mínima")
        print("=" * 70)
        print(f"\nTotal de conexiones posibles: {len(edges)}")
        print(f"Conexiones necesarias para el MST: {n - 1}")
        print("\nAristas ordenadas por costo:")
        for i, e in enumerate(sorted_edges, 1):
            print(f"  {i:2d}. ({e.u}, {e.v}) costo={e.cost}")
        
        print("\n" + "-" * 70)
        print("PROCESO DE SELECCIÓN (añadiendo conexiones baratas sin crear ciclos)")
        print("-" * 70 + "\n")
    
    paso = 1
    for edge in sorted_edges:
        u_name = pretty_user(users, edge.u)
        v_name = pretty_user(users, edge.v)
        
        # Verificar si agregar esta arista crearía un ciclo
        if dsu.union(edge.u, edge.v):
            # ✅ No crea ciclo → AGREGAR al MST
            mst.append(edge)
            costo_total += edge.cost
            
            if verbose:
                print(f"[Paso {paso:2d}] ✅ AGREGAR: {u_name} <--> {v_name}")
                print(f"           Costo: {edge.cost} | Costo acumulado: {costo_total}")
                print(f"           Componentes restantes: {dsu.components}")
                print()
            
            paso += 1
            
            # Si ya tenemos n-1 aristas, el MST está completo
            if len(mst) == n - 1:
                break
        else:
            # ❌ Crearía ciclo → DESCARTAR
            if verbose:
                print(f"          ❌ DESCARTAR: {u_name} <--> {v_name} (costo={edge.cost})")
                print(f"             Razón: Ya están conectados, crearía ciclo/redundancia")
                print()
    
    return mst, costo_total


def run(data_dir: Path, verbose: bool = True) -> None:
    """Ejecuta el algoritmo y muestra resultados."""
    amist_path = data_dir / "amistades.json"
    users_path = data_dir / "usuarios.json"
    
    if not amist_path.exists():
        raise FileNotFoundError(f"No se encontró amistades.json en: {amist_path}")
    if not users_path.exists():
        raise FileNotFoundError(f"No se encontró usuarios.json en: {users_path}")
    
    # Cargar datos
    edges = load_edges(amist_path)
    users = load_users(users_path)
    n = infer_n_vertices(users, edges)
    
    print("\n" + "=" * 70)
    print("RED DE AMISTADES: MÍNIMA CONECTIVIDAD")
    print("=" * 70)
    print(f"\nUsuarios en el campus: {n}")
    print(f"Conexiones posibles totales: {len(edges)}")
    print(f"Costo total si usáramos TODAS las conexiones: {sum(e.cost for e in edges)}")
    
    # Ejecutar Kruskal
    mst, costo_total = kruskal_mst(n, edges, users, verbose)
    
    # Resultados finales
    print("\n" + "=" * 70)
    print("RESULTADO: ÁRBOL DE EXPANSIÓN MÍNIMA (MST)")
    print("=" * 70)
    
    if len(mst) == n - 1:
        print(f"\n✅ RED COMPLETAMENTE CONECTADA")
        print(f"\nConexiones mínimas necesarias: {len(mst)} (de {len(edges)} posibles)")
        print(f"Costo total mínimo: {costo_total}")
        print(f"Ahorro vs usar todas las conexiones: {sum(e.cost for e in edges) - costo_total}")
        
        print("\n📋 Lista de conexiones del MST:")
        print("-" * 50)
        for i, edge in enumerate(mst, 1):
            u_name = pretty_user(users, edge.u)
            v_name = pretty_user(users, edge.v)
            print(f"  {i:2d}. {u_name} <--> {v_name} | Costo: {edge.cost}")
        print("-" * 50)
        print(f"  TOTAL: {len(mst)} conexiones | Costo: {costo_total}")
    else:
        print(f"\n⚠️ NO SE PUEDE CONECTAR TODA LA RED")
        print(f"   Conexiones encontradas: {len(mst)} de {n-1} necesarias")
        print(f"   Hay usuarios sin conexiones posibles hacia el resto.")
    
    # Visualización simple del árbol
    print("\n📊 Estructura del MST (representación de adyacencia):")
    print("-" * 50)
    adj: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(n)}
    for e in mst:
        adj[e.u].append((e.v, e.cost))
        adj[e.v].append((e.u, e.cost))
    
    for node in range(n):
        if adj[node]:
            neighbors = ", ".join(f"{v}(c={c})" for v, c in sorted(adj[node]))
            print(f"  Usuario {node}: conectado a [{neighbors}]")
        else:
            print(f"  Usuario {node}: (aislado)")


def main() -> None:
    """Punto de entrada CLI."""
    parser = argparse.ArgumentParser(
        description="Red de Amistades: Mínima Conectividad usando Kruskal"
    )
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default=".", 
        help="Carpeta con usuarios.json y amistades.json"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Modo silencioso (solo resultado final)"
    )
    args = parser.parse_args()
    
    run(Path(args.data_dir), verbose=not args.quiet)


if __name__ == "__main__":
    main()
