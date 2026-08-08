import logging
import warnings
from datetime import datetime, timezone
from typing import Any, Dict, Optional

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*use_return_dict.*")

from app.core.config import settings
from app.services.classifiers.base import BaseClassifier


logger = logging.getLogger("ml_service.roberta_classifier")


class RobertaClassifier(BaseClassifier):
    """
    RoBERTa Spam Classifier Provider using HuggingFace Transformers and PEFT LoRA adapter.
    Base Model: FacebookAI/roberta-base
    Adapter: ssheroz/spam-email-classifier-roberta-r8
    """

    BASE_MODEL_NAME = "FacebookAI/roberta-base"
    ADAPTER_NAME = "ssheroz/spam-email-classifier-roberta-r8"

    def __init__(self):
        self.tokenizer: Any | None = None
        self.model: Any | None = None
        self.device: Any = None
        self._is_loaded: bool = False
        self.version: str = "roberta-r8-v1.0.0"

        self.load()

    @property
    def provider_name(self) -> str:
        return "roberta"

    @property
    def device_name(self) -> str:
        if self.device is not None:
            return str(self.device.type)
        return "unknown"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded and self.model is not None and self.tokenizer is not None

    @property
    def details(self) -> Dict[str, Any]:
        return {
            "provider": "roberta",
            "loaded": self.is_loaded,
            "device": self.device_name,
            "base_model": self.BASE_MODEL_NAME,
            "adapter": self.ADAPTER_NAME,
        }

    def load(self) -> bool:
        logger.info(
            f"Initializing RoBERTa classifier: Base='{self.BASE_MODEL_NAME}', Adapter='{self.ADAPTER_NAME}'"
        )
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            from peft import PeftModel
        except ImportError as err:
            missing_pkg = getattr(err, "name", str(err))
            msg = (
                f"Missing required RoBERTa dependency '{missing_pkg}'. "
                f"Please install torch, transformers, peft, and safetensors."
            )
            logger.error(msg)
            raise RuntimeError(msg) from err

        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"RoBERTa classifier selected device: {self.device}")

            logger.info(f"Loading RoBERTa tokenizer from '{self.BASE_MODEL_NAME}'...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.BASE_MODEL_NAME)

            logger.info(
                f"Loading base sequence classification model from '{self.BASE_MODEL_NAME}'..."
            )
            base_model = AutoModelForSequenceClassification.from_pretrained(
                self.BASE_MODEL_NAME, num_labels=2
            )

            logger.info(f"Loading LoRA adapter from '{self.ADAPTER_NAME}'...")
            self.model = PeftModel.from_pretrained(base_model, self.ADAPTER_NAME)

            self.model.to(self.device)
            self.model.eval()

            self._is_loaded = True
            logger.info("RoBERTa model and LoRA adapter successfully loaded into memory.")
            return True

        except Exception as exc:
            msg = f"Failed to download or load RoBERTa model/adapter: {exc}"
            logger.error(msg)
            raise RuntimeError(msg) from exc

    def predict(
        self, subject: str, body: str, threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        if not self.is_loaded:
            self.load()

        import torch

        eff_threshold = (
            threshold if threshold is not None else settings.CLASSIFICATION_THRESHOLD
        )

        # Raw email text formatting for Transformer model
        subj_clean = (subject or "").strip()
        body_clean = (body or "").strip()
        raw_text = f"Subject: {subj_clean}\n\n{body_clean}".strip()
        if not raw_text or raw_text == "Subject:":
            raw_text = "Subject: \n\nEmpty body"

        # Tokenize raw text (NO TF-IDF or Scikit-Learn preprocessing)
        inputs = self.tokenizer(
            raw_text, return_tensors="pt", truncation=True, max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs, return_dict=True)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()


        # In binary spam models: Index 0 = safe/ham, Index 1 = spam
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
            "model": "roberta",
        }
