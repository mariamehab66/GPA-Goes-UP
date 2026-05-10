import os
import logging

from google import genai

log = logging.getLogger(__name__)

_client = genai.Client(
    api_key=os.environ.get(
        "GEMINI_API_KEY",
        ""
    )
)


def ask_gemini(prompt: str) -> str:

    try:

        response = _client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt,
        )

        return response.text.strip()

    except Exception as e:

        log.exception(
            "Gemini API call failed"
        )

        error_text = str(e)

        # ==========================================
        # RATE LIMIT / QUOTA EXCEEDED
        # ==========================================

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        ):

            return (
                "The AI explanation service is temporarily "
                "rate-limited. Core recommendation logic "
                "is still functioning normally."
            )

        # ==========================================
        # GENERIC FAILURE
        # ==========================================

        return (
            "Sorry, the AI advisor is temporarily unavailable. "
            "Please try again later."
        )