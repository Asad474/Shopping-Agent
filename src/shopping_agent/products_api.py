import sqlite3
from typing import Optional
from shopping_agent.config import DB_PATH


def search_products_db(
    query: Optional[str] = None,
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
) -> list[dict]:
    """Search products database by keyword query, maximum price, and organic flag."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = "SELECT id, name, category, price, description, is_organic FROM products WHERE 1=1"
    params: list = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    if is_organic is not None:
        sql += " AND is_organic = ?"
        params.append(1 if is_organic else 0)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "price": row[3],
            "description": row[4],
            "is_organic": bool(row[5]),
        }
        for row in rows
    ]


def get_product_by_id(product_id: int) -> Optional[dict]:
    """Fetch a single product by its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, category, price, description, is_organic FROM products WHERE id = ?",
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "price": row[3],
        "description": row[4],
        "is_organic": bool(row[5]),
    }


if __name__ == "__main__":
    print("Testing search_products_db(query='honey', is_organic=True):")
    results = search_products_db(query="honey", is_organic=True)
    for p in results:
        print(f"  #{p['id']} {p['name']} - ${p['price']} (Organic: {p['is_organic']})")

