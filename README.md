# AI Shopping Assistant 🤖

An intelligent, multimodal AI Shopping Agent built with **Python**, **LangChain**, **Google Gemini**, and **Streamlit**. The agent browses a SQLite store catalog, aggregates customer review ratings, identifies products from photos via Gemini Vision, and executes single or multi-item checkout orders in a single step.

---

## 🚀 Features

- **Conversational Product Search**: Search catalog products by name, category, maximum budget, and organic preference.
- **Rating & Review Aggregation**: Retrieves live star ratings and review counts from the store database to filter and recommend top products.
- **Batch Checkout (Reduced Tool Calls)**: Supports ordering single or multiple product IDs simultaneously in one database transaction (`checkout(product_ids=[1, 3])`).
- **Multimodal Image Search**: Uses Gemini Vision to analyze uploaded product photos or sample images, identifying the product name and whether it's organic.
- **Interactive Streamlit Web Interface**: Features chat history, multimodal in-chat image search (direct file attachment or sample photos), and conversational checkout.
- **Production-Ready Architecture**: Modular `src/` layout with separate service layers (`products_api`, `reviews_api`, `orders_api`, `vision_api`).
- **Minimal Multi-Stage Dockerfile**: Slim, containerized image built using Astral `uv` for minimal footprint and fast startup.

---

## 📁 Project Structure

```
shopping_agent/
├── pyproject.toml              # Project dependencies, metadata & tooling config
├── uv.lock                     # Locked dependency versions
├── Dockerfile                  # Multi-stage production container build
├── .dockerignore               # Docker build exclusions
├── .env.example                # Example environment variable template
├── store.db                    # SQLite database (products, reviews, orders)
├── setup_db.py                 # Database initialization and seed script
├── app.py                      # Streamlit web application
├── resources/                  # Sample test images (honey.png, oats.png, etc.)
└── src/
    └── shopping_agent/         # Core application package
        ├── __init__.py         # Public package exports
        ├── config.py           # Centralized configuration & path resolution
        ├── products_api.py     # Product search database operations
        ├── reviews_api.py      # Review and rating aggregation operations
        ├── orders_api.py       # Single & batch order placement operations
        ├── vision_api.py       # Gemini multimodal vision identification
        ├── agent.py            # LangChain agent, tool definitions & CLI main()
        └── utils.py            # Text normalization and message helpers
```

---

## 🛠️ Getting Started

### 1. Prerequisites
- **Python >= 3.14**
- [uv](https://docs.astral.sh/uv/) (recommended fast package manager) or standard `pip`
- Google Gemini API key

### 2. Environment Setup

Clone the repository and create your `.env` file:

```bash
cp .env.example .env
```

Open `.env` and insert your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies

Using `uv`:
```bash
uv sync
```

### 4. Initialize Database (Optional)
The project comes with a pre-seeded `store.db`. If you wish to re-seed or reset it:
```bash
uv run python setup_db.py
```

---

## 🖥️ Running the Application

### Option A: Streamlit Web UI (Recommended)
Launch the interactive web assistant:
```bash
uv run streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Option B: Terminal CLI
Run a direct query test via the package CLI:
```bash
uv run shopping-agent
```

---

## 🐳 Docker Containerization

### 1. Build the Docker Image
The `Dockerfile` uses a multi-stage build with `uv` and `python:3.14-slim` to produce a minimal, non-root image:

```bash
docker build -t shopping-agent:latest .
```

### 2. Run the Container
Pass your `GEMINI_API_KEY` into the container:

```bash
docker run -d \
  -p 8501:8501 \
  -e GEMINI_API_KEY="your_actual_api_key_here" \
  --name shopping-agent-app \
  shopping-agent:latest
```

Access the UI at `http://localhost:8501`.

---

## 📦 Package APIs

The core services can also be used as standard Python modules:

```python
from shopping_agent import (
    agent,
    search_products_db,
    get_product_rating,
    place_orders,
    get_orders
)

# Search items
products = search_products_db(query="honey", max_price=20.0, is_organic=True)

# Fetch ratings
rating = get_product_rating(product_id=1)

# Place batch order in one call
order_receipt = place_orders(product_ids=[1, 3])
```

