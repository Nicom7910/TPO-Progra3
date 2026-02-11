import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# =========================
# Modelos
# =========================

@dataclass(frozen=True)
class Usuario:
    id: int
    nombre: str
    apellido: str
    intereses: List[str]
    tiempo_max: int
    campus: str = "UADE"


@dataclass(frozen=True)
class Arista:
    u: int
    v: int
    costo: int = 1            # opcional (si no viene, peso 1)


# =========================
# JSON helpers (carga + demo opcional)
# =========================

def cargar_usuarios(path: str) -> List[Usuario]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    usuarios: List[Usuario] = []
    for u in data:
        usuarios.append(
            Usuario(
                id=int(u["id"]),
                nombre=str(u["nombre"]),
                apellido=str(u["apellido"]),
                intereses=list(u.get("intereses", [])),
                tiempo_max=int(u.get("tiempo_max", 0)),
                campus=str(u.get("campus", "DEFAULT")),
            )
        )
    return usuarios


def cargar_amistades(path: str) -> List[Arista]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    aristas: List[Arista] = []
    for e in data:
        aristas.append(
            Arista(
                u=int(e["u"]),
                v=int(e["v"]),
                costo=int(e.get("costo", 1))
            )
        )
    return aristas


def _crear_amistades_demo_si_no_existe(path: str) -> None:
    """
    Demo: crea un grafo (posiblemente no conexo) con costos opcionales.
    """
    if os.path.exists(path):
        return

    amistades_demo = [
        {"u": 0, "v": 1, "costo": 3},
        {"u": 1, "v": 2, "costo": 2},
        {"u": 0, "v": 2, "costo": 5},
        # componente aparte
        {"u": 3, "v": 4, "costo": 1},
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(amistades_demo, f, ensure_ascii=False, indent=2)


# =========================
# Disjoint Set Union (Union-Find) para Kruskal
# =========================

class DSU:
    def __init__(self, nodes: List[int]):
        self.parent = {x: x for x in nodes}
        self.rank = {x: 0 for x in nodes}

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


# =========================
# Utilidades de grafo
# =========================

def filtrar_por_campus(usuarios: List[Usuario], campus: str) -> List[Usuario]:
    return [u for u in usuarios if u.campus == campus]


def aristas_internas(aristas: List[Arista], ids_validos: set) -> List[Arista]:
    return [e for e in aristas if e.u in ids_validos and e.v in ids_validos]


def componentes_conexas(nodes: List[int], edges: List[Arista]) -> List[List[int]]:
    adj: Dict[int, List[int]] = {x: [] for x in nodes}
    for e in edges:
        adj[e.u].append(e.v)
        adj[e.v].append(e.u)

    visited = set()
    comps: List[List[int]] = []

    for start in nodes:
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        comp = []
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if y not in visited:
                    visited.add(y)
                    stack.append(y)
        comps.append(comp)

    return comps


# =========================
# Solución principal
# =========================

def conexiones_minimas_campus(
    usuarios: List[Usuario],
    amistades: List[Arista],
    campus: str
) -> Tuple[List[Arista], int, List[List[int]], List[Tuple[int, int]]]:
    """
    Devuelve:
      - aristas_seleccionadas: conjunto mínimo de conexiones (si es conexo, es un árbol de expansión)
        si hay costos -> MST por Kruskal; si no hay costos reales, igual funciona (costo=1).
      - costo_total: suma de costos de esas conexiones
      - componentes: componentes conexas dentro del campus usando amistades actuales
      - nuevas_conexiones_sugeridas: si está desconectado, sugiere (componentes-1) conexiones nuevas
        (u,v) para conectarlo (mínimo número). No puede calcular “costo mínimo” de nuevas si no se provee modelo.
    """
    usuarios_campus = filtrar_por_campus(usuarios, campus)
    nodes = [u.id for u in usuarios_campus]
    ids = set(nodes)

    edges = aristas_internas(amistades, ids)

    # 1) Componentes existentes
    comps = componentes_conexas(nodes, edges)

    # 2) Si el campus es conexo, sacamos MST con Kruskal (mínimo costo).
    #    Si no hay costos, todos 1 -> igual da un árbol de expansión de n-1.
    edges_sorted = sorted(edges, key=lambda e: e.costo)
    dsu = DSU(nodes)
    selected: List[Arista] = []
    cost_total = 0

    for e in edges_sorted:
        if dsu.union(e.u, e.v):
            selected.append(e)
            cost_total += e.costo
            if len(selected) == max(0, len(nodes) - 1):
                break

    # Verificar si realmente conectó a todos
    # (si comps > 1, nunca llegará a n-1 con solo edges existentes)
    nuevas_conexiones: List[Tuple[int, int]] = []
    if len(comps) > 1:
        # mínimo número de nuevas conexiones para conectar k componentes: k-1
        reps = [c[0] for c in comps]  # representante por componente
        for i in range(len(reps) - 1):
            nuevas_conexiones.append((reps[i], reps[i + 1]))

    return selected, cost_total, comps, nuevas_conexiones


def imprimir_resultado(
    usuarios: List[Usuario],
    aristas_seleccionadas: List[Arista],
    costo_total: int,
    componentes: List[List[int]],
    nuevas_conexiones: List[Tuple[int, int]],
    campus: str
) -> None:
    u_by_id = {u.id: u for u in usuarios if u.campus == campus}

    print(f"\n=== Conectividad mínima del campus: {campus} ===")
    print("Usuarios en campus:", len(u_by_id))

    print("\nComponentes actuales:", len(componentes))
    for i, comp in enumerate(componentes, 1):
        nombres = [f"{u_by_id[x].nombre}" for x in comp]
        print(f"  Componente {i}: {nombres}")

    print("\nConexiones seleccionadas (mínimas dentro de las existentes):")
    for e in aristas_seleccionadas:
        a = u_by_id[e.u]
        b = u_by_id[e.v]
        print(f"  - {a.nombre} <-> {b.nombre} | costo={e.costo}")
    print("Costo total (existentes seleccionadas):", costo_total)

    if len(componentes) == 1:
        print("\nEl campus ya es conexo. Con estas conexiones basta (árbol de expansión / MST).")
        print("Cantidad de conexiones seleccionadas:", len(aristas_seleccionadas), "(debería ser n-1)")
    else:
        print("\nEl campus NO es conexo con las amistades actuales.")
        print("Mínimas NUEVAS conexiones a agregar:", len(componentes) - 1)
        print("Sugerencia de nuevas conexiones (u, v) para unir componentes:")
        for (u, v) in nuevas_conexiones:
            print(f"  - {u} <-> {v}")


def main():
    usuarios_path = "usuarios.json"
    amistades_path = "amistades.json"
    usuarios = cargar_usuarios(usuarios_path)
    amistades = cargar_amistades(amistades_path)

    # Elegí el campus que quieras evaluar
    campus = "UADE"
    # Si en tu usuarios.json agregás "campus": "CAMPUS_A", cambiás esto.

    selected, cost_total, comps, nuevas = conexiones_minimas_campus(
        usuarios=usuarios,
        amistades=amistades,
        campus=campus
    )

    imprimir_resultado(
        usuarios=usuarios,
        aristas_seleccionadas=selected,
        costo_total=cost_total,
        componentes=comps,
        nuevas_conexiones=nuevas,
        campus=campus
    )


if __name__ == "__main__":
    main()
