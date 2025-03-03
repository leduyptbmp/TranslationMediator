from googletrans import Translator
from typing import Optional
import logging

class TranslationService:
    def __init__(self):
        self.translator = Translator()
        self.logger = logging.getLogger(__name__)

    def translate_text(self, text: str, target_lang: str = 'en', source_lang: str = None) -> Optional[str]:
        try:
            if not text:
                return None

            translation = self.translator.translate(
                text,
                dest=target_lang,
                src=source_lang if source_lang else 'auto'
            )
            return translation.text

        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            return None

    def detect_language(self, text: str) -> Optional[str]:
        try:
            detection = self.translator.detect(text)
            return detection.lang
        except Exception as e:
            self.logger.error(f"Language detection error: {str(e)}")
            return None
