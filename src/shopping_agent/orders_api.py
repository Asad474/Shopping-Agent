import json
import sqlite3
from typing import Any, Optional, Union
from shopping_agent.config import DB_PATH


def _normalize_product_ids(val: Any) -> list[int]:
    """Parse and normalize product IDs from int, float, str, or collection into a list of ints."""
    if val is None:
        return []
    if isinstance(val, bool):
        return []
    if isinstance(val, int):
        return [val]
    if isinstance(val, float):
        return [int(val)]
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return []
        # Support JSON string format like "[1, 2]"
        if val.startswith("[") and val.endswith("]"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return _normalize_product_ids(parsed)
            except (json.JSONDecodeError, ValueError):
                pass
        # Support comma-separated format like "1, 2"
        if "," in val:
            parts = val.split(",")
            return _normalize_product_ids(parts)
        # Clean single ID strings like "1", "#1", "ID:1"
        cleaned = val.lstrip("#").lower().replace("id:", "").strip()
        try:
            return [int(cleaned)]
        except ValueError:
            return []
    if isinstance(val, (list, tuple, set)):
        result: list[int] = []
        for item in val:
            result.extend(_normalize_product_ids(item))
        return result
    return []


def place_orders(
    product_ids: Optional[Union[list[int], int, str, Any]] = None,
    *,
    product_id: Optional[Union[int, str]] = None,
) -> dict:
    """Place orders for one or multiple products by their IDs in a single database transaction.

    Accepts:
      - A single product ID (int or numeric str)
      - A list/tuple of product IDs
      - Keyword argument `product_id` for backward compatibility
    """
    raw_input = product_ids if product_ids is not None else product_id
    if raw_input is None:
        return {
            "status": "failed",
            "error": "No product IDs provided",
            "orders": [],
            "total_items": 0,
            "total_amount": 0.0,
            "failed_ids": [],
        }

    ids = _normalize_product_ids(raw_input)
    if not ids:
        return {
            "status": "failed",
            "error": "product_ids must be an integer, list of integers, or numeric string",
            "orders": [],
            "total_items": 0,
            "total_amount": 0.0,
            "failed_ids": [],
        }

    placed_orders: list[dict] = []
    failed_ids: list[int] = []

    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            with conn:
                cursor = conn.cursor()
                for pid in ids:
                    cursor.execute(
                        "SELECT id, name, price FROM products WHERE id = ?", (pid,)
                    )
                    product = cursor.fetchone()

                    if not product:
                        failed_ids.append(pid)
                        continue

                    p_id, name, price = product
                    cursor.execute(
                        "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
                        (p_id, name, price),
                    )
                    order_id = cursor.lastrowid

                    cursor.execute(
                        "SELECT ordered_at FROM orders WHERE id = ?", (order_id,)
                    )
                    row = cursor.fetchone()
                    ordered_at = row[0] if row else ""

                    placed_orders.append({
                        "order_id": order_id,
                        "product_id": p_id,
                        "product_name": name,
                        "price": price,
                        "ordered_at": ordered_at,
                    })
        finally:
            conn.close()
    except sqlite3.Error as e:
        return {
            "status": "failed",
            "error": f"Database error: {e}",
            "orders": placed_orders,
            "total_items": len(placed_orders),
            "total_amount": round(sum(o["price"] for o in placed_orders), 2),
            "failed_ids": failed_ids or ids,
        }

    total_amount = round(sum(o["price"] for o in placed_orders), 2)
    if not failed_ids:
        status = "confirmed"
    elif placed_orders:
        status = "partial"
    else:
        status = "failed"

    result: dict[str, Any] = {
        "status": status,
        "orders": placed_orders,
        "total_items": len(placed_orders),
        "total_amount": total_amount,
        "failed_ids": failed_ids,
    }

    if status == "failed":
        result["error"] = f"Product ID(s) {failed_ids} not found in store catalog"
    elif status == "partial":
        result["warning"] = (
            f"Ordered {len(placed_orders)} item(s), but product ID(s) {failed_ids} were not found"
        )

    # Backward compatibility convenience for single item orders
    if len(placed_orders) == 1:
        result["order_id"] = placed_orders[0]["order_id"]
        result["product_id"] = placed_orders[0]["product_id"]
        result["product_name"] = placed_orders[0]["product_name"]
        result["price"] = placed_orders[0]["price"]
        result["ordered_at"] = placed_orders[0]["ordered_at"]

    return result


def place_order(
    product_id: Optional[Union[int, str]] = None,
    product_ids: Optional[Union[list[int], int, str]] = None,
) -> dict:
    """Backward-compatible wrapper for single or multi-item orders."""
    target = product_id if product_id is not None else product_ids
    return place_orders(target)


def get_orders(limit: Optional[int] = None) -> list[dict]:
    """Retrieve orders from the orders table ordered newest first."""
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            query = "SELECT id, product_id, product_name, price, ordered_at FROM orders ORDER BY id DESC"
            if limit and isinstance(limit, int) and limit > 0:
                query += f" LIMIT {limit}"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                {
                    "order_id": row[0],
                    "product_id": row[1],
                    "product_name": row[2],
                    "price": row[3],
                    "ordered_at": row[4],
                }
                for row in rows
            ]
        finally:
            conn.close()
    except sqlite3.Error:
        return []


def get_order_by_id(order_id: int) -> Optional[dict]:
    """Retrieve a single order by its ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, product_id, product_name, price, ordered_at FROM orders WHERE id = ?",
                (int(order_id),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "order_id": row[0],
                "product_id": row[1],
                "product_name": row[2],
                "price": row[3],
                "ordered_at": row[4],
            }
        finally:
            conn.close()
    except (sqlite3.Error, ValueError):
        return None


if __name__ == "__main__":
    print("Testing place_orders with multiple product IDs [1, 2]:")
    res = place_orders([1, 2])
    print("Result:", res)
    # Clean up test orders
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for o in res["orders"]:
        c.execute("DELETE FROM orders WHERE id = ?", (o["order_id"],))
    conn.commit()
    conn.close()
    print("Cleaned up test orders.")

    print("\nTesting place_order with keyword product_id=1:")
    res_single = place_order(product_id=1)
    print("Result:", res_single)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id = ?", (res_single["order_id"],))
    conn.commit()
    conn.close()
    print("Cleaned up single test order.")

    print("\nTesting string input '1, 2':")
    res_str = place_orders("1, 2")
    print("Result:", res_str)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for o in res_str["orders"]:
        c.execute("DELETE FROM orders WHERE id = ?", (o["order_id"],))
    conn.commit()
    conn.close()
    print("Cleaned up string test orders.")
