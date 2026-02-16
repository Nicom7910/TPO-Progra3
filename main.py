#!/usr/bin/env python3
"""
TPO Programación 3 - Red Social
===============================
Menú principal para ejecutar los diferentes ejercicios del trabajo práctico.

Ejercicios disponibles:
1. Asignación de Publicidad: Maximizando Alcance
2. Red de Amistades: Mínima Conectividad (Kruskal MST)
3. Simulación de Bloqueos y Conexiones Alternativas
"""
import os
import sys
from pathlib import Path


def clear_screen():
    """Limpia la pantalla de la terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    """Pausa hasta que el usuario presione Enter."""
    input("\n⏎ Presiona Enter para continuar...")


def print_header():
    """Muestra el encabezado del menú."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "TPO PROGRAMACIÓN 3 - RED SOCIAL" + " " * 14 + "║")
    print("║" + " " * 20 + "Menú Principal" + " " * 24 + "║")
    print("╚" + "═" * 58 + "╝")
    print()


def print_menu():
    """Muestra las opciones del menú."""
    print("┌" + "─" * 58 + "┐")
    print("│  EJERCICIOS DISPONIBLES:" + " " * 33 + "│")
    print("├" + "─" * 58 + "┤")
    print("│  1. Ejercicio 2: Asignación de Publicidad               │")
    print("│  2. Ejercicio 3: Red de Amistades - Mínima Conectividad │")
    print("│  3. Ejercicio Opcional 1: Simulación de Bloqueos        │")
    print("├" + "─" * 58 + "┤")
    print("│  0. Salir                                               │")
    print("└" + "─" * 58 + "┘")
    print()


def run_alcance():
    """Ejecuta el ejercicio de Asignación de Publicidad: Maximizando Alcance."""
    print("\n" + "=" * 60)
    print("  EJERCICIO 2: ASIGNACIÓN DE PUBLICIDAD - MAXIMIZANDO ALCANCE")
    print("=" * 60)
    print("\nEste ejercicio maximiza la cobertura de usuarios")
    print("seleccionando categorías de interés con un presupuesto")
    print("limitado (algoritmo Greedy con fracciones).")
    print()
    
    try:
        from EJ_2.alcance_vfinal import simular_red_social, indexar_usuarios_por_interes, greedy_max_cobertura_con_fracciones
        
        try:
            presupuesto = input("Presupuesto máximo (default=300): ").strip()
            presupuesto = int(presupuesto) if presupuesto else 300
        except ValueError:
            presupuesto = 300
        
        users, intereses = simular_red_social()
        idx = indexar_usuarios_por_interes(users, len(intereses))
        greedy_max_cobertura_con_fracciones(intereses, idx, presupuesto, len(users))
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


def run_red_minima():
    """Ejecuta el ejercicio de Red de Amistades: Mínima Conectividad."""
    print("\n" + "=" * 60)
    print("  EJERCICIO 3: RED DE AMISTADES - MÍNIMA CONECTIVIDAD")
    print("=" * 60)
    print("\nEste ejercicio encuentra el conjunto mínimo de conexiones")
    print("necesarias para conectar a todos los usuarios del campus,")
    print("minimizando el costo total (Algoritmo de Kruskal / MST).")
    print()
    
    try:
        from EJ_3.red_minima_kruskal import run
        data_dir = Path(".")
        
        modo = input("¿Modo detallado? (s/n, default=s): ").strip().lower()
        verbose = modo != 'n'
        
        run(data_dir, verbose=verbose)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


def run_bloqueos():
    """Ejecuta el ejercicio de Simulación de Bloqueos."""
    print("\n" + "=" * 60)
    print("  EJERCICIO OPCIONAL 1: SIMULACIÓN DE BLOQUEOS Y CONEXIONES")
    print("  ALTERNATIVAS")
    print("=" * 60)
    print("\nEste ejercicio simula qué pasa cuando se elimina una")
    print("conexión (bloqueo) y propone nuevas conexiones para")
    print("mantener la red conectada.")
    print()
    
    try:
        from EJ_1_Opcional.bloqueos_kruskal import run
        data_dir = Path(".")
        
        print("Ingresa los IDs de los usuarios a bloquear:")
        try:
            block_u = input("  ID usuario 1 (Enter para demo): ").strip()
            block_v = input("  ID usuario 2 (Enter para demo): ").strip()
            
            block_u = int(block_u) if block_u else None
            block_v = int(block_v) if block_v else None
        except ValueError:
            print("  → Usando valores demo")
            block_u, block_v = None, None
        
        modo = input("¿Modo resumido? (s/n, default=n): ").strip().lower()
        simple = modo == 's'
        
        run(data_dir, block_u, block_v, simple=simple)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


def main():
    """Función principal del menú."""
    # Asegurar que estamos en el directorio correcto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        opcion = input("Selecciona una opción: ").strip()
        
        if opcion == '0':
            print("\n👋 ¡Hasta luego!")
            sys.exit(0)
        elif opcion == '1':
            run_alcance()
        elif opcion == '2':
            run_red_minima()
        elif opcion == '3':
            run_bloqueos()
        else:
            print("\n⚠️ Opción no válida. Intenta de nuevo.")
        
        pause()


if __name__ == "__main__":
    main()
