from typing import Optional

from .incident_loader import load_incident_chunks
from .embedding_service import EmbeddingService
from .vector_store import LocalVectorStore
from .triage_generator import TriageGenerator
from .config import Config


class IncidentRAGPipeline:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = LocalVectorStore()
        self.triage_generator = TriageGenerator()
        self.chunks = []

    def build_knowledge_base(self, incident_dir: str = "incidents"):
        print("Loading incident documents...")
        self.chunks = load_incident_chunks(incident_dir)

        print(f"Loaded {len(self.chunks)} incident chunks")

        print("Generating embeddings...")
        embeddings = self.embedding_service.embed_chunks(self.chunks)

        print("Building local FAISS index...")
        self.vector_store.build_index(embeddings, self.chunks)

        print("Knowledge base is ready")

    def retrieve_similar_incidents(
        self,
        new_incident: str,
        top_k: Optional[int] = None
    ) -> list[dict]:
        if top_k is None:
            top_k = Config.TOP_K

        query_embedding = self.embedding_service.get_embedding(new_incident)

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )

    def generate_triage_note(
        self,
        new_incident: str,
        top_k: Optional[int] = None
    ) -> dict:
        similar_incidents = self.retrieve_similar_incidents(
            new_incident=new_incident,
            top_k=top_k
        )

        triage_note = self.triage_generator.generate(
            new_incident=new_incident,
            similar_incidents=similar_incidents
        )

        return {
            "new_incident": new_incident,
            "similar_incidents": similar_incidents,
            "triage_note": triage_note
        }