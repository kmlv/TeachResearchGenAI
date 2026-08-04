import Mathlib

theorem sumar_lo_mismo_conserva_el_orden (x y c : ℝ)
    (h : x < y) :
    x + c < y + c := by
  linarith

/-!
La táctica ahora intenta buscar una prueba aritmética. El intento falla, pero
eso por sí solo todavía no demuestra que el enunciado sea falso.
-/

theorem mas_casos_implica_mayor_tasa
    (casosA casosB pobA pobB : ℝ)
    (hA : 0 < pobA) (hB : 0 < pobB)
    (hcasos : casosB < casosA)
    (hpob : pobB < pobA) :
    casosB / pobB < casosA / pobA := by
  linarith
