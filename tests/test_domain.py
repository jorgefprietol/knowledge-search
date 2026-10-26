import copy
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from app.domain import DEMO, DOCUMENTS, process
from app.runtime import Store


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "knowledge.db")
        self.environment = patch.dict(os.environ, {"MODEL_BACKEND": "local"})
        self.environment.start()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()
        self.environment.stop()

    def call(self, **payload):
        response, _ = self.store.run({"tenant": "alpha", **payload}, uuid.uuid4().hex, process)
        return response["result"]

    def seed(self):
        return self.call(action="ingest", documents=copy.deepcopy(DOCUMENTS))

    def test_demo_returns_versioned_source(self):
        result = self.call(**{key: value for key, value in DEMO.items() if key != "tenant"})
        self.assertFalse(result["abstained"])
        self.assertEqual(result["sources"][0]["document_id"], "leave-policy")
        self.assertEqual(result["sources"][0]["version"], 1)
        self.assertEqual(result["answer"], result["sources"][0]["excerpt"])

    def test_tenant_filter_prevents_private_corpus_leak(self):
        self.seed()
        result = self.call(tenant="beta", query="vacaciones solicitud anticipación")
        self.assertTrue(result["abstained"])
        self.assertEqual(result["sources"], [])

    def test_access_groups_excluded_before_ranking(self):
        self.seed()
        self.assertTrue(self.call(query="nómina compensación ajustes")["abstained"])
        result = self.call(query="nómina compensación ajustes", access_groups=["hr"])
        self.assertEqual(result["sources"][0]["document_id"], "payroll-policy")

    def test_irrelevant_query_abstains(self):
        self.seed()
        self.assertTrue(self.call(query="telescopio volcán astronomía")["abstained"])

    def test_update_preserves_chunk_id_and_advances_version(self):
        self.seed()
        before = self.call(query="vacaciones anticipación")
        changed = dict(DOCUMENTS[0], text="Las vacaciones requieren veinte días de anticipación.", expected_version=1)
        self.call(action="ingest", documents=[changed])
        after = self.call(query="vacaciones anticipación")
        self.assertEqual(before["sources"][0]["chunk_id"], after["sources"][0]["chunk_id"])
        self.assertEqual(after["sources"][0]["version"], 2)
        self.assertIn("veinte", after["answer"])
        self.assertNotIn("quince", after["answer"])

    def test_identical_ingestion_keeps_version(self):
        self.seed()
        result = self.seed()
        self.assertTrue(all(not doc["changed"] and doc["version"] == 1 for doc in result["documents"]))

    def test_title_normalization_does_not_create_spurious_versions(self):
        document = dict(DOCUMENTS[0], title="  Política de vacaciones  ")
        self.call(action="ingest", documents=[document])
        result = self.call(action="ingest", documents=[document])
        self.assertFalse(result["documents"][0]["changed"])
        self.assertEqual(result["documents"][0]["version"], 1)

    def test_version_conflict_rejected(self):
        self.seed()
        with self.assertRaisesRegex(ValueError, "version conflict"):
            self.call(action="ingest", documents=[dict(DOCUMENTS[0], expected_version=0)])

    def test_delete_removes_citations(self):
        self.seed()
        self.assertTrue(self.call(action="delete", document_id="leave-policy")["deleted"])
        self.assertTrue(self.call(query="vacaciones anticipación")["abstained"])
        self.assertFalse(self.call(action="delete", document_id="leave-policy")["deleted"])

    def test_recreate_advances_version_and_rejects_stale_write(self):
        self.seed()
        before = self.call(query="vacaciones anticipación")["sources"][0]
        self.call(action="delete", document_id="leave-policy")
        recreated = self.call(action="ingest", documents=[dict(DOCUMENTS[0], text="Las vacaciones requieren veinte días de anticipación.")])
        self.assertEqual(recreated["documents"][0]["version"], 3)
        after = self.call(query="vacaciones anticipación")["sources"][0]
        self.assertEqual(before["chunk_id"], after["chunk_id"])
        self.assertEqual(after["version"], 3)
        with self.assertRaisesRegex(ValueError, "version conflict"):
            self.call(action="ingest", documents=[dict(DOCUMENTS[0], expected_version=1)])
        self.assertIn("veinte", self.call(query="vacaciones anticipación")["answer"])

    def test_delete_invalidates_previous_expected_version(self):
        self.seed()
        self.call(action="delete", document_id="leave-policy")
        for expected in (0, 1):
            with self.assertRaisesRegex(ValueError, "version conflict"):
                self.call(action="ingest", documents=[dict(DOCUMENTS[0], expected_version=expected)])

    def test_missing_delete_does_not_consume_revision(self):
        self.seed()
        self.assertTrue(self.call(action="delete", document_id="leave-policy")["deleted"])
        self.assertFalse(self.call(action="delete", document_id="leave-policy")["deleted"])
        self.assertEqual(self.call(action="ingest", documents=[DOCUMENTS[0]])["documents"][0]["version"], 3)

    def test_deleted_revision_is_scoped_to_tenant(self):
        self.seed()
        self.call(action="delete", document_id="leave-policy")
        other = self.call(tenant="beta", action="ingest", documents=[dict(DOCUMENTS[0], expected_version=0)])
        self.assertEqual(other["documents"][0]["version"], 1)
        self.assertEqual(self.call(action="ingest", documents=[DOCUMENTS[0]])["documents"][0]["version"], 3)

    def test_delete_rollback_restores_content_and_revision(self):
        self.seed()
        def fail_after_delete(payload, store):
            process({"tenant":"alpha", "action":"delete", "document_id":"leave-policy"}, store)
            raise ValueError("later operation failed")
        with self.assertRaisesRegex(ValueError, "later operation"):
            self.store.run({}, uuid.uuid4().hex, fail_after_delete)
        self.assertEqual(self.call(query="vacaciones anticipación")["sources"][0]["version"], 1)
        self.call(action="delete", document_id="leave-policy")
        self.assertEqual(self.call(action="ingest", documents=[DOCUMENTS[0]])["documents"][0]["version"], 3)

    def test_legacy_document_versions_migrate_before_delete(self):
        self.seed()
        self.call(action="ingest", documents=[dict(DOCUMENTS[0], text="Las vacaciones requieren veinte días de anticipación.", expected_version=1)])
        self.store.connection.execute("DROP TABLE document_revisions")
        self.call(action="delete", document_id="leave-policy")
        self.assertEqual(self.call(action="ingest", documents=[DOCUMENTS[0]])["documents"][0]["version"], 4)

    def test_delete_cannot_cross_tenant(self):
        self.seed()
        self.assertFalse(self.call(tenant="beta", action="delete", document_id="leave-policy")["deleted"])
        self.assertFalse(self.call(query="vacaciones anticipación")["abstained"])

    def test_document_batch_rolls_back_on_invalid_entry(self):
        with self.assertRaises(ValueError):
            self.call(action="ingest", documents=[DOCUMENTS[0], {"id": "../private", "title": "Invalid", "text": "text"}])
        self.assertTrue(self.call(query="vacaciones anticipación")["abstained"])
        recreated = self.call(action="ingest", documents=[dict(DOCUMENTS[0], expected_version=0)])
        self.assertEqual(recreated["documents"][0]["version"], 1)

    def test_evaluation_is_measured_on_fixed_fixture(self):
        self.seed()
        result = self.call(action="evaluate")
        self.assertEqual(result["retrieval_hit_rate_at_1"], 1)
        self.assertEqual(result["abstention_accuracy"], 1)
        self.assertEqual(len(result["cases"]), 3)
        self.assertIn("synthetic", result["scope"])

    def test_input_does_not_allow_filesystem_ingestion(self):
        with self.assertRaises(ValueError):
            self.call(action="ingest", documents=[{"id": "file", "title": "File", "path": "C:/Windows/win.ini"}])

    def test_invalid_access_groups_rejected(self):
        self.seed()
        with self.assertRaises(ValueError):
            self.call(query="vacaciones", access_groups="hr")

    def test_model_cannot_return_unlisted_source(self):
        self.seed()
        with patch.dict(os.environ, {"MODEL_BACKEND": "ollama"}), patch("app.providers.structured", return_value={"source_id": "invented"}):
            result = self.call(query="vacaciones anticipación")
        self.assertTrue(result["abstained"])

    def test_model_selects_excerpt_without_invented_answer(self):
        self.seed()
        hit = self.call(query="vacaciones anticipación")["sources"][0]
        with patch.dict(os.environ, {"MODEL_BACKEND": "ollama"}), patch("app.providers.structured", return_value={"source_id": hit["chunk_id"], "answer": "invented"}):
            result = self.call(query="vacaciones anticipación")
        self.assertEqual(result["answer"], hit["excerpt"])

    def test_retry_does_not_duplicate_document_audit(self):
        payload = {"action": "ingest", "tenant": "alpha", "documents": [DOCUMENTS[0]]}
        self.store.run(payload, "document-arrival-1", process)
        before = self.store.metrics()["audit_events"]
        _, replay = self.store.run(payload, "document-arrival-1", process)
        self.assertTrue(replay)
        self.assertEqual(self.store.metrics()["audit_events"], before)

    def test_restricting_document_access_removes_public_citation(self):
        self.seed()
        self.call(action="ingest", documents=[dict(DOCUMENTS[0], access_group="hr", expected_version=1)])
        self.assertTrue(self.call(query="vacaciones anticipación")["abstained"])
        self.assertFalse(self.call(query="vacaciones anticipación", access_groups=["hr"])["abstained"])


if __name__ == "__main__":
    unittest.main()
