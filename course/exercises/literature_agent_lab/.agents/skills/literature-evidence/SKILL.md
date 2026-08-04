---
name: literature-evidence
description: Convierte un corpus congelado en un brief de evidencia trazable, con anclaje textual y verificación humana obligatoria.
---

# Cadena de evidencia trazable

Use esta skill cuando exista una pregunta congelada, un protocolo previo y un
paquete de fuentes con localizadores estables.

## Procedimiento

1. **Inventariar antes de opinar.** Liste todos los registros y todas las
   fuentes. No empiece a redactar mientras el inventario esté incompleto.
2. **Cribar con el protocolo, no con la intuición.** Para cada registro,
   proponga un estado permitido y escriba qué criterio lo produjo. Si los
   metadatos no alcanzan, `uncertain` es la respuesta correcta.
3. **Anclar antes de interpretar.** Copie pasaje y localizador exactos. La
   interpretación se escribe después de tener el anclaje, nunca antes.
4. **Elegir el verbo según el diseño.** Aleatorizado admite lenguaje de efecto;
   observacional admite asociación. La diferencia no es de estilo.
5. **Separar población del protocolo de población del estudio.** Una fuente
   real sobre otra población es evidencia equivocada para esta pregunta.
6. **Detenerse en la compuerta.** Presente la fila y la tensión; espere la
   decisión registrada. No la anticipe ni la resuma como si hubiera ocurrido.
7. **Reanudar desde el estado.** Al retomar, lea `STATE.json`, la cola de
   `TRACE.csv` y las tablas; no reconstruya el trabajo desde la conversación.
8. **Ensamblar mecánicamente.** El brief se genera con el script desde el
   ledger. Nunca desde memoria ni desde el borrador que quedó en el chat.

## Cuándo detenerse y preguntar

- El pasaje disponible no cubre la afirmación que haría falta.
- El diseño no permite el verbo que la afirmación necesita.
- Dos fuentes se contradicen y ninguna regla del protocolo decide.
- La pregunta o el protocolo tendrían que cambiar para que el trabajo avance.

En los cuatro casos: registre `blocked` en `STATE.json` y formule la pregunta
mínima que una persona debe responder.
