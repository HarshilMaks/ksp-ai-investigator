from datetime import datetime, timedelta, timezone
import unittest
from uuid import UUID

from src.shared.clock import isoformat_utc, utc_now
from src.shared.config import SettingsError, load_settings
from src.shared.errors import ApplicationError, new_request_id


class SharedConfigurationTests(unittest.TestCase):
    def test_local_defaults_are_safe_and_match_locked_topology(self) -> None:
        settings = load_settings({"APP_ENV": "test"})
        self.assertEqual(settings.neo4j_uri, "bolt://localhost:7687")
        self.assertEqual(settings.neo4j_bolt_port, 7687)
        self.assertEqual(settings.neo4j_http_port, 7474)
        self.assertEqual(settings.model_chain[0], "groq/llama-3.3-70b-versatile")
        self.assertEqual(settings.embedding_dimensions, 1024)
        self.assertIsNone(settings.neo4j_password)
        self.assertNotIn("password", repr(settings).lower())

    def test_settings_diagnostics_redact_credentials(self) -> None:
        settings = load_settings(
            {
                "APP_ENV": "test",
                "NEO4J_PASSWORD": "neo4j-test-secret",
                "GROQ_API_KEY": "groq-test-secret",
            }
        )
        diagnostics = repr(settings.redacted())
        self.assertIn("[REDACTED]", diagnostics)
        self.assertNotIn("neo4j-test-secret", diagnostics)
        self.assertNotIn("groq-test-secret", diagnostics)

    def test_production_requires_deployment_credentials(self) -> None:
        with self.assertRaises(SettingsError) as raised:
            load_settings({"APP_ENV": "production"})
        self.assertEqual(raised.exception.code, "CONFIG_MISSING_REQUIRED")
        self.assertNotIn("NEO4J_PASSWORD", str(raised.exception))
        self.assertIn("CATALYST_PROJECT_ID", raised.exception.details["variables"])

    def test_production_rejects_insecure_urls(self) -> None:
        environment = {
            "APP_ENV": "catalyst",
            "CATALYST_PROJECT_ID": "project",
            "CATALYST_APP_ID": "app",
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "secret",
            "CATALYST_API_BASE_URL": "http://catalyst.example",
        }
        with self.assertRaises(SettingsError) as raised:
            load_settings(environment)
        self.assertEqual(raised.exception.code, "CONFIG_INSECURE_URL")
        self.assertNotIn("secret", str(raised.exception))

    def test_locked_ports_cannot_be_overridden(self) -> None:
        with self.assertRaises(SettingsError) as raised:
            load_settings({"NEO4J_BOLT_PORT": "7688"})
        self.assertEqual(raised.exception.code, "CONFIG_INVALID_PORT")

    def test_invalid_values_return_safe_error_details(self) -> None:
        with self.assertRaises(SettingsError) as raised:
            load_settings({"API_TIMEOUT_SECONDS": "not-an-int"})
        self.assertEqual(raised.exception.code, "CONFIG_INVALID_INTEGER")
        self.assertEqual(raised.exception.details, {"variable": "API_TIMEOUT_SECONDS"})


class SharedErrorsAndClockTests(unittest.TestCase):
    def test_error_response_has_standard_envelope_and_request_id(self) -> None:
        error = ApplicationError("ERR_TEST", "safe message")
        response = error.to_response().to_dict()
        self.assertEqual(response["error"]["code"], "ERR_TEST")
        UUID(response["error"]["request_id"])
        self.assertEqual(response["error"]["details"], {})

    def test_request_id_is_uuid(self) -> None:
        UUID(new_request_id())

    def test_clock_returns_aware_utc_and_normalizes_offsets(self) -> None:
        current = utc_now()
        self.assertIsNotNone(current.tzinfo)
        self.assertEqual(current.utcoffset(), timedelta(0))
        offset_value = datetime(2026, 7, 25, 18, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        self.assertEqual(isoformat_utc(offset_value), "2026-07-25T12:30:00Z")


if __name__ == "__main__":
    unittest.main()
