import json
from typing import Optional, Union
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from shopping_agent.config import DEFAULT_MODEL
from shopping_agent.orders_api import place_orders
from shopping_agent.products_api import search_products_db
from shopping_agent.reviews_api import get_product_rating
from shopping_agent.utils import get_text
from shopping_agent.vision_api import describe_product_image_api

llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL)


@tool
def search_products(
    query: Optional[str] = None,
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
) -> str:
    """Search the product database by keyword (matched against name, description, and category).

    Optionally filter by maximum price and/or organic status.
    Returns a JSON array of matching products, each with: id, name, category, price,
    description, is_organic.
    """
    products = search_products_db(
        query=query, max_price=max_price, is_organic=is_organic
    )
    return json.dumps(products)


@tool
def get_rating(product_id: int) -> str:
    """Get the average customer rating and total review count for a product by its ID.

    Returns a JSON object with: product_id, average_rating, review_count.
    """
    result = get_product_rating(product_id)
    return json.dumps(result)


@tool
def checkout(product_ids: Union[list[int], int]) -> str:
    """Place an order for one or multiple products by their product IDs in a single call.

    Accepts a single product ID or a list of product IDs (e.g. [1] or [1, 3]) to order multiple items at once.
    Returns a JSON object with: status, orders (list with order_id, product_name, price, ordered_at),
    total_items, total_amount, and failed_ids.
    """
    result = place_orders(product_ids)
    return json.dumps(result)


@tool
def describe_product_image(image_path: str) -> str:
    """Analyze an image of a product at the given file path.

    Returns a JSON object with:
      - search_query (str): Keyword to search for this product in the store
      - is_organic (bool or null): Whether the product appears to be organic
    """
    result = describe_product_image_api(image_path)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

agent = create_agent(
    tools=[search_products, get_rating, checkout, describe_product_image],
    model=llm,
    system_prompt=(
        "You are a helpful shopping assistant. Follow these rules strictly.\n\n"
        "IMAGE SEARCH — when the user provides an image path:\n"
        "1. Call describe_product_image with the path to identify the product.\n"
        "2. Use the returned search_query and is_organic to call search_products.\n"
        "3. Continue with the BROWSING flow from step 2 onwards.\n\n"
        "BROWSING — when the user describes what they want to buy:\n"
        "1. Call search_products to find matching items (apply any price/organic filters given).\n"
        "2. For each candidate, call get_rating to retrieve its average rating.\n"
        "3. Filter by the user's minimum rating if specified.\n"
        "4. Present qualifying products as a numbered list. For each item use this exact format "
        "   (plain text, no backticks, no code blocks, no bold, no italic):\n\n"
        "   #<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>\n\n"
        "   Add a blank line between each product entry for readability. "
        "   Always include (ID:X) so you can reference it later.\n"
        "5. If only one product qualifies, still show it in the list and ask: "
        "   'Would you like to order it? Just say yes or give me the number.'\n"
        "6. Do NOT call checkout at this stage.\n\n"
        "ORDERING — when the user confirms they want to buy (e.g. 'yes', 'sure', 'go ahead', "
        "'order number 2', 'the first one', 'get me #1 and #3', 'buy both', 'order all of them'):\n"
        "1. Look at your previous message to find the (ID:X) for the chosen product(s).\n"
        "2. Call checkout with the list of product_ids (e.g. [1] or [1, 3]) in a SINGLE tool call.\n"
        "3. Confirm the order to the user in plain text including the items and total amount.\n\n"
        "Never place an order unless the user explicitly confirms. "
        "Never guess a product_id — always take it from the (ID:X) in your own previous message."
    ),
)


def main() -> None:
    """CLI entry point for testing the shopping agent."""
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I want to buy organic honey with 4.5+ rating and less than $20 price"
                    ),
                }
            ]
        }
    )
    print("Result:\n", get_text(result["messages"][-1]))


if __name__ == "__main__":
    main()

