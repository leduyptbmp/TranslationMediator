from googletrans import Translator, LANGUAGES
from typing import Optional, Tuple
import logging
import time
from functools import wraps

def retry_on_error(retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logging.warning(f"Translation attempt {i+1} failed: {str(e)}")
                    if i < retries - 1:
                        time.sleep(delay * (i + 1))  # Exponential backoff
            logging.error(f"All translation attempts failed: {str(last_error)}")
            return None
        return wrapper
    return decorator

class TranslationService:
    def __init__(self):
        self.translator = Translator()
        self.logger = logging.getLogger(__name__)

    def _is_valid_language(self, lang_code: str) -> bool:
        return lang_code.lower() in LANGUAGES

    @retry_on_error(retries=3)
    def translate_text(self, text: str, target_lang: str = 'en', source_lang: str = None) -> Optional[str]:
        try:
            if not text or not text.strip():
                self.logger.warning("Empty text provided for translation")
                return None

            # Validate target language
            if not self._is_valid_language(target_lang):
                self.logger.error(f"Invalid target language code: {target_lang}")
                return None

            # Validate source language if provided
            if source_lang and not self._is_valid_language(source_lang):
                self.logger.error(f"Invalid source language code: {source_lang}")
                return None

            self.logger.info(f"Attempting to translate text to {target_lang}")
            self.logger.debug(f"Text to translate: {text[:50]}...")  # Log first 50 chars

            translation = self.translator.translate(
                text,
                dest=target_lang,
                src=source_lang if source_lang else 'auto'
            )

            self.logger.info(
                f"Translation successful. Source language detected: {translation.src}"
            )
            self.logger.debug(f"Translated text: {translation.text[:50]}...")
            return translation.text

        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            raise

    @retry_on_error(retries=3)
    def detect_language(self, text: str) -> Optional[str]:
        try:
            if not text or not text.strip():
                self.logger.warning("Empty text provided for language detection")
                return None

            self.logger.info("Attempting to detect language")
            detection = self.translator.detect(text)

            if detection and self._is_valid_language(detection.lang):
                self.logger.info(f"Language detection successful: {detection.lang}")
                return detection.lang
            else:
                self.logger.warning(f"Invalid or unsupported language detected: {detection.lang if detection else 'None'}")
                return None

        except Exception as e:
            self.logger.error(f"Language detection error: {str(e)}")
            raise