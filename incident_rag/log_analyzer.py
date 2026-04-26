from openai import OpenAI
from .config import Config


class LogAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.GENERATION_MODEL

    def build_prompt(self, new_incident: str, relevant_logs: list[dict]) -> str:
        log_context = ""
        for i, item in enumerate(relevant_logs, start=1):
            log_context += f"""
Relevant Log Chunk {i}
Timestamp: {item.get('timestamp', 'unknown')}
Level: {item.get('level', 'unknown')}
Service: {item.get('service', 'unknown')}
Error Hints: {", ".join(item.get('error_hints', []))}
Content:
{item['text']}
"""

        return f"""
You are an expert production incident analyst.

A new incident has been reported:

{new_incident}

Relevant runtime log snippets:

{log_context}

Analyze only the evidence shown above and produce:
1. What the logs suggest
2. Likely technical failure pattern
3. Important unknowns / missing evidence
4. Confidence level

Be concise and practical. Do not invent facts not present in the logs.
"""

    def analyze(self, new_incident: str, relevant_logs: list[dict]) -> str:
        if not relevant_logs:
            return "No relevant logs were provided or retrieved."

        prompt = self.build_prompt(new_incident, relevant_logs)
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.2,
            max_output_tokens=700,
        )
        return response.output_text