from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
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
    n_users: int = 1000
) -> Tuple[List[User], List[Interes]]:

    rng = random.Random()

    nombres_intereses = [
        "Deportes", "Tecnología", "Salud", "Finanzas", "Viajes",
        "Moda", "Música", "Gaming", "Educación", "Cine", "Programación",
        "Cocina", "Fitness", "Autos", "Política", "Arte",
        "Ciencia", "Mascotas", "Inversiones", "Marketing"
    ]

    # Costos grandes y aleatorios (ej: Deportes 100, Tecnología 300, Salud 40, etc.)
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
    """interes_id -> set(user_id)"""
    idx: Dict[int, Set[int]] = {i: set() for i in range(n_intereses)}
    for u in users:
        for it in u.intereses:
            idx[it].add(u.id)
    return idx


def _tomar_subset_deterministico(s: Set[int], k: int, seed: int) -> Set[int]:
    """
    Toma k elementos de un set de forma reproducible (sin depender del orden interno del set).
    """
    if k <= 0:
        return set()
    if k >= len(s):
        return set(s)
    rng = random.Random(seed)
    lista = sorted(s)  # estable
    return set(rng.sample(lista, k))


def _stats_categoria(interes_id: int,
                     usuarios_por_interes: Dict[int, Set[int]],
                     alcanzados: Set[int]) -> Tuple[int, int, float]:
    """
    Devuelve (alcanzados_en_categoria, total_en_categoria, porcentaje)
    """
    total = len(usuarios_por_interes[interes_id])
    if total == 0:
        return 0, 0, 0.0
    alc = len(usuarios_por_interes[interes_id] & alcanzados)
    return alc, total, 100.0 * alc / total


def greedy_max_cobertura_con_fracciones(
    intereses: List[Interes],
    usuarios_por_interes: Dict[int, Set[int]],
    presupuesto_max: int,
    total_usuarios: int,
    tolerancia_no_usar: int = 15,
    seed_fracciones: int = 999
) -> None:
    """
    Greedy por eficiencia (usuarios_nuevos / costo) con presupuesto.
    Mejora:
      - Si al final queda presupuesto "colgado", se permite comprar una FRACCIÓN
        del siguiente interés más eficiente para consumir el restante.

    Interpretación de fracción:
      - f = restante / costo_interes
      - alcanza aprox f * usuarios_nuevos (redondeo hacia abajo)
      - toma un subconjunto determinístico de esos usuarios
    """

    restantes = set(i.id for i in intereses)
    interes_by_id = {i.id: i for i in intereses}

    costo_total = 0
    alcanzados: Set[int] = set()

    print("\nIntereses disponibles:")
    for i in intereses:
        print(f"{i.id:02d} - {i.nombre:15s} | Costo: {i.costo}")

    print("\n--- Selección Greedy ---\n")

    paso = 1

    # -----------------------------
    # FASE 1: solo intereses enteros
    # -----------------------------
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
        alc_cat, total_cat, pct_cat = _stats_categoria(mejor_id, usuarios_por_interes, alcanzados)

        print(
            f"[Paso {paso:02d}] {it.nombre:15s} | "
            f"Costo {it.costo:3d} | "
            f"Usuarios nuevos {mejor_nuevos:4d} | "
            f"Total {len(alcanzados):4d}/{total_usuarios} ({cobertura:5.1f}%) | "
            f"Presupuesto {costo_total}/{presupuesto_max} | "
            f"Cobertura en {it.nombre}: {alc_cat}/{total_cat} ({pct_cat:5.1f}%)"
        )
        paso += 1

    # -----------------------------
    # FASE 2: fracciones (relleno)
    # -----------------------------
    restante = presupuesto_max - costo_total
    if restante > tolerancia_no_usar:

        while restante > tolerancia_no_usar:
            mejor_id = None
            mejor_ratio = 0.0
            mejor_nuevos_set: Optional[Set[int]] = None

            for iid in list(restantes):
                it = interes_by_id[iid]
                nuevos = usuarios_por_interes[iid] - alcanzados
                if not nuevos:
                    continue

                ratio = len(nuevos) / it.costo
                if ratio > mejor_ratio:
                    mejor_ratio = ratio
                    mejor_id = iid
                    mejor_nuevos_set = nuevos

            if mejor_id is None or mejor_nuevos_set is None:
                break

            it = interes_by_id[mejor_id]

            # si entra entero, lo compramos entero
            if it.costo <= restante:
                costo_total += it.costo
                alcanzados |= usuarios_por_interes[mejor_id]
                restantes.remove(mejor_id)
                restante = presupuesto_max - costo_total

                cobertura = 100 * len(alcanzados) / total_usuarios
                alc_cat, total_cat, pct_cat = _stats_categoria(mejor_id, usuarios_por_interes, alcanzados)

                print(
                    f"[Paso {paso:02d}] {it.nombre:15s} | "
                    f"Costo {it.costo:3d} | "
                    f"Usuarios nuevos {len(mejor_nuevos_set):4d} | "
                    f"Total {len(alcanzados):4d}/{total_usuarios} ({cobertura:5.1f}%) | "
                    f"Presupuesto {costo_total}/{presupuesto_max} | "
                    f"Cobertura en {it.nombre}: {alc_cat}/{total_cat} ({pct_cat:5.1f}%)"
                )
                paso += 1
                continue

            # fracción: gasto todo el restante
            gasto = restante
            f = gasto / it.costo

            nuevos_total = len(mejor_nuevos_set)
            nuevos_a_tomar = int(nuevos_total * f)
            if nuevos_a_tomar <= 0:
                break

            subset = _tomar_subset_deterministico(mejor_nuevos_set, nuevos_a_tomar, seed_fracciones + paso)

            costo_total += gasto
            alcanzados |= subset
            restante = presupuesto_max - costo_total

            cobertura = 100 * len(alcanzados) / total_usuarios
            alc_cat, total_cat, pct_cat = _stats_categoria(mejor_id, usuarios_por_interes, alcanzados)

            print(
                f"[Paso {paso:02d}] {it.nombre:15s} | "
                f"Costo {it.costo:3d} | "
                f"FRACCIÓN {f:0.2f} (gasto {gasto}) | "
                f"Usuarios nuevos {len(subset):4d} | "
                f"Total {len(alcanzados):4d}/{total_usuarios} ({cobertura:5.1f}%) | "
                f"Presupuesto {costo_total}/{presupuesto_max} | "
                f"Cobertura en {it.nombre}: {alc_cat}/{total_cat} ({pct_cat:5.1f}%)"
            )
            paso += 1
            break

    print("\n--- RESULTADO FINAL ---")
    print("Presupuesto máximo:", presupuesto_max)
    print("Presupuesto usado :", costo_total)
    print("Restante          :", presupuesto_max - costo_total)
    print("Usuarios alcanzados:", len(alcanzados), "de", total_usuarios)
    print("Cobertura final   :", f"{100*len(alcanzados)/total_usuarios:.2f}%")


if __name__ == "__main__":
    users, intereses = simular_red_social()
    idx = indexar_usuarios_por_interes(users, len(intereses))

    presupuesto = 300
    greedy_max_cobertura_con_fracciones(
        intereses, idx, presupuesto, len(users),
        tolerancia_no_usar=30
    )
