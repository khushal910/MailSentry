"""
Model Loader Service Stub for MailSentry backend.
Model deserialization and serving is handled by independent ml-service microservice.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class BaseModelLoader:
    def load(self, champion_dir: str, metadata: dict) -> Any:
        return None


class ModelLoaderFactory:
    @classmethod
    def create(cls, metadata: dict) -> BaseModelLoader:
        return BaseModelLoader()
