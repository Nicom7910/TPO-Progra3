from dataclasses import dataclass
from random import Random
from typing import List


# =========================
#   MODELO DE CONEXIÓN
# =========================
@dataclass(frozen=True)
class Edge:
    u: int
    v: int
    cost: int

    def __str__(self) -> str:
        return f"{self.u} --({self.cost})-- {self.v}"


# =========================
#   UNION-FIND
# =========================
class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False  # formaría ciclo (redundancia)

        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1
        return True


# =========================
#   GENERADOR DE GRAFO
# =========================
def generate_random_graph(
    n_users: int = 10,
    n_edges: int = 18,
    cost_min: int = 1,
    cost_max: int = 10,
    seed: int = 7
) -> List[Edge]:
    """
    Genera un grafo NO dirigido con costos aleatorios.
    - Primero crea un árbol base (asegura conectividad).
    - Luego agrega aristas extra aleatorias.
    """
    rng = Random(seed)
    edges_set = set()

    def add_edge(u: int, v: int):
        if u == v:
            return
        a, b = (u, v) if u < v else (v, u)
        cost = rng.randint(cost_min, cost_max)
        edges_set.add((a, b, cost))

    # Base conectada (árbol)
    for i in range(1, n_users):
        j = rng.randrange(0, i)
        add_edge(i, j)

    # Extra aristas
    tries = 0
    while len(edges_set) < n_edges and tries < 10_000:
        u = rng.randrange(0, n_users)
        v = rng.randrange(0, n_users)
        add_edge(u, v)
        tries += 1

    return [Edge(u, v, c) for (u, v, c) in edges_set]


# =========================
#   KRUSKAL PASO A PASO
# =========================
def kruskal_mst_step_by_step(n_users: int, edges: List[Edge]) -> List[Edge]:
    uf = UnionFind(n_users)
    edges_sorted = sorted(edges, key=lambda e: e.cost)

    mst: List[Edge] = []
    total = 0

    print("\n=== ARISTAS ORDENADAS POR COSTO (Kruskal) ===")
    for e in edges_sorted:
        print(" ", e)

    print("\n=== CONSTRUCCIÓN DEL ÁRBOL DE RECUBRIMIENTO MÍNIMO ===")
    for e in edges_sorted:
        if uf.union(e.u, e.v):
            mst.append(e)
            total += e.cost
            print(f"\n✅ Se agrega: {e}")
            print(f"   MST actual ({len(mst)} aristas, costo={total}):")
            for x in mst:
                print("    ", x)
            if len(mst) == n_users - 1:
                break
        else:
            print(f"❌ Se rechaza (ciclo): {e}")

    if len(mst) != n_users - 1:
        raise ValueError("No se pudo conectar toda la red con las conexiones disponibles.")

    print("\n=== RESULTADO FINAL ===")
    print(f"Aristas en el MST: {len(mst)} (debe ser {n_users-1})")
    print(f"Costo total mínimo: {total}")

    return mst


# =========================
#   MAIN
# =========================
def main():
    n_users = 10
    n_edges = 18  # grafo "completo" en sentido de "todas las conexiones simuladas" (no necesariamente K10)
    seed = 7

    edges = generate_random_graph(
        n_users=n_users,
        n_edges=n_edges,
        cost_min=1,
        cost_max=10,
        seed=seed
    )

    print("=== GRAFO COMPLETO SIMULADO (todas las conexiones generadas) ===")
    print(f"Usuarios: {n_users} (IDs 0..{n_users-1})")
    print(f"Conexiones generadas: {len(edges)} (seed={seed}, costo 1..10)\n")
    for e in sorted(edges, key=lambda x: (x.u, x.v, x.cost)):
        print(" ", e)

    kruskal_mst_step_by_step(n_users, edges)


if __name__ == "__main__":
    main()
