import Mathlib

/-!
Puente elemental hacia el ejemplo de Disentangling.

Si `x ≤ y` y `a` esta entre cero y uno, el promedio ponderado
`a * x + (1 - a) * y` queda entre `x` e `y`.
-/

theorem mezcla_entre_extremos (x y a : ℝ)
    (hxy : x ≤ y) (ha0 : 0 ≤ a) (ha1 : a ≤ 1) :
    x ≤ a * x + (1 - a) * y ∧
      a * x + (1 - a) * y ≤ y := by
  constructor <;> nlinarith
