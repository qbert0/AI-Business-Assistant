from app.schemas.context import ContextBuildRequest, ContextItem, ConversationMessage
from app.services.context_service import ContextService


def test_build_context_includes_history_query_and_context_items() -> None:
    service = ContextService()
    payload = ContextBuildRequest(
        organization_id="org-1",
        query="What is the current expense approval policy?",
        history=[
            ConversationMessage(role="user", content="Summarize the finance handbook."),
            ConversationMessage(role="assistant", content="Here is a brief summary."),
        ],
        external_contexts=[
            ContextItem(
                title="Finance Handbook",
                content="Expenses above 10 million VND need manager approval.",
                source="s3://finance/handbook.pdf",
            )
        ],
    )

    result = service.build_context(payload)

    assert result.messages[0].role == "system"
    assert "Finance Handbook" in result.messages[0].content
    assert result.messages[-1].content == payload.query
    assert result.context_items[0].source == "s3://finance/handbook.pdf"
    assert result.token_estimate > 0
