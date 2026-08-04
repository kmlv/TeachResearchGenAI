# Live demo de Lean en VS Code

Esta carpeta contiene un demo reproducible de 8:30–9:45 minutos para una
audiencia que nunca ha visto Lean. El archivo visible es `DemoEnVivo.lean`; los
seis archivos bajo `estados/` permiten recuperar cada momento del relato.

Desde `course/exercises/lean_verification_demo/`:

```bash
./live_demo/preparar.sh 00
./live_demo/verificar_live_demo.sh
```

Después abra **esa carpeta padre** en VS Code y siga `GUION.md`. No abra solo
`live_demo/`: la carpeta padre contiene las versiones fijadas de Lean y Mathlib.

Estados disponibles:

| Estado | Propósito | Resultado esperado |
|---:|---|---|
| `00` | caso inicial mínimo | verde |
| `10` | confundir conteos con tasas | rojo: `Type mismatch` |
| `15` | una táctica busca y no encuentra prueba | rojo: `linarith failed to find a contradiction` |
| `20` | contraejemplo 2/100 frente a 1/10 | verde |
| `30` | mismo denominador positivo | verde |
| `40` | mezcla entre extremos | verde |

`preparar.sh` también acepta los nombres `verde`, `rojo`, `busqueda`,
`contraejemplo`, `reparacion` y `mezcla`. Cada ejecución reemplaza únicamente
`live_demo/DemoEnVivo.lean` por la copia exacta del estado elegido.

Los dos textos de error se verifican literalmente y están fijados al
`lean-toolchain` del proyecto, Lean **v4.31.0**. Si se actualiza esa versión, se
deben volver a observar los diagnósticos antes de modificar el arnés.

El demo no usa `sorry` ni `axiom`. Hereda `lean-toolchain`, `lakefile.toml` y
`lake-manifest.json` del ejercicio padre; no introduce dependencias nuevas.
