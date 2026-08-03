import Mathlib

/-!
Primer ejemplo verde para leer Lean sin conocimientos previos.

En castellano: si `x` es menor que `y`, sumar el mismo numero `c` a ambos
lados conserva el orden. `linarith` busca una prueba aritmetica y el nucleo de
Lean comprueba el resultado que produce.
-/

theorem sumar_mismo_conserva_orden (x y c : ℝ) (h : x < y) :
    x + c < y + c := by
  linarith
