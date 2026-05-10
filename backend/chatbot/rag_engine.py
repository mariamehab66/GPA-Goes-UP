import json
import os
import re
import logging

log = logging.getLogger(__name__)

KNOWLEDGE = []


def load_knowledge():

    global KNOWLEDGE

    try:

        knowledge_path = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "academic_knowledge.json"
        )

        with open(
            knowledge_path,
            "r",
            encoding="utf-8"
        ) as f:

            KNOWLEDGE = json.load(f)

        log.info(
            "Loaded %d academic knowledge entries",
            len(KNOWLEDGE)
        )

    except Exception:

        log.exception(
            "Failed to load academic_knowledge.json"
        )


def _tokenize(text: str):

    text = text.lower()

    # Remove punctuation
    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text
    )

    return set(text.split())


def retrieve_relevant_rules(
    query: str,
    top_k: int = 3
):

    if not KNOWLEDGE:

        load_knowledge()

    query_tokens = _tokenize(query)

    scored = []

    for idx, data in enumerate(KNOWLEDGE):

        searchable_text = " ".join([

            data.get("english", ""),

            data.get("arabic", ""),

            " ".join(
                data.get("tags", [])
            ),

            " ".join(
                data.get("examples", [])
            )
        ])

        rule_tokens = _tokenize(
            searchable_text
        )

        score = len(
            query_tokens.intersection(
                rule_tokens
            )
        )

        if score > 0:

            scored.append(
                (score, idx, data)
            )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    results = []

    for score, idx, data in scored[:top_k]:

        results.append({

            "rule_id":
                f"rule_{idx}",

            "score":
                score,

            "category":
                data.get("category"),

            "english":
                data.get("english"),

            "arabic":
                data.get("arabic"),

            "examples":
                data.get("examples", []),

            "tags":
                data.get("tags", [])
        })

    return results