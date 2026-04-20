from app.schemas.context import ContextBuildRequest, ContextBuildResponse, ConversationMessage


DEFAULT_SYSTEM_PROMPT = (
    "You are an enterprise financial advisory assistant. "
    "Provide grounded, concise, professional answers. "
    "Use only the trusted context that is supplied. "
    "If the available context is insufficient, say so clearly instead of inventing facts."
)


class ContextService:
    def build_context(self, payload: ContextBuildRequest) -> ContextBuildResponse:
        history = payload.history[-payload.max_history_messages :]
        context_items = payload.external_contexts

        system_parts = [payload.system_prompt or DEFAULT_SYSTEM_PROMPT]
        if payload.organization_id:
            system_parts.append(f"Organization context: {payload.organization_id}.")
        if context_items:
            serialized_items = []
            for index, item in enumerate(context_items, start=1):
                label = f"[{index}] {item.title}"
                if item.source:
                    label = f"{label} ({item.source})"
                serialized_items.append(f"{label}\n{item.content}")
            system_parts.append("Trusted context:\n" + "\n\n".join(serialized_items))

        system_prompt = "\n\n".join(part for part in system_parts if part.strip())
        messages = [ConversationMessage(role="system", content=system_prompt), *history]
        messages.append(ConversationMessage(role="user", content=payload.query))

        token_estimate = sum(max(1, len(message.content) // 4) for message in messages)
        return ContextBuildResponse(
            system_prompt=system_prompt,
            messages=messages,
            context_items=context_items,
            token_estimate=token_estimate,
        )
