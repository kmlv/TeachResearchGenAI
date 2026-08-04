#!/usr/bin/env bash
set -euo pipefail

demo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$demo_dir/.." && pwd)"
cd "$project_dir"

green_files=(
  live_demo/DemoEnVivo.lean
  live_demo/estados/00_verde.lean
  live_demo/estados/20_contraejemplo.lean
  live_demo/estados/30_reparacion.lean
  live_demo/estados/40_mezcla.lean
)

for file in "${green_files[@]}"; do
  echo "VERDE  $file"
  lake env lean "$file"
done

expect_failure() {
  local file="$1"
  local expected_fragment="$2"
  local label="$3"

  echo "ROJO   $file ($label; fallo esperado)"
  set +e
  local failure_output
  failure_output="$(lake env lean "$file" 2>&1)"
  local failure_status=$?
  set -e

  if [[ $failure_status -eq 0 ]]; then
    echo "ERROR: $file fue aceptado; dejó de representar el rechazo esperado."
    exit 1
  fi

  if [[ "$failure_output" != *"$expected_fragment"* ]]; then
    echo "ERROR: $file falló con un diagnóstico inesperado."
    echo "Fragmento esperado: $expected_fragment"
    printf '%s\n' "$failure_output"
    exit 1
  fi
}

# Estos fragmentos se observaron con el lean-toolchain fijado en v4.31.0.
# Si el proyecto actualiza la versión, hay que recapturarlos antes de cambiarlos.
expect_failure \
  "live_demo/estados/10_rojo.lean" \
  "Type mismatch" \
  "objeto ofrecido de tipo incorrecto"
expect_failure \
  "live_demo/estados/15_busqueda_falla.lean" \
  "linarith failed to find a contradiction" \
  "búsqueda de táctica sin prueba"

echo "OK: cinco archivos verdes y dos errores rojos deliberados verificados."
