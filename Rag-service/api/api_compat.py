from fastapi import APIRouter, Body, HTTPException

from conn import ModelServiceClient
from services import get_graphiti_service

router = APIRouter()

model_service_client = ModelServiceClient()


@router.post("/model-service/smoke")
async def model_service_smoke_test(
    payload: dict[str, object] = Body(default_factory=dict),
) -> dict[str, object]:
    sample_text = str(
        payload.get(
            "text",
            "Cong ty ABC cong bo doanh thu quy 1 tang 8 phan tram so voi cung ky.",
        )
    )
    sample_question = str(
        payload.get(
            "question",
            "Trich xuat cac thuc the va quan he duoi dang JSON hop le.",
        )
    )

    embeddings_result = await model_service_client.create_embeddings(
        [sample_text],
        metadata={"source": "rag-service-compat-smoke"},
    )

    inference_result = await model_service_client.create_inference(
        question=sample_question,
        system_prompt=(
            "Ban phai tra ve JSON hop le voi cac truong entities va relationships. "
            "Khong duoc them giai thich ngoai JSON."
        ),
        history=[{"role": "user", "content": sample_text}],
        max_tokens=800,
        temperature=0.0,
        metadata={"source": "rag-service-compat-smoke"},
    )

    embedding_vectors = embeddings_result.get("data", [])
    first_vector = embedding_vectors[0]["embedding"] if embedding_vectors else []
    response_text = ((inference_result.get("response", {}) or {}).get("response_text", ""))[:1000]

    return {
        "status": "ok",
        "embedding": {
            "dimensions": embeddings_result.get("dimensions"),
            "vector_count": len(embedding_vectors),
            "preview": first_vector[:8],
        },
        "inference": {
            "request_id": (inference_result.get("request", {}) or {}).get("id"),
            "response_preview": response_text,
        },
    }


@router.post("/graphiti/ingest-smoke")
async def graphiti_ingest_smoke_test(
    payload: dict[str, object] = Body(default_factory=dict),
) -> dict[str, object]:
    sample_text = str(
        payload.get(
            "text",
            "Cong ty ABC cong bo doanh thu quy 1 tang 8 phan tram so voi cung ky. "
            "Doanh nghiep ky vong bien loi nhuan se cai thien trong quy tiep theo.",
        )
    )
    source_description = str(payload.get("source_description", "compat smoke test"))
    group_id = payload.get("group_id")
    if group_id is not None:
        group_id = str(group_id)

    try:
        graphiti_service = await get_graphiti_service()
        result = await graphiti_service.smoke_ingest_text(
            sample_text,
            source_description=source_description,
            group_id=group_id,
        )
        return {
            "status": "ok",
            "graphiti": result,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Graphiti smoke ingest failed",
                "error": str(exc),
            },
        ) from exc
