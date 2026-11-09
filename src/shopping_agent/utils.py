"""Console and output helpers shared across the project."""


def get_text(msg) -> str:
    """Return readable text from a message.

    LangChain message ``content`` can be either:
      - a plain string, or
      - a list of content blocks like
        [{"type": "text", "text": "...", "extras": {...}}, ...]

    This function normalizes both cases to a single string containing
    only the text parts.
    """
    if isinstance(msg.content, str):
        return msg.content

    return "\n".join(
        block["text"]
        for block in msg.content
        if isinstance(block, dict) and block.get("type") == "text"
    )

