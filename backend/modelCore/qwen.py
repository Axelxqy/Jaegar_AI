from mlx_lm import load, stream_generate

from .interface import JaegarInterface


class QwenModel(JaegarInterface):

    def __init__(self, model_path: str):
        self.model, self.tokenizer = load(model_path)

    def generate(self, prompt: str) -> str:
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        prompt_tokens = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
        )

        response = []

        for generation in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt_tokens,
            max_tokens=1000,
        ):
            response.append(generation.text)

        return "".join(response)