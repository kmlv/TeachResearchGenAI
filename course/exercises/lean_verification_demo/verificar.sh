#!/usr/bin/env bash
set -euo pipefail

demo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$demo_dir"

lake env lean Incidencia.lean
lake env lean PrimerPaso.lean
lake env lean MezclaEntreExtremos.lean
lake env lean ExtensionInyectividad.lean
lake env lean PuenteDisentangling.lean

set +e
red_output="$(lake env lean IncidenciaRojo.lean 2>&1)"
red_status=$?
set -e

if [[ $red_status -eq 0 ]]; then
  echo "ERROR: IncidenciaRojo.lean compiló; el momento rojo dejó de ser rojo."
  exit 1
fi

if [[ "$red_output" != *"Type mismatch"* ]]; then
  echo "ERROR: IncidenciaRojo.lean falló con un mensaje inesperado."
  printf '%s\n' "$red_output"
  exit 1
fi

echo "Lean: cinco artefactos aceptados y el rechazo deliberado verificado."
