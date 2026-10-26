"""Versioned knowledge retrieval with explicit access filters and evaluation."""
from app.retrieval import answer, identifier, initialize, put, remove, search

TITLE = "Knowledge Search"
DESCRIPTION = "Búsqueda documental con permisos, versiones y citas verificables."
DEMO = {"action": "demo", "tenant": "demo-company", "query": "vacaciones solicitud anticipación"}
DOCUMENTS = [
    {"id": "leave-policy", "title": "Política de vacaciones", "text": "Las vacaciones se solicitan con quince días de anticipación. La solicitud debe incluir fecha de inicio, fecha de regreso y aprobación del responsable del equipo."},
    {"id": "travel-policy", "title": "Reembolso de viajes", "text": "El reembolso de viajes requiere factura y comprobante de pago. El plazo para presentar gastos es de treinta días después del viaje. Los gastos sin comprobantes pasan a revisión financiera."},
    {"id": "payroll-policy", "title": "Nómina y compensación", "text": "Los ajustes de nómina requieren aprobación de recursos humanos y finanzas. El cierre de nómina se realiza el día veinticinco de cada mes.", "access_group": "hr"},
]
EVALUATION = [
    {"query": "vacaciones anticipación solicitud", "expected_document_id": "leave-policy"},
    {"query": "viajes reembolso comprobante", "expected_document_id": "travel-policy"},
    {"query": "temperatura volcán telescopio", "expected_document_id": None},
]


def process(payload, store):
    connection = store.connection
    initialize(connection)
    tenant = identifier(payload.get("tenant"), "tenant")
    action = payload.get("action", "query")
    if action == "demo":
        for document in DOCUMENTS:
            put(connection, tenant, document)
        action = "query"
    if action == "ingest":
        documents = payload.get("documents")
        if not isinstance(documents, list) or not 1 <= len(documents) <= 50:
            raise ValueError("documents must contain 1-50 document objects")
        result = [put(connection, tenant, document) for document in documents]
        store.event("documents.ingested", {"tenant": tenant, "count": len(result)})
        return {"documents": result}
    if action == "delete":
        removed = remove(connection, tenant, payload.get("document_id"))
        store.event("document.deleted", {"tenant": tenant, "removed": removed})
        return {"deleted": removed}
    if action == "query":
        query = payload.get("query")
        hits = search(connection, tenant, query, payload.get("access_groups"))
        result = answer(query, hits)
        store.event("knowledge.queried", {"tenant": tenant, "abstained": result["abstained"], "source_count": len(result["sources"])})
        return result
    if action == "evaluate":
        # The fixture is fixed and inspectable, avoiding path-based file access.
        cases = []
        for case in EVALUATION:
            hits = search(connection, tenant, case["query"], [])
            actual = hits[0]["document_id"] if hits else None
            cases.append({**case, "actual_document_id": actual, "passed": actual == case["expected_document_id"]})
        answerable = [case for case in cases if case["expected_document_id"] is not None]
        unanswerable = [case for case in cases if case["expected_document_id"] is None]
        return {"dataset": "policy-fixture-v1", "cases": cases, "retrieval_hit_rate_at_1": sum(case["passed"] for case in answerable) / len(answerable), "abstention_accuracy": sum(case["passed"] for case in unanswerable) / len(unanswerable), "case_accuracy": sum(case["passed"] for case in cases) / len(cases), "scope": "synthetic local fixture; not a production accuracy estimate"}
    raise ValueError("unknown action")
