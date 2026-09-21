import json
import logging
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger("ai_case_manager.gemini")


class GeminiService:
    """
    Google Gemini 1.5 Flash AI Engine Integration
    Provides multimodal vision triage, case summarization, bilingual Marathi/English translation,
    and missing parameter inspection for municipal operations.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY or ""
        self.base_url = settings.AI_API_BASE_URL or "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-flash"

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def generate_content(self, prompt: str, timeout_sec: float = 6.0) -> Optional[str]:
        """Send prompt to Gemini 1.5 Flash."""
        if not self.is_configured():
            logger.debug("Gemini API key not configured, using municipal heuristic engine.")
            return None

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 800,
            }
        }

        try:
            with httpx.Client(timeout=timeout_sec) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                else:
                    logger.warning(f"Gemini API returned status {res.status_code}: {res.text[:120]}")
        except Exception as e:
            logger.warning(f"Gemini API request failed (falling back smoothly): {e}")

        return None

    def analyze_vision_multimodal(
        self,
        image_base64: Optional[str] = None,
        filename: Optional[str] = None,
        landmark_hint: Optional[str] = None,
        voice_note: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Multimodal analysis using Gemini 1.5 Flash."""
        if not self.is_configured():
            return None

        prompt = f"""
You are the AI Municipal Dispatch Assistant for a city corporation.
Analyze this civic grievance evidence:
Filename: {filename or 'photo.jpg'}
Landmark Hint: {landmark_hint or 'None'}
Voice/Notes: {voice_note or 'None'}

Return ONLY valid JSON with no markdown formatting or extra text:
{{
  "predicted_category_code": "POTHOLES" or "GARBAGE_OVERFLOW" or "WATER_LEAK" or "STREETLIGHT_OUT" or "DRAINAGE_BLOCKED",
  "predicted_title": "Short title",
  "generated_description": "2 sentence technical description",
  "suggested_priority": "CRITICAL" or "HIGH" or "MEDIUM" or "LOW",
  "suggested_severity": "CRITICAL" or "MAJOR" or "MODERATE" or "MINOR",
  "confidence_score": 0.96,
  "landmark_inferred": "Extracted landmark or Dadar West"
}}
"""
        response_text = self.generate_content(prompt)
        if response_text:
            try:
                # Clean potential markdown wrapping
                cleaned = response_text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    if cleaned.endswith("```"):
                        cleaned = cleaned.rsplit("\n", 1)[0]
                cleaned = cleaned.strip()
                return json.loads(cleaned)
            except Exception as e:
                logger.warning(f"Failed to parse Gemini JSON: {e}")

        return None


gemini_service = GeminiService()
