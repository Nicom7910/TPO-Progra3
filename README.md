# TPO Programación 3 - Red Social

## Descripción

Este trabajo práctico implementa soluciones algorítmicas para problemas de optimización en una red social universitaria. El proyecto incluye tres ejercicios principales que abordan diferentes aspectos de la teoría de grafos y algoritmos greedy.

## Ejecución

Para ejecutar el menú principal:

```bash
python3 main.py
```

El menú presenta las siguientes opciones:

| Opción | Ejercicio | Descripción |
|--------|-----------|-------------|
| 1 | Ejercicio 2: Asignación de Publicidad | Maximiza el alcance de usuarios seleccionando categorías de interés con presupuesto limitado |
| 2 | Ejercicio 3: Red de Amistades | Encuentra el conjunto mínimo de conexiones para conectar todos los usuarios (MST con Kruskal) |
| 3 | Ejercicio Opcional 1: Simulación de Bloqueos | Simula la eliminación de conexiones y propone reconexiones mínimas |
| 0 | Salir | Termina la ejecución |

## Estructura de archivos

### Código fuente principal

- `main.py` - Menú principal que integra todos los ejercicios

### Ejercicios

- Carpeta `EJ_2/`
	- `EJ_2/alcance_vfinal.py` - Algoritmo greedy para maximizar la cobertura de usuarios (Asignación de Publicidad)
	- `EJ_2/Informe_Asignacion_Alcance.txt` - Informe teórico del ejercicio de publicidad

- Carpeta `EJ_3/`
	- `EJ_3/red_minima_kruskal.py` - Algoritmo de Kruskal para obtener el Árbol de Expansión Mínima (Red de Amistades)
	- `EJ_3/Informe_Red_Minima_Kruskal.txt` - Informe teórico del ejercicio de conectividad mínima

- Carpeta `EJ_1_Opcional/`
	- `EJ_1_Opcional/bloqueos_kruskal.py` - Simulación de bloqueos y propuesta de reconexiones mínimas
	- `EJ_1_Opcional/Informe_Bloqueos_Kruskal.txt` - Informe teórico del ejercicio opcional de bloqueos

### Datos de entrada

- `usuarios.json` - Lista de usuarios del campus
- `amistades.json` - Conexiones posibles entre usuarios con sus costos

## Requisitos

- Python 3.7 o superior
- No requiere dependencias externas
