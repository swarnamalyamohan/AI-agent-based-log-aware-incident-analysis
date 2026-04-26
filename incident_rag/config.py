import os


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "text-embedding-3-small"
    )

    GENERATION_MODEL = os.getenv(
        "GENERATION_MODEL",
        "gpt-4.1-mini"
    )

    TOP_K = int(os.getenv("TOP_K", "5"))