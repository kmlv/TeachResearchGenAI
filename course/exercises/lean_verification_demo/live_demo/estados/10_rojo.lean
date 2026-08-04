import Mathlib

theorem sumar_lo_mismo_conserva_el_orden (x y c : ℝ)
    (h : x < y) :
    x + c < y + c := by
  linarith

/-!
Estado rojo deliberado: el supuesto compara conteos, pero la conclusión
compara tasas. Este archivo debe fallar con un error de tipo.
-/

theorem mas_casos_implica_mayor_tasa
    (casosA casosB pobA pobB : ℝ)
    (hA : 0 < pobA) (hB : 0 < pobB)
    (hcasos : casosB < casosA)
    (hpob : pobB < pobA) :
    casosB / pobB < casosA / pobA := by
  exact hcasos
