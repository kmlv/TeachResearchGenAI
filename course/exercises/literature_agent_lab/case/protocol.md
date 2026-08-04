# Protocolo congelado antes del cribado

## Incluir

1. Estudio empírico primario con participantes humanos adultos.
2. Mensaje o diálogo persuasivo generado o mediado por un LLM.
3. Comparación pertinente y resultado posterior de actitud, creencia,
   intención o conducta.
4. Publicado o difundido entre 2023 y 2026.

## Excluir

- Evaluaciones donde solo interactúan modelos y las personas únicamente
  califican texto.
- Ensayos conceptuales, reseñas o comentarios sin resultado empírico primario.
- Estudios sin comparador o sin resultado humano posterior a la exposición.

## Estados permitidos en el cribado

- `include`
- `exclude`
- `uncertain`
- `editorial_flag`

`uncertain` y `editorial_flag` son estados terminales del cribado para este
ejercicio: no avanzan solos a extracción ni al brief. Sacar un registro de ese
estado exige una decisión humana nueva.

## Población del protocolo

`adultos`. Una fila de evidencia cuya población declarada sea distinta no puede
entrar al ledger oficial ni al brief, por muy real que sea el pasaje.

## Diseños que habilitan lenguaje causal

- `experimento aleatorizado`
- `experimento de campo aleatorizado`

Cualquier otro diseño obliga a lenguaje asociativo. Esta regla la comprueba un
validador léxico: revisa qué verbos aparecen en la interpretación y qué diseño
declara el paquete de fuentes. El validador no entiende de causalidad; solo
impide que un verbo causal quede sin respaldo de diseño. La decisión sustantiva
sigue siendo humana.

## Regla de decisión

El agente propone. Una persona escribe la decisión final y su razón mediante
`scripts/review_gate.py`. Ninguna frase del chat cuenta como aprobación.

## Regla de parada

El corpus es una muestra didáctica congelada: ocho registros de metadatos
reales para el cribado y cuatro fuentes de entrenamiento para la extracción. No
se declara saturación ni exhaustividad.
