from typing import Optional

from .embedding_service import EmbeddingService
from .log_parser import LogParser
from .log_analyzer import LogAnalyzer
from .rag_pipeline import IncidentRAGPipeline
from .triage_generator import TriageGenerator
from .vector_store import LocalVectorStore
from .config import Config


class IncidentAssistantAgent:
    """
    Agent-style orchestration layer:
    1. Retrieve similar historical incidents from KB
    2. Parse and retrieve relevant current log snippets
    3. Analyze logs
    4. Generate a final triage note using both historical + current evidence
    """

    def __init__(self):
        self.pipeline = IncidentRAGPipeline()
        self.embedding_service = EmbeddingService()
        self.log_parser = LogParser()
        self.log_analyzer = LogAnalyzer()
        self.log_vector_store = LocalVectorStore()
        self.triage_generator = TriageGenerator()
        self._log_chunks = []

    def build_knowledge_base(self, incident_dir: str = "incidents"):
        self.pipeline.build_knowledge_base(incident_dir=incident_dir)

    def build_log_index_from_text(self, log_text: str):
        self._log_chunks = self.log_parser.parse_text(log_text)
        if not self._log_chunks:
            self.log_vector_store.index = None
            self.log_vector_store.chunks = []
            return

        embeddings = [
            self.embedding_service.get_embedding(self._format_log_chunk(chunk))
            for chunk in self._log_chunks
        ]
        self.log_vector_store.build_index(embeddings, self._log_chunks)

    def build_log_index_from_file(self, path: str):
        chunks = self.log_parser.load_file(path)
        self._log_chunks = chunks
        if not self._log_chunks:
            self.log_vector_store.index = None
            self.log_vector_store.chunks = []
            return

        embeddings = [
            self.embedding_service.get_embedding(self._format_log_chunk(chunk))
            for chunk in self._log_chunks
        ]
        self.log_vector_store.build_index(embeddings, self._log_chunks)

    def retrieve_relevant_logs(self, new_incident: str, top_k: Optional[int] = None) -> list[dict]:
        if top_k is None:
            top_k = min(5, Config.TOP_K)

        if self.log_vector_store.index is None:
            return []

        query_embedding = self.embedding_service.get_embedding(new_incident)
        return self.log_vector_store.search(query_embedding=query_embedding, top_k=top_k)

    def run(self, new_incident: str, log_text: Optional[str] = None, log_file: Optional[str] = None) -> dict:
        if log_text:
            self.build_log_index_from_text(log_text)
        elif log_file:
            self.build_log_index_from_file(log_file)

        similar_incidents = self.pipeline.retrieve_similar_incidents(new_incident)
        relevant_logs = self.retrieve_relevant_logs(new_incident)
        log_analysis = self.log_analyzer.analyze(new_incident, relevant_logs)

        triage_note = self.triage_generator.generate_with_logs(
            new_incident=new_incident,
            similar_incidents=similar_incidents,
            relevant_logs=relevant_logs,
            log_analysis=log_analysis,
        )

        return {
            "new_incident": new_incident,
            "similar_incidents": similar_incidents,
            "relevant_logs": relevant_logs,
            "log_analysis": log_analysis,
            "triage_note": triage_note,
        }

    @staticmethod
    def _format_log_chunk(chunk: dict) -> str:
        return f"""
Source: {chunk.get('source', 'runtime_logs')}
Timestamp: {chunk.get('timestamp', 'unknown')}
Level: {chunk.get('level', 'unknown')}
Service: {chunk.get('service', 'unknown')}
Error Hints: {", ".join(chunk.get('error_hints', []))}
{chunk.get('text', '')}
""".strip()