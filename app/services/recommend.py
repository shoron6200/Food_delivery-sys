""""For you" recommendations: rank menu items for one customer.

This is a content-based recommender: it looks at what THIS customer ordered
before (which items, which categories) and at how well each restaurant is
rated. No machine learning yet. Every score can be explained in one sentence,
which is what the `reason` is for.
"""

from collections import Counter
from dataclasses import dataclass

from app.models.restaurant import MenuItem

# A restaurant nobody has reviewed yet is treated as average, not as bad.
NEUTRAL_RATING = 3.0
# Extra points for an item in the customer's favourite category (scaled by how
# much of their past ordering was in that category).
CATEGORY_WEIGHT = 5.0
# Extra points for an item the customer has ordered before.
REORDER_BONUS = 2.0


@dataclass(frozen=True)
class PastItem:
    """One line from the customer's delivered orders."""

    menu_item_id: int
    category: str
    quantity: int


@dataclass(frozen=True)
class Recommendation:
    item: MenuItem
    score: float
    reason: str


def recommend(
    candidates: list[MenuItem], history: list[PastItem], limit: int = 10
) -> list[Recommendation]:
    """Return the `limit` best candidates for a customer with this history."""
    total_quantity = sum(past.quantity for past in history)
    quantity_by_category = Counter()
    for past in history:
        quantity_by_category[past.category.lower()] += past.quantity
    ordered_before = {past.menu_item_id for past in history}

    results = []
    for item in candidates:
        rating = item.restaurant.average_rating
        score = rating if rating is not None else NEUTRAL_RATING

        # Between 0 and 1: the part of their past ordering that was this category.
        category_share = 0.0
        if total_quantity > 0:
            category_share = quantity_by_category[item.category.lower()] / total_quantity
        score += CATEGORY_WEIGHT * category_share

        if item.id in ordered_before:
            score += REORDER_BONUS
            reason = "You ordered this before"
        elif category_share > 0:
            reason = f"Because you like {item.category}"
        elif rating is not None and rating >= 4:
            reason = "From a highly rated restaurant"
        else:
            reason = "Something new to try"

        results.append(Recommendation(item=item, score=round(score, 2), reason=reason))

    # Best score first. Ties: cheaper first, then a fixed order so the list is stable.
    results.sort(key=lambda r: (-r.score, r.item.price, r.item.id))
    return results[:limit]
