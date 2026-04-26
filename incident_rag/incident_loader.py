import re
from pathlib import Path


def read_markdown_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def extract_metadata(content: str, file_name: str) -> dict:
    metadata = {
        "incident_id": file_name.replace(".md", ""),
        "service": "unknown",
        "severity": "unknown",
        "date": "unknown"
    }

    service_match = re.search(r"\*\*Service\*\*:\s*(.+)", content)
    severity_match = re.search(r"\*\*Severity\*\*:\s*(.+)", content)
    date_match = re.search(r"\*\*Date\*\*:\s*(.+)", content)

    if service_match:
        metadata["service"] = service_match.group(1).strip()

    if severity_match:
        metadata["severity"] = severity_match.group(1).strip()

    if date_match:
        metadata["date"] = date_match.group(1).strip()

    return metadata


def split_into_sections(content: str) -> list[dict]:
    pattern = r"##\s+(.+?)\n"
    parts = re.split(pattern, content)

    sections = []

    for i in range(1, len(parts), 2):
        section_name = parts[i].strip()
        section_text = parts[i + 1].strip() if i + 1 < len(parts) else ""

        if section_text:
            sections.append({
                "section": section_name.lower().replace(" ", "_"),
                "text": section_text
            })

    return sections


def load_incident_chunks(incident_dir: str = "incidents") -> list[dict]:
    chunks = []

    for path in Path(incident_dir).glob("*.md"):
        content = read_markdown_file(str(path))
        metadata = extract_metadata(content, path.name)
        sections = split_into_sections(content)

        for section in sections:
            chunks.append({
                "incident_id": metadata["incident_id"],
                "service": metadata["service"],
                "severity": metadata["severity"],
                "date": metadata["date"],
                "section": section["section"],
                "text": section["text"],
                "source_file": path.name
            })

    return chunks