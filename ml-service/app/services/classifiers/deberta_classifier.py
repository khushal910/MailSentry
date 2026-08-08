import logging
import os
import warnings
from datetime import datetime, timezone
from typing import Any, Dict, Optional

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*use_return_dict.*")

from app.core.config import settings
from app.core.model_registry import get_model_config
from app.services.classifiers.base import BaseClassifier

logger = logging.getLogger("ml_service.deberta_classifier")


class DebertaClassifier(BaseClassifier):
    """
    DeBERTa-v3 Spam Classifier Provider using Hugging Face Transformers and PEFT LoRA adapter.
    Base Model: microsoft/deberta-v3-base
    Target Modules: query_proj, key_proj, value_proj
    """

    BASE_MODEL_NAME = "microsoft/deberta-v3-base"
    ADAPTER_NAME = os.getenv(
        "DEBERTA_ADAPTER", "ssheroz/spam-email-classifier-deberta-v3-base-r8"
    )

    def __init__(self):
        self.tokenizer: Any | None = None
        self.model: Any | None = None
        self.device: Any = None
        self._is_loaded: bool = False
        self.version: str = "deberta-v3-r8-v1.0.0"
        self.config = get_model_config("deberta-v3-base") or {}

        self.load()

    @property
    def provider_name(self) -> str:
        return "deberta-v3-base"

    @property
    def device_name(self) -> str:
        if self.device is not None:
            return str(self.device.type)
        return "unknown"

    @property
    def is_loaded(self) -> bool:
        return (
            self._is_loaded
            and self.model is not None
            and self.tokenizer is not None
        )

    @property
    def details(self) -> Dict[str, Any]:
        return {
            "provider": "deberta-v3-base",
            "model_name": "DeBERTa-v3-base",
            "loaded": self.is_loaded,
            "device": self.device_name,
            "base_model": self.BASE_MODEL_NAME,
            "adapter": self.ADAPTER_NAME,
            "lora_enabled": settings.LORA_ENABLED,
            "lora_rank": settings.LORA_R,
            "target_modules": ["query_proj", "key_proj", "value_proj"],
            "version": self.version,
        }

    def load(self) -> bool:
        logger.info(
            f"Initializing DeBERTa-v3 classifier: Base='{self.BASE_MODEL_NAME}', Adapter='{self.ADAPTER_NAME}'"
        )

        # Apply custom HF_HOME or TRANSFORMERS_CACHE if set in settings/env
        if settings.HF_HOME:
            os.environ["HF_HOME"] = settings.HF_HOME
            os.environ["TRANSFORMERS_CACHE"] = settings.HF_HOME

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            from peft import PeftModel
        except ImportError as err:
            missing_pkg = getattr(err, "name", str(err))
            msg = (
                f"Missing required DeBERTa dependency '{missing_pkg}'. "
                f"Please verify PyTorch, transformers, sentencepiece, peft, and safetensors are installed."
            )
            logger.error(msg)
            raise RuntimeError(msg) from err

        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"DeBERTa-v3 classifier selected device: {self.device}")

            logger.info(
                f"Loading DeBERTa-v3 tokenizer from '{self.BASE_MODEL_NAME}'..."
            )
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.BASE_MODEL_NAME, use_fast=False
                )
            except Exception as tok_err:
                logger.warning(f"Initial DeBERTa tokenizer load failed ({tok_err}). Cleaning cache and retrying with DebertaV2Tokenizer...")
                import shutil
                cache_dir = os.path.expanduser("~/.cache/huggingface/hub/models--microsoft--deberta-v3-base")
                if os.path.exists(cache_dir):
                    try:
                        shutil.rmtree(cache_dir, ignore_errors=True)
                    except Exception:
                        pass
                try:
                    from transformers import DebertaV2Tokenizer
                    self.tokenizer = DebertaV2Tokenizer.from_pretrained(self.BASE_MODEL_NAME, force_download=True)
                except Exception:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.BASE_MODEL_NAME, force_download=True)




            logger.info(
                f"Loading base sequence classification model from '{self.BASE_MODEL_NAME}'..."
            )
            base_model = AutoModelForSequenceClassification.from_pretrained(
                self.BASE_MODEL_NAME, num_labels=2
            )

            # Load LoRA adapter if enabled & available
            if settings.LORA_ENABLED:
                try:
                    logger.info(
                        f"Loading LoRA adapter from '{self.ADAPTER_NAME}'..."
                    )
                    self.model = PeftModel.from_pretrained(
                        base_model, self.ADAPTER_NAME
                    )
                except Exception as adapter_exc:
                    logger.warning(
                        f"Could not load LoRA adapter '{self.ADAPTER_NAME}': {adapter_exc}. "
                        f"Proceeding with fine-tuned base model architecture."
                    )
                    self.model = base_model
            else:
                self.model = base_model

            self.model.to(self.device)
            self.model.eval()

            # Startup validation: Perform warm-up test inference
            logger.info("Executing startup warm-up test inference for DeBERTa-v3...")
            warmup_res = self.predict(
                subject="Startup Check", body="Validating DeBERTa model loading."
            )
            if not warmup_res or "predicted_label" not in warmup_res:
                raise RuntimeError("DeBERTa warm-up test prediction returned invalid response schema.")

            self._is_loaded = True
            logger.info("DeBERTa-v3 model and tokenizer successfully loaded into memory and validated.")
            return True

        except Exception as exc:
            msg = f"Failed to load DeBERTa-v3 model/adapter: {exc}"
            logger.error(msg)
            raise RuntimeError(msg) from exc

    def predict(
        self, subject: str, body: str, threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        if not self.model or not self.tokenizer:
            self.load()

        import torch

        eff_threshold = (
            threshold if threshold is not None else settings.CLASSIFICATION_THRESHOLD
        )

        subj_clean = (subject or "").strip()
        body_clean = (body or "").strip()
        raw_text = f"Subject: {subj_clean}\n\n{body_clean}".strip()
        if not raw_text or raw_text == "Subject:":
            raw_text = "Subject: \n\nEmpty body"

        inputs = self.tokenizer(
            raw_text, return_tensors="pt", truncation=True, max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs, return_dict=True)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

        safe_prob = float(probs[0])
        spam_prob = float(probs[1])

        is_spam = spam_prob >= eff_threshold
        predicted_label = "spam" if is_spam else "safe"
        predicted_score = round(spam_prob if is_spam else safe_prob, 4)

        return {
            "subject": subj_clean[:255],
            "predicted_label": predicted_label,
            "predicted_score": predicted_score,
            "probabilities": {
                "safe": round(safe_prob, 4),
                "spam": round(spam_prob, 4),
                "ham": round(safe_prob, 4),
            },
            "classified_at": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
            "model": "deberta-v3-base",
        }
