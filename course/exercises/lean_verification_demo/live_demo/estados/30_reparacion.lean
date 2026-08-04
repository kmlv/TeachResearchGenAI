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

/-!
La reparación no fuerza una prueba del teorema anterior: cambia el contrato.
Con el mismo denominador positivo, sí se conserva el orden.
-/

theorem misma_poblacion_mayor_tasa
    (casosA casosB poblacion : ℝ)
    (hpob : 0 < poblacion)
    (hcasos : casosB < casosA) :
    casosB / poblacion < casosA / poblacion := by
  gcongr
