from fastapi import APIRouter

from ..schemas import KnowledgeSearchRequest, OperationsIntelligenceRequest
from ..services import asset_resolver, knowledge, operations_intelligence

router = APIRouter()


@router.get("/meta/document-types")
def document_types():
    return {"document_types": list(knowledge.DOCUMENT_TYPES)}


@router.post("/knowledge/search")
def search(req: KnowledgeSearchRequest):
    asset_id = asset_resolver.validate(req.asset_id) if req.asset_id else None
    return knowledge.search_knowledge(req.query, asset_id, req.document_type, req.num_results)


@router.post("/operations-intelligence")
def analyze(req: OperationsIntelligenceRequest):
    return operations_intelligence.ask_operations_intelligence(req.question, req.asset_id)
