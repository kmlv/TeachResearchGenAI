# Mapa del sistema: 18 libros completos

El sistema separa preparación, recuperación, evaluación y síntesis. Esa
separación permite reemplazar o mejorar una etapa sin fingir que otra ya está
resuelta.

```mermaid
flowchart LR
    A["18 PDF locales"] --> B["Manifest<br/>autor · año · ruta · política"]
    B --> C{"Preflight"}
    C -->|"digital"| D["Extracción por página"]
    C -->|"scanned o glued"| E["OCR incremental"]
    E --> D
    D --> F["Fragmentos de 320 palabras<br/>45 de solapamiento · páginas trazables"]
    F --> R["Build log<br/>hash · páginas · tiempos"]
    F --> G["Embeddings multilingües<br/>384 dimensiones"]
    F --> H["FTS5 / BM25"]
    G --> I["Ranking denso"]
    H --> J["Ranking lexical"]
    I --> K["Fusión RRF + diversidad"]
    J --> K
    K --> L["Top-k con autor, año y páginas"]
    L --> M{"Verificación humana"}
    M -->|"relevante"| N["Paquete de evidencia"]
    M -->|"no relevante"| O["Error documentado / nueva qrel"]
    N --> P["RAG opcional<br/>respuesta con citas o abstención"]
    N --> Q["Grafo opcional<br/>solo para relaciones explícitas"]
```

## Qué se produjo

| capa | artefacto | evidencia |
| --- | --- | --- |
| corpus | `manifest-full-books.csv` | 18 obras únicas con autor y año |
| calidad | `preflight-report-full-books.json` local | cero bloqueos full-scan |
| OCR | `ocr_cache/` local | 2,637 procesadas; 2,606 con texto; cero fallos |
| índice | `local_index_full/` local | 8,669 páginas; 14,726 fragmentos |
| trazabilidad | `page_ledger.jsonl` local | fuente PDF/OCR por página |
| evaluación | preguntas + qrels + pool exportado | 12 preguntas; 123 candidatos; 6 sin juzgar |
| resultados | `evaluation-report-full-books.md` | lexical/dense/hybrid comparables |
| docencia | deck, runbooks y demo congelada | pipeline explicable y repetible |
| audio | `20260804-000749_embeddings-y-rag-con-18-libros-completos.mp3` · 8:19 | relato de proceso, hallazgos y límites, con G2/G4 aprobados |
| aprobación | `approval-checklist.md` | G2 y G4 aprobados por Kristian; 6 casos aceptados sin juicio |

## Tres salidas distintas

1. **Buscar pasajes:** lexical, dense o hybrid.
2. **Redactar con evidencia:** RAG, después de evaluar el recuperador.
3. **Responder relaciones:** grafo ligero, solo si la pregunta exige aristas
   auditables entre autores, métodos, datasets, poblaciones o resultados.

Los microdatos siguen un cuarto camino: SQL sobre DuckDB o Parquet. Se indexan
sus diccionarios y metodologías; no se transforman millones de observaciones en
embeddings.
