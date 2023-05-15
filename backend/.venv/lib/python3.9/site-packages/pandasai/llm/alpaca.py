"""Alpaca LLM"""

import requests
from .base import LLM
from ..exceptions import LLMNotFoundError


class Alpaca(LLM):
    """Alpaca LLM"""

    max_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.75
    top_k: float = 40.0
    beams: int = 4

    def __init__(
        self,
        **kwargs,
    ):
        self._set_params(**kwargs)

    def _set_params(self, **kwargs):
        valid_params = [
            "max_tokens",
            "temperature",
            "top_p",
            "top_k",
            "beams",
        ]
        for key, value in kwargs.items():
            if key in valid_params:
                setattr(self, key, value)

    def call(self, instruction: str, value: str) -> str:
        """Call Alpaca LLM"""
        self.last_prompt = str(instruction) + str(value)

        response = requests.post(
            "https://tloen-alpaca-lora.hf.space/run/predict",
            json={
                "data": [
                    instruction,
                    value,
                    self.temperature,
                    self.top_p,
                    self.top_k,
                    self.beams,
                    self.max_tokens,
                ]
            },
            timeout=60,
        ).json()

        if "error" in response:
            raise LLMNotFoundError("Error while calling Alpaca LLM")

        return response["data"][0]

    @property
    def type(self) -> str:
        return "alpaca-lora"
