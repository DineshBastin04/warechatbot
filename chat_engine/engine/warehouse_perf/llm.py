"""
Per-workspace narrative LLM, built from THAT workspace's llm_config.

Mirrors how initialize_vanna_instance picks a backend (model_type 'openai' ->
OpenAI chat completions with the workspace's api_key/model_name; 'ollama' ->
the local Ollama server) without constructing a Vanna instance or touching the
global `vn`. The Ollama host comes from WPA_OLLAMA_HOST (default
http://localhost:11434, the same default engine/ollama uses) — never from
user input. Output is treated as untrusted narrative text only: it is
validated against the findings before use (reporting.validate_narrative) and
is never parsed for instructions, SQL or recipients.
"""
import os

LLM_TIMEOUT_SECONDS = float(os.environ.get("WPA_LLM_TIMEOUT_SECONDS", "60"))


class Narrator:
    def complete(self, system_prompt, user_prompt):
        raise NotImplementedError


class OpenAINarrator(Narrator):
    def __init__(self, api_key, model):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, timeout=LLM_TIMEOUT_SECONDS, max_retries=1)
        self.model = model

    def complete(self, system_prompt, user_prompt):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return (resp.choices[0].message.content or "").strip() if resp.choices else ""


class OllamaNarrator(Narrator):
    def __init__(self, model):
        import ollama
        from httpx import Timeout
        host = os.environ.get("WPA_OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.Client(host, timeout=Timeout(LLM_TIMEOUT_SECONDS))
        self.model = model if ":" in model else model + ":latest"

    def complete(self, system_prompt, user_prompt):
        resp = self.client.chat(model=self.model, stream=False, messages=[
            {"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])
        return (resp["message"]["content"] or "").strip()


def build_narrator(llm_config):
    """Returns a Narrator or None when the workspace has no usable LLM."""
    cfg = llm_config or {}
    kind = cfg.get("model_type")
    model = cfg.get("model_name")
    if not model:
        return None
    if kind == "openai":
        if not cfg.get("api_key"):
            return None
        return OpenAINarrator(cfg["api_key"], model)
    if kind == "ollama":
        return OllamaNarrator(model)
    return None
