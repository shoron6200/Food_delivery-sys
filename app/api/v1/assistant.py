"""AI assistant endpoint: say what you feel like eating, get dishes you can order."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import Customer, DbSession
from app.core.config import settings
from app.schemas.assistant import AssistantOut, AssistantRequest, AssistantSuggestionOut
from app.services.assistant import AssistantUnavailable, ask_claude, keep_real_picks
from app.services.catalog import get_orderable_items
from app.services.rate_limit import RateLimiter

router = APIRouter(prefix="/assistant", tags=["assistant"])

# Every call costs real money, so each customer gets 5 per minute.
limiter = RateLimiter(max_calls=5, per_seconds=60)


@router.post("/suggest", response_model=AssistantOut)
def suggest(data: AssistantRequest, customer: Customer, db: DbSession):
    if not settings.anthropic_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The AI assistant is not set up on this server (ANTHROPIC_API_KEY is missing)",
        )
    if not limiter.allow(customer.id):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many questions in a short time. Wait a minute and try again.",
        )

    items = get_orderable_items(db)
    if not items:
        # Nothing to choose from, so there is no reason to pay for a model call.
        return AssistantOut(
            reply="No restaurant is taking orders right now. Please try again later.",
            suggestions=[],
            food_total=0,
        )

    try:
        answer = ask_claude(data.message, items)
    except AssistantUnavailable as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error))

    suggestions = [
        AssistantSuggestionOut(item=item, quantity=quantity, line_total=item.price * quantity)
        for item, quantity in keep_real_picks(answer.picks, items)
    ]
    return AssistantOut(
        reply=answer.reply,
        suggestions=suggestions,
        food_total=sum(suggestion.line_total for suggestion in suggestions),
    )
