import Mathlib

theorem sumar_lo_mismo_conserva_el_orden (x y c : ℝ)
    (h : x < y) :
    x + c < y + c := by
  linarith

/-!
A tiene 2 casos entre 100 personas; B tiene 1 caso entre 10 personas.
A tiene más casos y más población, pero no mayor tasa.
-/

theorem contraejemplo_mas_casos_menor_tasa :
    (1 : ℝ) < 2 ∧
    (10 : ℝ) < 100 ∧
    ¬ ((1 : ℝ) / 10 < (2 : ℝ) / 100) := by
  norm_num
