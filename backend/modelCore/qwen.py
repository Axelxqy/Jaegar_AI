from mlx_lm import load, stream_generate

from .interface import JaegarInterface


class QwenModel(JaegarInterface):

    def __init__(self, model_path: str):
        self.model, self.tokenizer = load(model_path)

    def generate(self, messages: list[dict[str, str]]) -> str:
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

        raw_output = "".join(response)

        print("\n===== RAW GENERATION =====")
        print(repr(raw_output))
        print("==========================\n")

        # Step 3: Separate the thinking and final answer
        if "</think>" in raw_output:
            thinking, answer = raw_output.split("</think>", 1)
            thinking = thinking.removeprefix("<think>").strip()
            answer = answer.strip()

            print("===== THINKING =====")
            print(thinking)

            print("===== FINAL ANSWER =====")
            print(answer)
        else:
            print("No visible thinking separator found.")


        return raw_output