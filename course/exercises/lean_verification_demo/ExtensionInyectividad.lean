/-!
Extension sin Mathlib: una prueba breve para adaptar despues de la clase.

Si la composicion g o f es inyectiva, entonces f es inyectiva. La conclusion
no puede fortalecerse a que g sea inyectiva: g puede confundir valores que f
nunca alcanza.
-/

theorem composicion_inyectiva_implica_primera_inyectiva
    {α β γ : Type}
    (f : α → β) (g : β → γ)
    (hcomp : Function.Injective (g ∘ f)) :
    Function.Injective f := by
  intro x y hfxfy
  apply hcomp
  exact congrArg g hfxfy

def fUnitBool (_ : Unit) : Bool := false

def gBoolUnit (_ : Bool) : Unit := ()

example : Function.Injective (gBoolUnit ∘ fUnitBool) := by
  intro x y _
  cases x
  cases y
  rfl

example : ¬ Function.Injective gBoolUnit := by
  intro hg
  have hfalse_true : false = true := hg rfl
  cases hfalse_true
