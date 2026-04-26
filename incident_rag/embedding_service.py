from openai import OpenAI
from .config import Config


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.EMBEDDING_MODEL

    def get_embedding(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding

    def embed_chunks(self, chunks: list[dict]) -> list[list[float]]:
        embeddings = []

        for index, chunk in enumerate(chunks):
            text = self.format_chunk_for_embedding(chunk)
            embedding = self.get_embedding(text)
            embeddings.append(embedding)

            if (index + 1) % 10 == 0:
                print(f"Embedded {index + 1}/{len(chunks)} chunks")

        return embeddings

    @staticmethod
    def format_chunk_for_embedding(chunk: dict) -> str:
        return f"""
Incident ID: {chunk['incident_id']}
Service: {chunk['service']}
Severity: {chunk['severity']}
Section: {chunk['section']}

{chunk['text']}
""".strip()