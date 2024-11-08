import os
from typing import Optional

from evals.api import CompletionFn, CompletionResult
from evals.prompt.base import CompletionPrompt
from evals.record import record_sampling

import requests
import json
import time
import random
from tenacity import retry, stop_after_attempt, wait_random

import openai


class LangChainLLMCompletionResult(CompletionResult):
    def __init__(self, response) -> None:
        self.response = response

    def get_completions(self) -> list[str]:
        return [self.response.strip()]


class RouterCompletionFn(CompletionFn):
    def __init__(self, llm_kwargs: Optional[dict] = None, **kwargs) -> None:
        self.router_url = 'https://mintii-router-500540193826.us-central1.run.app/route/mintiiv0'
        self.headers = {
            'X-API-Key': 'ac6c73c1-3e20-49ce-b0eb-7e3d0f82e7be',
            'Content-Type': 'application/json'
        }

    def call_router(self, prompt: str) -> str:
        data = {"prompt": prompt}
        response = self._post_request(data)
        if 'status_code' in response and response['status_code'] != 200:
            raise Exception('Router error')
        
        # Assuming 'response' is a dictionary and doesn't require .json() parsing
        response_data = response  # Since response is already a dictionary
        message_content = response_data.get("message_content", "")
        
        return message_content

    @retry(stop=stop_after_attempt(3))
    def _post_request(self, data):
        response = requests.post(self.router_url, headers=self.headers, json=data)
        response = response.json()
        return response


    def __call__(self, prompt, **kwargs) -> LangChainLLMCompletionResult:
        prompt = CompletionPrompt(prompt).to_formatted_prompt()
        response = self.call_router(prompt)
        record_sampling(prompt=prompt, sampled=response)
        return LangChainLLMCompletionResult(response)