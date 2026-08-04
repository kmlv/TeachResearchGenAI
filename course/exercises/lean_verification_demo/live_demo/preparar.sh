#!/usr/bin/env bash
set -euo pipefail

demo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
state="${1:-00}"

case "$state" in
  00|verde) source_file="00_verde.lean" ;;
  10|rojo) source_file="10_rojo.lean" ;;
  15|busqueda) source_file="15_busqueda_falla.lean" ;;
  20|contraejemplo) source_file="20_contraejemplo.lean" ;;
  30|reparacion) source_file="30_reparacion.lean" ;;
  40|mezcla) source_file="40_mezcla.lean" ;;
  *)
    echo "Uso: ./live_demo/preparar.sh {00|10|15|20|30|40}"
    echo "Nombres equivalentes: verde, rojo, busqueda, contraejemplo, reparacion, mezcla"
    exit 2
    ;;
esac

cp "$demo_dir/estados/$source_file" "$demo_dir/DemoEnVivo.lean"
echo "Estado $state preparado en live_demo/DemoEnVivo.lean"
echo "Abra la carpeta lean_verification_demo en VS Code y espere el indicador verde."
