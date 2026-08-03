import Mathlib

/-!
Este archivo debe fallar. `verificar.sh` comprueba que Lean siga rechazando el
paso con un error de tipo. Para la presentacion, el mismo bloque se descomenta
en `Incidencia.lean`, donde queda junto al contraejemplo y la reparacion.
-/

theorem incidencia_mayor (casosA casosB pobA pobB : ℝ)
    (hA : 0 < pobA) (hB : 0 < pobB)
    (hcasos : casosB < casosA) (hpob : pobB < pobA) :
    casosB / pobB < casosA / pobA := by
  exact hcasos
