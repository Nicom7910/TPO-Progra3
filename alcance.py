import json
from dataclasses import dataclass
from typing import List, Tuple, Optional

NEG_INF = -10**18


# =========================
# 1) MODELOS (Red Social)
# =========================

@dataclass(frozen=True)
class UsuarioRS:
    id: int
    nombre: str
    apellido: str
    intereses: List[str]
    tiempo_max: int


@dataclass(frozen=True)
class AnuncioRS:
    id: int
    categoria: str
    costo: int               # costo por impresión (por usuario al que se muestra)
    alcance_base: float
    duracion: int            # tiempo que consume en el feed


# =========================
# 2) CARGA DE JSON
# =========================

def cargar_usuarios(path: str) -> List[UsuarioRS]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    usuarios: List[UsuarioRS] = []
    for u in data:
        usuarios.append(
            UsuarioRS(
                id=u["id"],
                nombre=u["nombre"],
                apellido=u["apellido"],
                intereses=u["intereses"],
                tiempo_max=u["tiempo_max"]
            )
        )
    return usuarios


def cargar_anuncios(path: str) -> List[AnuncioRS]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    anuncios: List[AnuncioRS] = []
    for a in data:
        anuncios.append(
            AnuncioRS(
                id=a["id"],
                categoria=a["categoria"],
                costo=a["costo"],
                alcance_base=float(a["alcance_base"]),
                duracion=a["duracion"]
            )
        )
    return anuncios


# =========================
# 3) PREFERENCIAS (afinidad)
# =========================

def generar_preferencias(
    usuarios: List[UsuarioRS],
    anuncios: List[AnuncioRS],
    pref_match: float = 1.0,
    pref_no_match: float = 0.3
) -> List[List[float]]:
    """
    preferencias[u][i] = afinidad del usuario u con el anuncio i.
    Regla simple:
      - si categoria anuncio ∈ intereses usuario => pref_match
      - si no => pref_no_match
    """
    prefs: List[List[float]] = []
    for u in usuarios:
        fila: List[float] = []
        set_int = set(u.intereses)
        for ad in anuncios:
            fila.append(pref_match if ad.categoria in set_int else pref_no_match)
        prefs.append(fila)
    return prefs


# =========================
# 4) ALGORITMO PRINCIPAL (DP)
#    Costo por usuario / impresión
# =========================

def _knapsack_usuario_2d(
    anuncios: List[AnuncioRS],
    prefs: List[float],
    tiempo_max: int,
    presupuesto_max: int
) -> Tuple[List[float], List[int], List[List[float]], List[List[Optional[Tuple[int, int, int]]]]]:
    """
    Para un usuario:
      dp[t][b] = mejor valor con tiempo exacto t y presupuesto exacto b
    Valor de mostrar anuncio i al usuario:
      alcance_base[i] * pref[u][i]
    Restricciones:
      sum(costo) <= presupuesto_asignado
      sum(duracion) <= tiempo_max
      0/1 por usuario (no repetir el mismo anuncio al mismo usuario)

    Devuelve:
      - best_por_b[b]: mejor valor con presupuesto exacto b (max sobre t)
      - best_t_por_b[b]: t que logra ese mejor valor
      - dp y parent para reconstrucción
    """
    n = len(anuncios)
    if len(prefs) != n:
        raise ValueError("Las preferencias del usuario deben tener longitud n (cantidad de anuncios).")

    T = tiempo_max
    B = presupuesto_max

    dp = [[NEG_INF] * (B + 1) for _ in range(T + 1)]
    parent: List[List[Optional[Tuple[int, int, int]]]] = [[None] * (B + 1) for _ in range(T + 1)]
    dp[0][0] = 0.0

    for i, ad in enumerate(anuncios):
        c = ad.costo
        d = ad.duracion
        v = ad.alcance_base * prefs[i]

        # 0/1 -> recorrer hacia atrás
        for t in range(T, d - 1, -1):
            for b in range(B, c - 1, -1):
                if dp[t - d][b - c] == NEG_INF:
                    continue
                cand = dp[t - d][b - c] + v
                if cand > dp[t][b]:
                    dp[t][b] = cand
                    parent[t][b] = (t - d, b - c, i)

    best_por_b = [0.0] * (B + 1)
    best_t_por_b = [0] * (B + 1)
    for b in range(B + 1):
        mejor_val = 0.0
        mejor_t = 0
        for t in range(T + 1):
            if dp[t][b] > mejor_val:
                mejor_val = dp[t][b]
                mejor_t = t
        best_por_b[b] = mejor_val
        best_t_por_b[b] = mejor_t

    return best_por_b, best_t_por_b, dp, parent


def _reconstruir(parent: List[List[Optional[Tuple[int, int, int]]]], t_fin: int, b_fin: int) -> List[int]:
    """Reconstruye índices (posiciones) de anuncios elegidos para el usuario desde (t_fin, b_fin)."""
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


def asignar_publicidad_multiusuario(
    usuarios: List[UsuarioRS],
    anuncios: List[AnuncioRS],
    preferencias: List[List[float]],
    presupuesto_total: int
) -> Tuple[float, List[List[int]], List[int]]:
    """
    DP multiusuario:
      1) Para cada usuario u: resolver mochila 0/1 con 2 restricciones (tiempo, presupuesto)
         -> best_u[b] = mejor valor para u con presupuesto b.
      2) Repartir el presupuesto total entre usuarios para maximizar suma de best_u[b_u].

    Devuelve:
      - mejor_alcance_total
      - asignacion_por_usuario: lista de IDs de anuncios elegidos por usuario
      - presupuesto_por_usuario: cuánto presupuesto se asignó a cada usuario
    """
    U = len(usuarios)
    n = len(anuncios)
    B = presupuesto_total

    if B < 0:
        raise ValueError("presupuesto_total debe ser >= 0")
    if len(preferencias) != U:
        raise ValueError("preferencias debe tener una fila por usuario.")
    for u in range(U):
        if len(preferencias[u]) != n:
            raise ValueError(f"preferencias[{u}] debe tener longitud n (cantidad de anuncios).")

    # 1) DP por usuario
    best_u: List[List[float]] = []          # best_u[u][b]
    best_t_u: List[List[int]] = []          # best_t_u[u][b]
    parent_u: List[List[List[Optional[Tuple[int, int, int]]]]] = []  # parent por usuario

    for u in range(U):
        best_b, best_t, _, parent = _knapsack_usuario_2d(
            anuncios=anuncios,
            prefs=preferencias[u],
            tiempo_max=usuarios[u].tiempo_max,
            presupuesto_max=B
        )
        best_u.append(best_b)
        best_t_u.append(best_t)
        parent_u.append(parent)

    # 2) DP global para repartir presupuesto: O(U * B^2)
    dp_prev = [NEG_INF] * (B + 1)
    dp_prev[0] = 0.0
    parent_global = [[0] * (B + 1) for _ in range(U + 1)]  # cuánto asigno al usuario u-1

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

    # reconstrucción: presupuesto por usuario
    presupuesto_por_usuario = [0] * U
    b = B
    for u in range(U, 0, -1):
        b_u = parent_global[u][b]
        presupuesto_por_usuario[u - 1] = b_u
        b -= b_u

    # reconstrucción: anuncios por usuario
    asignacion_por_usuario: List[List[int]] = []
    for u in range(U):
        b_u = presupuesto_por_usuario[u]

        # para reconstruir, necesitamos el t que daba el mejor valor con ese b_u
        # recalculamos el dp para el usuario para recuperar dp (solo 1 usuario cada vez),
        # o si querés, lo guardamos (más memoria). Acá recalculo para mantenerlo simple.
        best_b, best_t, dp, parent = _knapsack_usuario_2d(
            anuncios=anuncios,
            prefs=preferencias[u],
            tiempo_max=usuarios[u].tiempo_max,
            presupuesto_max=B
        )
        t_u = best_t[b_u]
        elegidos_idx = _reconstruir(parent, t_u, b_u)
        asignacion_por_usuario.append([anuncios[i].id for i in elegidos_idx])

    return mejor_total, asignacion_por_usuario, presupuesto_por_usuario


# =========================
# 5) MAIN: TODO INTEGRADO
# =========================

def main():
    # Cambiá estos paths según tu estructura
    usuarios_path = "usuarios.json"
    anuncios_path = "anuncios.json"

    presupuesto_total = 7

    usuarios = cargar_usuarios(usuarios_path)
    anuncios = cargar_anuncios(anuncios_path)

    # Preferencias generadas por intereses/categoría
    preferencias = generar_preferencias(usuarios, anuncios, pref_match=1.0, pref_no_match=0.3)

    mejor, asignacion, presup_u = asignar_publicidad_multiusuario(
        usuarios=usuarios,
        anuncios=anuncios,
        preferencias=preferencias,
        presupuesto_total=presupuesto_total
    )

    print("=== RESULTADOS (Maximizando Alcance - Red Social) ===")
    print("Presupuesto total:", presupuesto_total)
    print("Alcance ponderado máximo total:", round(mejor, 2))
    print("Presupuesto asignado por usuario:", presup_u)

    anuncios_por_id = {a.id: a for a in anuncios}

    for idx_u, u in enumerate(usuarios):
        ads_ids = asignacion[idx_u]
        total_costo = 0
        total_t = 0
        total_val = 0.0

        print(f"\nUsuario {u.id}: {u.nombre} {u.apellido}")
        print("Intereses:", u.intereses)
        print("tiempo_max:", u.tiempo_max, "| presupuesto_asignado:", presup_u[idx_u])
        print("Anuncios elegidos:", ads_ids)

        for ad_id in ads_ids:
            ad = anuncios_por_id[ad_id]
            # preferencia del usuario hacia ese anuncio (mismo orden que anuncios)
            pref = preferencias[idx_u][ad_id]  # asumiendo ids 0..n-1
            val = ad.alcance_base * pref

            total_costo += ad.costo
            total_t += ad.duracion
            total_val += val

            print(f"  - ad {ad_id} ({ad.categoria}): costo={ad.costo}, dur={ad.duracion}, pref={pref}, valor={val:.2f}")

        print("Totales -> costo:", total_costo, "tiempo:", total_t, "valor:", round(total_val, 2))


if __name__ == "__main__":
    main()
