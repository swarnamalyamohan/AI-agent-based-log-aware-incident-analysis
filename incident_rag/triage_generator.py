from openai import OpenAI
from .config import Config


class TriageGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.GENERATION_MODEL

    def build_prompt(self, new_incident: str, similar_incidents: list[dict]) -> str:
        context = ""
        for index, item in enumerate(similar_incidents, start=1):
            context += f"""
Similar Incident {index}
Incident ID: {item['incident_id']}
Service: {item['service']}
Severity: {item['severity']}
Date: {item['date']}
Section: {item['section']}
Similarity Score: {item['score']:.2f}
Content: {item['text']}
"""

        prompt = f"""
You are an expert SRE assistant.

A new production incident has been reported.

NEW INCIDENT:
{new_incident}

SIMILAR HISTORICAL INCIDENTS:
{context}

Generate a triage recommendation using only the historical incidents above.

Return the answer with these sections:
1. Likely Root Cause
2. Recommended Immediate Actions
3. Similar Past Incidents
4. Prevention Suggestions
5. Confidence and Assumptions

Be practical, concise, and useful for an on-call engineer.
Do not invent facts that are not supported by the provided historical incidents.
"""
        return prompt

    def build_prompt_with_logs(
        self,
        new_incident: str,
        similar_incidents: list[dict],
        relevant_logs: list[dict],
        log_analysis: str,
    ) -> str:
        incident_context = ""
        for index, item in enumerate(similar_incidents, start=1):
            incident_context += f"""
Similar Incident {index}
Incident ID: {item['incident_id']}
Service: {item['service']}
Severity: {item['severity']}
Date: {item['date']}
Section: {item['section']}
Similarity Score: {item['score']:.2f}
Content: {item['text']}
"""

        log_context = ""
        for index, item in enumerate(relevant_logs, start=1):
            log_context += f"""
Relevant Log Chunk {index}
Timestamp: {item.get('timestamp', 'unknown')}
Level: {item.get('level', 'unknown')}
Service: {item.get('service', 'unknown')}
Similarity Score: {item.get('score', 0.0):.2f}
Error Hints: {", ".join(item.get('error_hints', []))}
Content:
{item['text']}
"""

        return f"""
You are an expert SRE assistant.

A new production incident has been reported.

NEW INCIDENT:
{new_incident}

SIMILAR HISTORICAL INCIDENTS:
{incident_context}

CURRENT RUNTIME LOG EVIDENCE:
{log_context}

PRELIMINARY LOG ANALYSIS:
{log_analysis}

Use both the historical incidents and the runtime log evidence.

Return the answer with these sections:
1. Likely Root Cause
2. Evidence from Logs
3. Recommended Immediate Actions
4. Similar Past Incidents
5. Prevention Suggestions
6. Confidence and Assumptions
7. Draft Incident Update

Be practical, concise, and useful for an on-call engineer.
Do not invent facts that are not supported by the provided evidence.
Clearly separate confirmed evidence from assumptions.
"""

    def generate(self, new_incident: str, similar_incidents: list[dict]) -> str:
        prompt = self.build_prompt(new_incident, similar_incidents)
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.2,
            max_output_tokens=900,
        )
        return response.output_text

    def generate_with_logs(
        self,
        new_incident: str,
        similar_incidents: list[dict],
        relevant_logs: list[dict],
        log_analysis: str,
    ) -> str:
        prompt = self.build_prompt_with_logs(
            new_incident=new_incident,
            similar_incidents=similar_incidents,
            relevant_logs=relevant_logs,
            log_analysis=log_analysis,
        )
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.2,
            max_output_tokens=1200,
        )
        return response.output_text