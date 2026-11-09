import base64
import json
import mimetypes
import os
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from shopping_agent.config import VISION_MODEL
from shopping_agent.utils import get_text


def describe_product_image_api(image_path: str) -> dict:
    """Analyze a product image and return search query and organic flag."""
    if not os.path.exists(image_path):
        return {"error": f"Image file not found: {image_path}"}

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/png"

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    b64_data = base64.b64encode(image_bytes).decode("utf-8")

    prompt = (
        "Identify the grocery or retail product shown in this image. "
        "Return a valid JSON object with exactly two keys:\n"
        "1. 'search_query': a concise 1-3 word keyword search query to find this item in a store database (e.g. 'honey', 'oats', 'milk', 'coffee')\n"
        "2. 'is_organic': true if the packaging explicitly shows organic, false if non-organic, or null if uncertain.\n"
        "Return ONLY the JSON object, nothing else."
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_data}"},
            },
        ]
    )

    try:
        vision_llm = ChatGoogleGenerativeAI(model=VISION_MODEL)
        response = vision_llm.invoke([message])
        text = get_text(response).strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)
        return {
            "search_query": data.get("search_query", ""),
            "is_organic": data.get("is_organic"),
        }
    except Exception as e:
        return {"error": str(e), "search_query": "", "is_organic": None}


if __name__ == "__main__":
    from shopping_agent.config import BASE_DIR

    sample_img = str(BASE_DIR / "resources" / "honey.png")
    if os.path.exists(sample_img):
        print(f"Sample image exists at: {sample_img}")
        print(describe_product_image_api(sample_img))
