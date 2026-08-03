import Mathlib

/-!
Puente pedagogico al proyecto Disentangling.

El lema `expected_mix` de `Independence.lean`, en el proyecto Disentangling,
representa loterias finitas y demuestra que el valor esperado de una mezcla es
la mezcla de los valores esperados. Aqui aislamos solo ese nucleo algebraico
para que se pueda leer y modificar.
-/

open scoped BigOperators

def valorEsperado {n : ℕ} (u p : Fin n → ℝ) : ℝ :=
  ∑ i, p i * u i

def mezcla {n : ℕ} (a : ℝ) (p q : Fin n → ℝ) : Fin n → ℝ :=
  fun i => a * p i + (1 - a) * q i

theorem valorEsperado_mezcla {n : ℕ}
    (u p q : Fin n → ℝ) (a : ℝ) :
    valorEsperado u (mezcla a p q) =
      a * valorEsperado u p + (1 - a) * valorEsperado u q := by
  unfold valorEsperado mezcla
  calc
    (∑ i, (a * p i + (1 - a) * q i) * u i) =
        ∑ i, (a * (p i * u i) + (1 - a) * (q i * u i)) := by
          apply Finset.sum_congr rfl
          intro i _
          ring
    _ = a * (∑ i, p i * u i) + (1 - a) * (∑ i, q i * u i) := by
          simp [Finset.sum_add_distrib, Finset.mul_sum]

/-!
Lean comprobo una identidad sobre numeros reales. Para interpretar `p` y `q`
como probabilidades aun tendriamos que codificar no negatividad y suma uno.
Ese limite es parte de la leccion: lo que no se formaliza no se verifica.
-/
