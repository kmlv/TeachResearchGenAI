import Mathlib

theorem sumar_lo_mismo_conserva_el_orden (x y c : ℝ)
    (h : x < y) :
    x + c < y + c := by
  linarith

theorem contraejemplo_mas_casos_menor_tasa :
    (1 : ℝ) < 2 ∧
    (10 : ℝ) < 100 ∧
    ¬ ((1 : ℝ) / 10 < (2 : ℝ) / 100) := by
  norm_num

theorem misma_poblacion_mayor_tasa
    (casosA casosB poblacion : ℝ)
    (hpob : 0 < poblacion)
    (hcasos : casosB < casosA) :
    casosB / poblacion < casosA / poblacion := by
  gcongr

/-!
Puente algebraico, no una formalización completa de loterías: si a es un peso
entre 0 y 1, la mezcla de x e y no sale del intervalo entre ambos.
-/

theorem mezcla_entre_extremos (x y a : ℝ)
    (hxy : x ≤ y) (ha0 : 0 ≤ a) (ha1 : a ≤ 1) :
    x ≤ a * x + (1 - a) * y ∧
      a * x + (1 - a) * y ≤ y := by
  constructor <;> nlinarith
