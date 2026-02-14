from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
import random


@dataclass(frozen=True)
class User:
    id: int
    intereses: Set[int]

@dataclass(frozen=True)
class Interes:
    id: int
    nombre: str
    costo: int


def simular_red_social(
    n_users: int = 1000,
    seed: int = 5

) -> Tuple[List[User], List[Interes]]:

    rng = random.Random(seed)

    nombres_intereses = [
        "Deportes", "Tecnología", "Salud", "Finanzas", "Viajes",
        "Moda", "Música", "Gaming", "Educación", "Cine", "Programación",
        "Cocina", "Fitness", "Autos", "Política", "Arte",
        "Ciencia", "Mascotas", "Inversiones", "Marketing"
    ]

    # Costos grandes y aleatorios
    intereses = [
        Interes(i, nombre, rng.randint(40, 400))
        for i, nombre in enumerate(nombres_intereses)
    ]

    users: List[User] = []
    for uid in range(n_users):
        k = rng.randint(1, 5)
        its = set(rng.sample(range(len(intereses)), k))
        users.append(User(uid, its))

    return users, intereses


def indexar_usuarios_por_interes(users: List[User], n_intereses: int) -> Dict[int, Set[int]]:
    idx: Dict[int, Set[int]] = {i: set() for i in range(n_intereses)}
    for u in users:
        for it in u.intereses:
            idx[it].add(u.id)
    return idx


def greedy_max_cobertura(
    intereses: List[Interes],
    usuarios_por_interes: Dict[int, Set[int]],
    presupuesto_max: int,
    total_usuarios: int
) -> None:

    restantes = set(i.id for i in intereses)
    interes_by_id = {i.id: i for i in intereses}

    costo_total = 0
    alcanzados: Set[int] = set()

    print("\nIntereses disponibles:")
    for i in intereses:
        print(f"{i.id:02d} - {i.nombre:15s} | Costo: {i.costo}")

    print("\n--- Selección Greedy ---\n")

    paso = 1
    while True:
        mejor_id = None
        mejor_ratio = 0.0
        mejor_nuevos = 0

        for iid in list(restantes):
            it = interes_by_id[iid]

            if costo_total + it.costo > presupuesto_max:
                continue

            nuevos = usuarios_por_interes[iid] - alcanzados
            ganancia = len(nuevos)
            if ganancia <= 0:
                continue

            ratio = ganancia / it.costo
            if ratio > mejor_ratio:
                mejor_ratio = ratio
                mejor_id = iid
                mejor_nuevos = ganancia

        if mejor_id is None:
            break

        it = interes_by_id[mejor_id]
        costo_total += it.costo
        alcanzados |= usuarios_por_interes[mejor_id]
        restantes.remove(mejor_id)

        cobertura = 100 * len(alcanzados) / total_usuarios

        print(
            f"[Paso {paso}] "
            f"{it.nombre:15s} | "
            f"Costo {it.costo:3d} | "
            f"Usuarios nuevos {mejor_nuevos:4d} | "
            f"Total {len(alcanzados):4d}/{total_usuarios} ({cobertura:5.1f}%) | "
            f"Presupuesto {costo_total}/{presupuesto_max}"
        )

        paso += 1

    print("\n--- RESULTADO FINAL ---")
    print("Presupuesto máximo:", presupuesto_max)
    print("Presupuesto usado:", costo_total)
    print("Usuarios alcanzados:", len(alcanzados), "de", total_usuarios)
    print("Cobertura final:", f"{100*len(alcanzados)/total_usuarios:.2f}%")



if __name__ == "__main__":
    users, intereses = simular_red_social()
    idx = indexar_usuarios_por_interes(users, len(intereses))

    presupuesto = 300
    greedy_max_cobertura(intereses, idx, presupuesto, len(users))
