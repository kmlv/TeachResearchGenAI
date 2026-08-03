"""Límites y procedencia de una sesión: se aplican también ante llamadas inválidas."""

from __future__ import annotations

from dataclasses import dataclass, field

from .corpus import Corpus
from .models import Passage

MAX_OPERATIONS = 6
MAX_SEARCHES = 3


@dataclass
class AuditSession:
    corpus: Corpus = field(default_factory=Corpus)
    operations: int = 0
    searches: int = 0
    found_ids: set[str] = field(default_factory=set)
    opened_ids: set[str] = field(default_factory=set)

    def _consume(self) -> str | None:
        self.operations += 1
        if self.operations > MAX_OPERATIONS:
            return f"Límite de {MAX_OPERATIONS} operaciones agotado."
        return None

    def search(self, query: str) -> list[Passage] | str:
        exhausted = self._consume()
        if exhausted:
            return exhausted
        self.searches += 1
        if self.searches > MAX_SEARCHES:
            return f"Límite de {MAX_SEARCHES} búsquedas agotado."
        results = self.corpus.search(query)
        self.found_ids.update(passage.id for passage in results)
        return results

    def open(self, passage_id: str) -> Passage | str:
        exhausted = self._consume()
        if exhausted:
            return exhausted
        if passage_id not in self.found_ids:
            return "Solo se puede abrir un ID devuelto por buscar_corpus."
        passage = self.corpus.open(passage_id)
        if passage is None:
            return "ID de pasaje inexistente."
        self.opened_ids.add(passage_id)
        return passage
