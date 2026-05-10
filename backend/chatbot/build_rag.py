import json
import os
from sentence_transformers import SentenceTransformer
import numpy as np

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

model = SentenceTransformer(MODEL_NAME)

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_DOCS = os.path.join(_BACKEND, "..", "docs")

# LOAD RULES
with open(os.path.join(_BACKEND, "Rule_Engine.json"), "r", encoding="utf-8") as f:
    rules_json = json.load(f)

with open(os.path.join(_DOCS, "Academic System Rules.docx.txt"), "r", encoding="utf-8") as f:
    english_rules = f.read()

with open(os.path.join(_DOCS, "Academic Rules in Arabic.docx.txt"), "r", encoding="utf-8") as f:
    arabic_rules = f.read()

# CREATE CHUNKS
chunks = []

# JSON rules
for key, value in rules_json.items():

    chunk = {
        "source": "rule_engine_json",
        "title": key,
        "text": json.dumps(value, ensure_ascii=False, indent=2)
    }

    chunks.append(chunk)

# English rules
for section in english_rules.split("\n\n"):

    section = section.strip()

    if len(section) < 40:
        continue

    chunks.append({
        "source": "english_rules",
        "title": "English Rules",
        "text": section
    })

# Arabic rules
for section in arabic_rules.split("\n\n"):

    section = section.strip()

    if len(section) < 40:
        continue

    chunks.append({
        "source": "arabic_rules",
        "title": "Arabic Rules",
        "text": section
    })

# CREATE EMBEDDINGS
texts = [c["text"] for c in chunks]

embeddings = model.encode(texts).tolist()


# SAVE
with open(os.path.join(_HERE, "rules_chunks.json"), "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

with open(os.path.join(_HERE, "embeddings_store.json"), "w", encoding="utf-8") as f:
    json.dump(embeddings, f)

print(f"Built RAG store with {len(chunks)} chunks.")