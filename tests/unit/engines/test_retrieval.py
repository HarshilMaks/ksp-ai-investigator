from __future__ import annotations

import unittest

from data.generator import generate_fixture
from src.engines.search_ranking import HybridSearchEngine
from src.engines.retrieval.vector import VectorBackendUnavailable
from src.engines.sql_retrieval import (
    InMemoryFIRStore,
    StructuredRetrievalEngine,
    StructuredRetrievalError,
)


class SQLRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = generate_fixture(count=12, seed=20260725, year=2026)
        self.engine = StructuredRetrievalEngine(InMemoryFIRStore.from_fixture(self.fixture))

    def test_exact_filters_counts_dates_and_citations(self) -> None:
        first = self.fixture.firs[0]
        result = self.engine.search(
            filters={
                "fir_id": first.fir_id,
                "district": first.district,
                "year": 2026,
            },
            columns=("fir_id", "fir_number", "district"),
            limit=10,
        )
        self.assertEqual(result.total, 1)
        self.assertEqual(result.records[0].record["fir_id"], str(first.fir_id))
        self.assertEqual(set(result.records[0].record), {"fir_id", "fir_number", "district"})
        self.assertEqual(result.records[0].citation.source_type, "FIR")
        self.assertEqual(result.records[0].citation.source_id, str(first.fir_id))

        date_result = self.engine.search(
            filters={"crime_date_from": "2026-01-01T00:00:00+05:30", "crime_date_to": "2026-01-31T23:59:59+05:30"},
            limit=100,
        )
        self.assertGreater(date_result.total, 0)
        self.assertTrue(all(record.citation.source_type == "FIR" for record in date_result.records))

    def test_count_is_deterministic_and_unknown_filters_fail_closed(self) -> None:
        category = self.fixture.firs[0].crime_category
        one = self.engine.store.count({"crime_category": category})
        two = self.engine.store.count({"crime_category": category})
        self.assertEqual(one, two)
        with self.assertRaises(StructuredRetrievalError):
            self.engine.search(filters={"unrestricted_sql": "DROP TABLE firs"})

    def test_structured_limit_is_enforced(self) -> None:
        with self.assertRaises(StructuredRetrievalError):
            self.engine.search(limit=1001)


class UnavailableVectorBackend:
    def search(self, query: str, *, top_k: int, similarity_threshold: float, metadata_filter: dict | None):
        raise VectorBackendUnavailable("synthetic backend outage")


class HybridSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = generate_fixture(count=12, seed=20260725, year=2026)
        self.engine = HybridSearchEngine.from_firs(fixture.firs)

    def test_hybrid_search_has_rrf_scores_ranks_and_citations(self) -> None:
        result = self.engine.search("cybercrime modus operandi", top_k=5)
        self.assertEqual(result.rrf_k, 60)
        self.assertLessEqual(len(result.hits), 5)
        self.assertGreater(result.candidate_count, 0)
        self.assertEqual([hit.rank for hit in result.hits], list(range(1, len(result.hits) + 1)))
        self.assertTrue(all(hit.score > 0 for hit in result.hits))
        self.assertTrue(all(hit.citation.source_type == "FIR" for hit in result.hits))
        self.assertTrue(all(hit.citation.source_id for hit in result.hits))

    def test_metadata_filter_and_candidate_limit_are_applied(self) -> None:
        result = self.engine.search(
            "fraud",
            top_k=3,
            metadata_filter={"district": "Bengaluru Urban"},
        )
        self.assertLessEqual(len(result.hits), 3)
        self.assertTrue(all(hit.document.metadata["district"] == "Bengaluru Urban" for hit in result.hits))
        with self.assertRaises(ValueError):
            self.engine.search("fraud", top_k=101)

    def test_same_fixture_and_query_are_reproducible(self) -> None:
        query = "synthetic cybercrime incident modus operandi"
        left = self.engine.search(query, top_k=5)
        right = self.engine.search(query, top_k=5)
        self.assertEqual(
            [(hit.document.source_id, hit.score) for hit in left.hits],
            [(hit.document.source_id, hit.score) for hit in right.hits],
        )

    def test_external_vector_failure_degrades_to_local_search_explicitly(self) -> None:
        fixture = generate_fixture(count=6, seed=20260725, year=2026)
        engine = HybridSearchEngine.from_firs(
            fixture.firs,
            external_vector_backend=UnavailableVectorBackend(),
        )
        result = engine.search("fraud", top_k=3)
        self.assertTrue(result.degraded)
        self.assertEqual(result.backend, "local-deterministic")
        self.assertIsNotNone(result.degradation)
        self.assertEqual(result.degradation.code, "VECTOR_BACKEND_UNAVAILABLE")
        self.assertGreater(len(result.hits), 0)


if __name__ == "__main__":
    unittest.main()
