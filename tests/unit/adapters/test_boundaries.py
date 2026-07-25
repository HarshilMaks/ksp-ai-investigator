from pathlib import Path
import tempfile
import unittest

from src.adapters.cache import build_cache
from src.adapters.catalyst import (
    CatalystDataStoreAdapter,
    LocalCache,
    LocalDataStore,
    LocalEventBus,
    LocalObjectStore,
)
from src.adapters.llm import LiteLLMRouter
from src.adapters.neo4j import Neo4jClient
from src.adapters.stratus import build_object_store
from src.shared.config import load_settings
from src.shared.errors import AdapterUnavailableError, ApplicationError
from src.shared.ports import CatalystRequest, CatalystResponse, ModelRequest, ModelResponse, StreamChunk


class FakeTransport:
    def __init__(self) -> None:
        self.requests: list[CatalystRequest] = []

    async def send(self, request: CatalystRequest) -> CatalystResponse:
        self.requests.append(request)
        if request.operation == "get":
            return CatalystResponse(200, {"value": {"id": request.payload["key"]}}, request.request_id)
        return CatalystResponse(200, {"event_id": "fake-event", "claims": {"role": "IO"}}, request.request_id)


class FakeBackend:
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.calls: list[str] = []

    async def complete(self, model: str, request: ModelRequest) -> ModelResponse:
        self.calls.append(model)
        if len(self.calls) <= self.failures:
            raise RuntimeError("provider failure must not escape")
        return ModelResponse(model, "grounded response", "request-1")

    async def stream(self, model: str, request: ModelRequest):
        yield StreamChunk("chunk", model, "request-1")


class LocalAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_data_cache_events_and_object_store(self) -> None:
        data = LocalDataStore()
        await data.put("firs", "fir-1", {"fir_id": "fir-1", "status": "OPEN"})
        self.assertEqual(await data.get("firs", "fir-1"), {"fir_id": "fir-1", "status": "OPEN"})
        self.assertEqual(await data.query("firs", {"status": "OPEN"}), [{"fir_id": "fir-1", "status": "OPEN"}])

        cache = LocalCache()
        await cache.set("key", {"value": 1}, ttl_seconds=10)
        self.assertEqual(await cache.get("key"), {"value": 1})

        events = LocalEventBus()
        self.assertEqual(await events.publish("fir.inserted", {"fir_id": "fir-1"}), "local-00000001")
        self.assertEqual(events.events[0][0], "fir.inserted")

        with tempfile.TemporaryDirectory() as directory:
            objects = LocalObjectStore(directory)
            await objects.put("cards/card.json", b"{}", content_type="application/json")
            self.assertEqual(await objects.get("cards/card.json"), b"{}")
            with self.assertRaises(ApplicationError):
                await objects.get("../outside")

    async def test_local_factories_are_default_and_do_not_need_external_flags(self) -> None:
        settings = load_settings({"APP_ENV": "test"})
        self.assertIsInstance(build_cache(settings), LocalCache)
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsInstance(build_object_store(settings, directory), LocalObjectStore)


class DisabledExternalAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_catalyst_is_disabled_without_transport_or_network(self) -> None:
        settings = load_settings({"APP_ENV": "test"})
        adapter = CatalystDataStoreAdapter(settings)
        with self.assertRaises(AdapterUnavailableError) as raised:
            await adapter.get("firs", "fir-1")
        self.assertEqual(raised.exception.code, "CATALYST_DISABLED")

    async def test_neo4j_and_llm_are_disabled_by_default(self) -> None:
        settings = load_settings({"APP_ENV": "test"})
        graph = Neo4jClient.from_settings(settings)
        with self.assertRaises(AdapterUnavailableError) as graph_error:
            await graph.read("MATCH (n) RETURN n")
        self.assertEqual(graph_error.exception.code, "NEO4J_DISABLED")

        router = LiteLLMRouter(settings)
        with self.assertRaises(AdapterUnavailableError) as llm_error:
            await router.complete(ModelRequest(({"role": "user", "content": "hello"},)))
        self.assertEqual(llm_error.exception.code, "LLM_DISABLED")


class InjectedBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_catalyst_transport_receives_typed_request_only_when_enabled(self) -> None:
        settings = load_settings({"APP_ENV": "test", "CATALYST_EXTERNAL_ENABLED": "true"})
        transport = FakeTransport()
        adapter = CatalystDataStoreAdapter(settings, transport)
        value = await adapter.get("firs", "fir-1")
        self.assertEqual(value, {"id": "fir-1"})
        self.assertEqual(transport.requests[0].service, "data_store")
        self.assertEqual(transport.requests[0].operation, "get")
        self.assertNotIn("password", repr(transport.requests[0]).lower())

    async def test_llm_router_uses_locked_fallback_order(self) -> None:
        settings = load_settings({"APP_ENV": "test", "LLM_ENABLED": "true"})
        backend = FakeBackend(failures=2)
        router = LiteLLMRouter(settings, backend)
        response = await router.complete(ModelRequest(({"role": "user", "content": "hello"},)))
        self.assertEqual(response.content, "grounded response")
        self.assertEqual(backend.calls, list(settings.model_chain[:3]))
        chunks = [chunk async for chunk in router.stream(ModelRequest(({"role": "user", "content": "hello"},)))]
        self.assertEqual(chunks[0].content, "chunk")

    async def test_neo4j_connection_boundary_preserves_locked_ports(self) -> None:
        settings = load_settings({"APP_ENV": "test", "NEO4J_ENABLED": "true"})
        graph = Neo4jClient.from_settings(settings, driver=FakeGraphDriver())
        self.assertEqual(graph.connection.uri, "bolt://localhost:7687")
        self.assertEqual(graph.connection.bolt_port, 7687)
        self.assertEqual(await graph.read("RETURN 1"), [{"value": 1}])


class FakeGraphDriver:
    async def read(self, cypher: str, params: dict) -> list[dict]:
        return [{"value": 1}]

    async def write(self, cypher: str, params: dict) -> list[dict]:
        return []


if __name__ == "__main__":
    unittest.main()
