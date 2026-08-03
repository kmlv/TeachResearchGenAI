import Mathlib

/-!
Demo principal: una afirmacion plausible que Lean rechaza.

Para producir el momento rojo en vivo, quite `/-` y `-/` solo del primer
bloque. Lean mostrara que una desigualdad entre conteos no tiene el tipo de la
desigualdad entre tasas que se quiere demostrar.
-/

/-
theorem incidencia_mayor (casosA casosB pobA pobB : ℝ)
    (hA : 0 < pobA) (hB : 0 < pobB)
    (hcasos : casosB < casosA) (hpob : pobB < pobA) :
    casosB / pobB < casosA / pobA := by
  exact hcasos
-/

/-!
Lean no solo deja de encontrar una prueba: tambien acepta una refutacion.
Con A = (2 casos, 100 personas) y B = (1 caso, 10 personas), A tiene mas
casos y mas poblacion, pero menor incidencia.
-/

theorem incidencia_mayor_es_falsa :
    ¬ ∀ casosA casosB pobA pobB : ℝ,
        0 < pobA → 0 < pobB →
        casosB < casosA → pobB < pobA →
        casosB / pobB < casosA / pobA := by
  intro h
  have hcontra := h 2 1 100 10 (by norm_num) (by norm_num)
    (by norm_num) (by norm_num)
  norm_num at hcontra

/-!
La reparacion cambia el enunciado: compara tasas con el mismo denominador.
El supuesto de comparabilidad hace el trabajo sustantivo.
-/

theorem incidencia_comparable (casosA casosB pob : ℝ)
    (hpob : 0 < pob) (hcasos : casosB < casosA) :
    casosB / pob < casosA / pob := by
  gcongr
