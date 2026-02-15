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

### Código fuente

- `main.py` - Menú principal que integra todos los ejercicios
- `alcance_vfinal.py` - Algoritmo greedy para maximizar cobertura de usuarios
- `red_minima_kruskal.py` - Algoritmo de Kruskal para MST
- `bloqueos_kruskal.py` - Simulación de bloqueos y reconexión

### Datos de entrada

- `usuarios.json` - Lista de usuarios del campus
- `amistades.json` - Conexiones posibles entre usuarios con sus costos

### Documentación

- `Informe_Asignacion_Alcance.txt` - Informe del ejercicio de publicidad
- `Informe_Red_Minima_Kruskal.txt` - Informe del ejercicio de conectividad mínima
- `bloqueos.txt` - Informe del ejercicio de bloqueos

## Requisitos

- Python 3.7 o superior
- No requiere dependencias externas

## Algoritmos implementados

1. **Greedy por eficiencia marginal** - Para maximización de cobertura con presupuesto
2. **Kruskal con Union-Find (DSU)** - Para árbol de expansión mínima
3. **Detección de componentes conexas** - Para análisis de bloqueos y reconexión
