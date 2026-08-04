import Mathlib

/-! Estado inicial: un contrato pequeño que Lean acepta. -/

theorem sumar_lo_mismo_conserva_el_orden (x y c : ℝ)
    (h : x < y) :
    x + c < y + c := by
  linarith

-- El siguiente bloque se pega aquí.
