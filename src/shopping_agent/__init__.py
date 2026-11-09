"""Shopping Agent package."""

from shopping_agent.agent import agent, main
from shopping_agent.config import BASE_DIR, DB_PATH, DEFAULT_MODEL, VISION_MODEL
from shopping_agent.orders_api import get_orders, place_order, place_orders
from shopping_agent.products_api import get_product_by_id, search_products_db
from shopping_agent.reviews_api import get_product_rating, get_ratings_for_products
from shopping_agent.utils import get_text
from shopping_agent.vision_api import describe_product_image_api

__all__ = [
    "agent",
    "main",
    "search_products_db",
    "get_product_by_id",
    "get_product_rating",
    "get_ratings_for_products",
    "place_order",
    "place_orders",
    "get_orders",
    "describe_product_image_api",
    "get_text",
    "BASE_DIR",
    "DB_PATH",
    "DEFAULT_MODEL",
    "VISION_MODEL",
]
