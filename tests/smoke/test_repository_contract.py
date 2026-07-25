from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class RepositoryContractTests(unittest.TestCase):
    def test_required_boundaries_exist(self) -> None:
        for relative in ("src", "functions", "client", "data", "appsail", "tests", ".LOCK"):
            self.assertTrue((ROOT / relative).is_dir(), relative)

    def test_phase_plan_and_investigator_journey_exist(self) -> None:
        self.assertTrue((ROOT / "implementation_phases.md").is_file())
        journey = (ROOT / "docs" / "investigator-journey.md").read_text()
        self.assertIn("proactive alerts", journey)
        self.assertIn("Hypothesis Panel", journey)
        self.assertIn("Investigation Health", journey)
        self.assertIn("The officer owns the investigation", journey)

    def test_locked_and_private_files_are_present_but_not_runtime_inputs(self) -> None:
        self.assertTrue((ROOT / ".LOCK" / "DECISIONS.md").is_file())
        self.assertTrue((ROOT / ".LOCK" / "TODO.md").is_file())
        self.assertTrue((ROOT / "session-ses_0754.md").is_file())
        self.assertNotIn("session-ses_0754.md", (ROOT / "README.md").read_text())

    def test_backend_contract_is_python_only(self) -> None:
        config = (ROOT / "pyproject.toml").read_text()
        self.assertIn('backend_language = "python"', config)
        self.assertIn('deployment_python = "3.11"', config)
        self.assertIn("synthetic_data_only = true", config)


if __name__ == "__main__":
    unittest.main()
