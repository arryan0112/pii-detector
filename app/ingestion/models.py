from dataclasses import dataclass, field


@dataclass
class TextChunk:
    text: str
    source_file: str
    format: str
    location: str
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class IngestionResult:
    filename: str
    format: str
    chunks: list[TextChunk]
    errors: list[str]
    total_chars: int = 0

    def __post_init__(self):
        self.total_chars = sum(len(c.text) for c in self.chunks)