import base64
import json
import os
import pathlib
from typing import TYPE_CHECKING, Union

import json_repair
from pydantic import TypeAdapter
from typing_extensions import Optional, Required, TypedDict

if TYPE_CHECKING:
    from openai import AsyncOpenAI  # Importing OpenAI can be slow on low-power machines

from telegram_signer.utils import UserInput, print_to_user

DEFAULT_MODEL = "gpt-4o"


def encode_image(image: bytes):
    return base64.b64encode(image).decode("utf-8")


class OpenAIConfig(TypedDict, total=False):
    api_key: Required[str]
    base_url: Optional[str]
    model: Optional[str]


class OpenAIConfigManager:
    def __init__(self, workdir: Union[str, pathlib.Path]):
        self.workdir = pathlib.Path(workdir)

    def get_config_file(self) -> pathlib.Path:
        return self.workdir / ".openai_config.json"

    def has_env_config(self):
        return bool(os.environ.get("OPENAI_API_KEY"))

    def has_config(self) -> bool:
        return self.has_env_config() and bool(self.load_file_config())

    def load_file_config(self) -> Optional[dict]:
        config_file = self.get_config_file()
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as fp:
                c = json.load(fp)
            return TypeAdapter(OpenAIConfig).validate_python(c)
        return None

    def save_config(self, api_key: str, base_url: str = None, model: str = None):
        config_file = self.get_config_file()
        config = OpenAIConfig(api_key=api_key, base_url=base_url, model=model)
        with open(config_file, "w", encoding="utf-8") as fp:
            json.dump(config, fp, ensure_ascii=False, indent=2)

    def load_config(self) -> Optional[OpenAIConfig]:
        # Environment variables take precedence
        if self.has_env_config():
            return OpenAIConfig(
                api_key=os.environ["OPENAI_API_KEY"],
                base_url=os.environ.get("OPENAI_BASE_URL"),
                model=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
            )
        return self.load_file_config()

    def ask_for_config(self):
        print_to_user("Configure OpenAI-compatible API settings and save them locally.")
        input_ = UserInput()
        api_key = input_("Enter OPENAI_API_KEY: ").strip()
        while not api_key:
            print_to_user("API key cannot be empty.")
            api_key = input_("Enter OPENAI_API_KEY: ").strip()

        base_url = (
            input_(
                "Enter OPENAI_BASE_URL (optional): "
            ).strip()
            or None
        )
        model = (
            input_(
                f"Enter OPENAI_MODEL (optional, default ({DEFAULT_MODEL})): "
            ).strip()
            or None
        )
        self.save_config(api_key, base_url=base_url, model=model)
        print_to_user("OpenAI config saved.")
        return self.load_config()


def get_openai_client(
    api_key: str = None,
    base_url: str = None,
    **kwargs,
) -> Optional["AsyncOpenAI"]:
    from openai import AsyncOpenAI, OpenAIError

    try:
        return AsyncOpenAI(api_key=api_key, base_url=base_url, **kwargs)
    except OpenAIError:
        return None


class AITools:
    def __init__(self, cfg: OpenAIConfig):
        self.client = get_openai_client(
            api_key=cfg["api_key"], base_url=cfg.get("base_url")
        )
        self.default_model = cfg.get("model") or DEFAULT_MODEL

    async def choose_option_by_image(
        self,
        image: bytes,
        query: str,
        options: list[tuple[int, str]],
        client: "AsyncOpenAI" = None,
        model: str = None,
        temperature=0.1,
    ) -> int:
        sys_prompt = """You are an image recognition assistant. Choose the single best option from the image and question. If none is perfect, choose the closest option. Return JSON only:
    {
      "option": 1,  // Integer option index, starting at 0.
      "reason": "Reason in 30 words or fewer"
    }
    The option field is your selected option.
    """
        client = client or self.client
        model = model or self.default_model
        text_query = f"Question: {query}. Options: {json.dumps(options)}."
        messages = [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_query},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encode_image(image)}"
                        },
                    },
                ],
            },
        ]
        # noinspection PyTypeChecker
        completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            response_format={"type": "json_object"},
            stream=False,
            temperature=temperature,
        )
        message = completion.choices[0].message
        result = json_repair.loads(message.content)
        return int(result["option"])

    async def calculate_problem(
        self,
        query: str,
        sys_prompt: str = "Answer the user's question. Reply with only the answer.",
        client: "AsyncOpenAI" = None,
        model: str = None,
        temperature=0.1,
    ) -> str:
        model = model or self.default_model
        client = client or self.client
        messages = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        text = f"Question: {query}\n\nReply with only the answer. The answer is:"
        messages.append({"role": "user", "content": text})
        # noinspection PyTypeChecker
        completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            stream=False,
            temperature=temperature,
        )
        return completion.choices[0].message.content.strip()

    async def get_reply(
        self,
        sys_prompt: str,
        query: str,
        client: "AsyncOpenAI" = None,
        model: str = None,
    ) -> str:
        model = model or self.default_model
        client = client or self.client
        messages = [
            {
                "role": "system",
                "content": sys_prompt,
            },
            {"role": "user", "content": f"{query}"},
        ]
        # noinspection PyTypeChecker
        completion = await client.chat.completions.create(
            messages=messages,
            model=model,
            stream=False,
        )
        message = completion.choices[0].message
        return message.content


