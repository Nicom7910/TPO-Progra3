import json
import os
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

NEG_INF = -10**18


@dataclass(frozen=True)
class Usuario:
    id: int
    nombre: str
    apellido: str
    intereses: List[str]
    tiempo_max: int


@dataclass(frozen=True)
class Anuncio:
    id: int
    categoria: str
    costo: int    # costo por mostrar a UN usuario
    alcance_base: float    # alcance potencial base
    duracion: int    # tiempo consumido en el feed



# Carga de datos

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
                intereses=list(u["intereses"]),
                tiempo_max=int(u["tiempo_max"]),
            )
        )
    return usuarios


def cargar_anuncios(path: str) -> List[Anuncio]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    anuncios: List[Anuncio] = []
    for a in data:
        anuncios.append(
            Anuncio(
                id=int(a["id"]),
                categoria=str(a["categoria"]),
                costo=int(a["costo"]),
                alcance_base=float(a["alcance_base"]),
                duracion=int(a["duracion"]),
            )
        )
    return anuncios

def generar_preferencias(
    usuarios: List[Usuario],
    anuncios: List[Anuncio],
    pref_match: float = 1.0,
    pref_no_match: float = 0.3
) -> List[List[float]]:
    """
    Preferencia(u, anuncio) en base al perfil:
      - si categoria del anuncio ∈ intereses del usuario => pref_match
      - sino => pref_no_match
    """
    prefs: List[List[float]] = []
    for u in usuarios:
        set_int = set(u.intereses)
        fila = []
        for ad in anuncios:
            fila.append(pref_match if ad.categoria in set_int else pref_no_match)
        prefs.append(fila)
    return prefs


def _knapsack_usuario_2d(
    anuncios: List[Anuncio],
    prefs_u: List[float],
    tiempo_max: int,
    presupuesto_max: int
) -> Tuple[
    List[float],
    List[int],
    List[List[float]],
    List[List[Optional[Tuple[int, int, int]]]]
]:
    """
    Para un usuario u:
      dp[t][b] = mejor valor con tiempo exacto t y presupuesto exacto b

    Valor de anuncio i para el usuario:
      anuncios[i].alcance_base * prefs_u[i]

    Devuelve:
      - best_por_b[b]: mejor valor para ese presupuesto b (maximizando sobre t)
      - best_t_por_b[b]: el tiempo t que logra best_por_b[b]
      - dp y parent para reconstrucción
    """

    n = len(anuncios)

    # Validación: debe haber una preferencia por cada anuncio
    if len(prefs_u) != n:
        raise ValueError("prefs_u debe tener longitud = cantidad de anuncios.")

    T = tiempo_max
    B = presupuesto_max

    # Inicializamos dp con -infinito (estado imposible), evita combinaciones inválidas
    dp = [[NEG_INF] * (B + 1) for _ in range(T + 1)]

    # parent[t][b] guarda (t_prev, b_prev, i) si se llegó tomando el anuncio i
    parent: List[List[Optional[Tuple[int, int, int]]]] = [
        [None] * (B + 1) for _ in range(T + 1)
    ]

    # Caso base: sin tiempo y sin presupuesto → valor 0
    dp[0][0] = 0.0

    # Recorremos cada anuncio (knapsack 0/1)
    for i, ad in enumerate(anuncios):

        c = ad.costo          # consumo de presupuesto
        d = ad.duracion       # consumo de tiempo
        v = ad.alcance_base * prefs_u[i]  # valor ponderado para este usuario

        # Recorremos hacia atrás para que sea 0/1 (no reutilizar el mismo anuncio)
        for t in range(T, d - 1, -1):
            for b in range(B, c - 1, -1):

                # Si el estado previo es imposible, no podemos usar este anuncio
                if dp[t - d][b - c] == NEG_INF:
                    continue

                # Candidato: tomar el anuncio i
                cand = dp[t - d][b - c] + v

                # Si mejora el valor actual, actualizamos
                if cand > dp[t][b]:
                    dp[t][b] = cand
                    # Guardamos desde dónde venimos y qué anuncio tomamos
                    parent[t][b] = (t - d, b - c, i)

    # Para cada presupuesto b, buscamos el mejor valor maximizando sobre el tiempo
    best_por_b = [0.0] * (B + 1)
    best_t_por_b = [0] * (B + 1)

    for b in range(B + 1):
        mejor_val = 0.0
        mejor_t = 0

        # Buscamos el mejor tiempo t para este presupuesto exacto b
        for t in range(T + 1):
            if dp[t][b] > mejor_val:
                mejor_val = dp[t][b]
                mejor_t = t

        best_por_b[b] = mejor_val
        best_t_por_b[b] = mejor_t

    return best_por_b, best_t_por_b, dp, parent


def _reconstruir(parent: List[List[Optional[Tuple[int, int, int]]]], t_fin: int, b_fin: int) -> List[int]:
    """Devuelve índices (posición en la lista anuncios) elegidos para el usuario desde (t_fin, b_fin)."""
    elegidos: List[int] = []
    t, b = t_fin, b_fin
    while True:
        p = parent[t][b]
        if p is None:
            break
        prev_t, prev_b, idx_ad = p
        elegidos.append(idx_ad)
        t, b = prev_t, prev_b
    elegidos.reverse()
    return elegidos


def asignar_anuncios_maximizando_alcance(
    usuarios: List[Usuario],
    anuncios: List[Anuncio],
    presupuesto_total: int,
    pref_match: float = 1.0,
    pref_no_match: float = 0.3
) -> Tuple[float, Dict[int, List[int]], Dict[int, int]]:
    """
    Asigna anuncios a usuarios maximizando alcance total ponderado por perfil,
    sin exceder el presupuesto_total y respetando tiempo_max por usuario.

    Devuelve:
      - mejor_alcance_total
      - asignacion: dict {usuario_id: [anuncio_id, ...]}
      - presupuesto_asignado: dict {usuario_id: presupuesto_asignado}
    """
    U = len(usuarios)
    B = presupuesto_total
    if B < 0:
        raise ValueError("presupuesto_total debe ser >= 0")

    # preferencia(u,i) según intereses
    preferencias = generar_preferencias(usuarios, anuncios, pref_match=pref_match, pref_no_match=pref_no_match)

    # 1) DP por usuario: best_u[u][b] = mejor valor si asigno b presupuesto al usuario u
    best_u: List[List[float]] = []
    best_t_u: List[List[int]] = []
    # guardamos dp/parent para reconstruir sin recalcular
    dp_u: List[List[List[float]]] = []
    parent_u: List[List[List[Optional[Tuple[int, int, int]]]]] = []

    for u_idx in range(U):
        best_b, best_t, dp, parent = _knapsack_usuario_2d(
            anuncios=anuncios,
            prefs_u=preferencias[u_idx],
            tiempo_max=usuarios[u_idx].tiempo_max,
            presupuesto_max=B
        )
        best_u.append(best_b)
        best_t_u.append(best_t)
        dp_u.append(dp)
        parent_u.append(parent)

    # 2) DP global de reparto de presupuesto: dp_prev[b] = mejor usando usuarios procesados
    dp_prev = [NEG_INF] * (B + 1)
    dp_prev[0] = 0.0

    # parent_global[u][b] = cuánto asigné al usuario u-1 para llegar al óptimo en dp[u][b]
    parent_global = [[0] * (B + 1) for _ in range(U + 1)]

    for u in range(1, U + 1):
        dp_cur = [NEG_INF] * (B + 1)
        for b_total in range(B + 1):
            mejor_val = NEG_INF
            mejor_bu = 0
            for b_u in range(b_total + 1):
                if dp_prev[b_total - b_u] == NEG_INF:
                    continue
                cand = dp_prev[b_total - b_u] + best_u[u - 1][b_u]
                if cand > mejor_val:
                    mejor_val = cand
                    mejor_bu = b_u
            dp_cur[b_total] = mejor_val
            parent_global[u][b_total] = mejor_bu
        dp_prev = dp_cur

    mejor_total = dp_prev[B]

    # reconstruir presupuesto por usuario
    presupuesto_asignado: List[int] = [0] * U
    b = B
    for u in range(U, 0, -1):
        b_u = parent_global[u][b]
        presupuesto_asignado[u - 1] = b_u
        b -= b_u

    # reconstruir anuncios por usuario usando (dp_u, parent_u)
    asignacion_por_usuario: List[List[int]] = []
    for u_idx in range(U):
        b_u = presupuesto_asignado[u_idx]
        t_u = best_t_u[u_idx][b_u]
        idx_elegidos = _reconstruir(parent_u[u_idx], t_u, b_u)
        asignacion_por_usuario.append([anuncios[i].id for i in idx_elegidos])

    asignacion = {usuarios[i].id: asignacion_por_usuario[i] for i in range(U)}
    presupuesto_dict = {usuarios[i].id: presupuesto_asignado[i] for i in range(U)}
    return mejor_total, asignacion, presupuesto_dict


def imprimir_resultados(
    usuarios: List[Usuario],
    anuncios: List[Anuncio],
    asignacion: Dict[int, List[int]],
    presupuesto_asignado: Dict[int, int],
    pref_match: float = 1.0,
    pref_no_match: float = 0.3,
):
    anuncios_por_id = {a.id: a for a in anuncios}
    prefs = generar_preferencias(usuarios, anuncios, pref_match=pref_match, pref_no_match=pref_no_match)

    # mapa id->index para poder recuperar pref correctamente aunque ids no sean 0..n-1
    idx_por_id = {a.id: i for i, a in enumerate(anuncios)}

    total_costo = 0
    total_val = 0.0

    print("\n=== Asignación de Publicidad (Red Social) ===")
    for u_idx, u in enumerate(usuarios):
        ads_ids = asignacion.get(u.id, [])
        b_u = presupuesto_asignado.get(u.id, 0)

        costo_u = 0
        tiempo_u = 0
        val_u = 0.0

        print(f"\nUsuario {u.id}: {u.nombre} {u.apellido}")
        print("Intereses:", u.intereses)
        print("Tiempo máximo:", u.tiempo_max, "| Presupuesto asignado:", b_u)
        print("Anuncios asignados:", ads_ids)

        for ad_id in ads_ids:
            ad = anuncios_por_id[ad_id]
            i = idx_por_id[ad_id]
            pref = prefs[u_idx][i]
            valor = ad.alcance_base * pref

            costo_u += ad.costo
            tiempo_u += ad.duracion
            val_u += valor

            print(f"  - Anuncio sobre {ad.categoria}: costo={ad.costo}, dur={ad.duracion}, pref={pref}, valor={valor:.2f}")

        print("Totales usuario -> costo:", costo_u, "tiempo:", tiempo_u, "alcance:", round(val_u, 2))

        total_costo += costo_u
        total_val += val_u

    print("\n=== Totales globales ===")
    print("Costo total:", total_costo)
    print("Alcance total:", round(total_val, 2))


def main():
    usuarios_path = "usuarios.json"
    anuncios_path = "anuncios.json"

    usuarios = cargar_usuarios(usuarios_path)
    anuncios = cargar_anuncios(anuncios_path)

    presupuesto_total = 7

    # Preferencias por perfil (coincidencia de intereses)
    pref_match = 1.0
    pref_no_match = 0.3

    mejor_total, asignacion, presupuesto_asignado = asignar_anuncios_maximizando_alcance(
        usuarios=usuarios,
        anuncios=anuncios,
        presupuesto_total=presupuesto_total,
        pref_match=pref_match,
        pref_no_match=pref_no_match
    )

    print("Presupuesto total:", presupuesto_total)
    print("Alcance máximo total:", round(mejor_total, 2))

    imprimir_resultados(
        usuarios=usuarios,
        anuncios=anuncios,
        asignacion=asignacion,
        presupuesto_asignado=presupuesto_asignado,
        pref_match=pref_match,
        pref_no_match=pref_no_match
    )


if __name__ == "__main__":
    main()
