import re
from pathlib import Path

import chromadb

from rootcause.config import CHROMA_DIR, KNOWLEDGE_DIR

COLLECTION_NAME = "rootcause_knowledge"


def _chunk_markdown_file(path: Path) -> list[dict]:
    """Splits a knowledge markdown file into one chunk per '## ' section,
    pulling out the trailing 'Source: ...' line as a citation."""
    text = path.read_text(encoding="utf-8")
    domain = path.stem
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section.startswith("## "):
            continue
        title, _, body = section.partition("\n")
        title = title.removeprefix("## ").strip()
        source_match = re.search(r"Source:\s*(.+)$", body, flags=re.MULTILINE)
        citation = source_match.group(1).strip() if source_match else "Uncited"
        content = re.sub(r"Source:\s*.+$", "", body, flags=re.MULTILINE).strip()
        chunks.append({
            "id": f"{domain}::{title}",
            "text": f"{title}\n{content}",
            "domain": domain,
            "citation": citation,
            "source_file": path.name,
        })
    return chunks


class KnowledgeStore:
    def __init__(self, persist_dir: Path = CHROMA_DIR, collection_name: str = COLLECTION_NAME):
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def build_index(self, knowledge_dir: Path = KNOWLEDGE_DIR, rebuild: bool = False) -> int:
        if rebuild:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(name=self.collection.name)

        all_chunks = []
        for md_file in sorted(Path(knowledge_dir).glob("*.md")):
            all_chunks.extend(_chunk_markdown_file(md_file))

        if not all_chunks:
            return 0

        self.collection.upsert(
            ids=[c["id"] for c in all_chunks],
            documents=[c["text"] for c in all_chunks],
            metadatas=[
                {"domain": c["domain"], "citation": c["citation"], "source_file": c["source_file"]}
                for c in all_chunks
            ],
        )
        return len(all_chunks)

    def query(self, text: str, n_results: int = 4, domain: str | None = None) -> list[dict]:
        where = {"domain": domain} if domain else None
        results = self.collection.query(query_texts=[text], n_results=n_results, where=where)
        hits = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        for chunk_id, doc, meta, distance in zip(ids, docs, metas, distances):
            hits.append({
                "id": chunk_id,
                "text": doc,
                "domain": meta.get("domain"),
                "citation": meta.get("citation"),
                "source_file": meta.get("source_file"),
                "distance": distance,
            })
        return hits

    def count(self) -> int:
        return self.collection.count()
