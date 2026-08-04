# Evaluación de recuperación — libros completos

Estado: **aprobado en G4**.

Resultados medidos contra páginas auditadas una por una. Los reportes
contienen solo metadatos; no incluyen texto de los libros.

- Índice: `local_index_full`
- Preguntas: 12
- Qrels positivas: 57
- Qrels negativas explícitas: 58
- Procedencia de las positivas: 38 descubiertas en el pool y 19 sembradas independientemente
- Pool top-5: 123 candidatos únicos; 57 positivos, 60 negativos explícitos y 6 sin juzgar

Kristian aprobó G4 aceptando los candidatos `unjudged` como incompletitud documentada. Para calcular las métricas se tratan como no relevantes, según la convención IR declarada. Como parte del gold set se descubrió desde los recuperadores comparados, las cifras absolutas pueden ser optimistas y la comparación no es plenamente independiente.

| modo | Hit@3 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: |
| lexical | 0.333 | 0.354 | 0.310 |
| dense | 0.917 | 0.792 | 0.584 |
| hybrid | 0.833 | 0.799 | 0.587 |

## Resultado por pregunta

### B01 — ¿Cuáles son las diferencias entre el Sistema 1 y el Sistema 2 en el procesamiento cognitivo?

- lexical: Hit@3 0; RR 0.000; nDCG@5 0.000
- dense: Hit@3 1; RR 1.000; nDCG@5 0.723
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.485

### B02 — ¿Qué evidencia empírica se documenta sobre el 'endowment effect' en transacciones de mercado?

- lexical: Hit@3 1; RR 1.000; nDCG@5 1.000
- dense: Hit@3 1; RR 1.000; nDCG@5 0.553
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.830

### B03 — ¿Cómo demuestra la economía conductual que los consumidores siempre toman decisiones perfectamente racionales?

- lexical: Hit@3 0; RR 0.250; nDCG@5 0.168
- dense: Hit@3 1; RR 1.000; nDCG@5 0.637
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.805

### B04 — ¿De qué manera la aversión a la pérdida (loss aversion) afecta la toma de decisiones bajo riesgo?

- lexical: Hit@3 1; RR 1.000; nDCG@5 0.869
- dense: Hit@3 1; RR 1.000; nDCG@5 0.723
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.786

### E01 — ¿Cuáles son las ventajas metodológicas de la asignación aleatoria en ensayos de campo?

- lexical: Hit@3 0; RR 0.000; nDCG@5 0.000
- dense: Hit@3 1; RR 1.000; nDCG@5 1.000
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.640

### E02 — ¿Qué recomiendan Imbens y Rubin para el diseño de experimentos de laboratorio con estudiantes de pregrado?

- lexical: Hit@3 0; RR 0.000; nDCG@5 0.000
- dense: Hit@3 1; RR 0.500; nDCG@5 0.498
- hybrid: Hit@3 0; RR 0.250; nDCG@5 0.202

### E03 — ¿Cuáles son los supuestos principales —incluida SUTVA— detrás del framework 'potential outcomes'?

- lexical: Hit@3 1; RR 1.000; nDCG@5 1.000
- dense: Hit@3 1; RR 0.500; nDCG@5 0.214
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.869

### E04 — ¿Por qué se recomienda el pago con incentivos monetarios contingentes al desempeño en economía experimental?

- lexical: Hit@3 0; RR 0.000; nDCG@5 0.000
- dense: Hit@3 1; RR 1.000; nDCG@5 0.830
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.509

### G01 — ¿Qué condiciones deben cumplirse para un equilibrio perfecto en subjuegos?

- lexical: Hit@3 0; RR 0.000; nDCG@5 0.000
- dense: Hit@3 1; RR 0.500; nDCG@5 0.387
- hybrid: Hit@3 1; RR 0.333; nDCG@5 0.307

### G02 — ¿Cómo se resuelve analíticamente un juego de negociación de ofertas alternadas infinito?

- lexical: Hit@3 0; RR 0.000; nDCG@5 0.000
- dense: Hit@3 1; RR 1.000; nDCG@5 0.832
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.737

### G03 — ¿Bajo qué circunstancias ocurre una falla de mercado debido a 'adverse selection'?

- lexical: Hit@3 1; RR 1.000; nDCG@5 0.684
- dense: Hit@3 1; RR 1.000; nDCG@5 0.616
- hybrid: Hit@3 1; RR 1.000; nDCG@5 0.869

### G04 — ¿Cómo demuestra Mas-Colell que todos los juegos de suma cero en tiempo discreto tienen al menos un equilibrio en estrategias puras?

- lexical: Hit@3 0; RR 0.000; nDCG@5 0.000
- dense: Hit@3 0; RR 0.000; nDCG@5 0.000
- hybrid: Hit@3 0; RR 0.000; nDCG@5 0.000
