from datetime import time
from enum import Enum
from typing import ClassVar, List, Literal, Optional, Tuple, Type, Union

from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
)
from typing_extensions import Self, TypeAlias

ChatId: TypeAlias = Union[int, str]


def normalize_chat_username(value: str) -> str:
    return value.strip().lstrip("@").lower()


def parse_chat_id_or_username(value: Union[int, str]) -> ChatId:
    if isinstance(value, int):
        return value
    value = str(value).strip()
    if not value:
        raise ValueError("chat_id cannot be empty")
    if value.startswith("@"):
        if len(value) == 1:
            raise ValueError("username cannot be empty")
        return value
    return int(value)


def get_display_width(text: str) -> int:
    """Calculate terminal display width."""
    width = 0
    for char in text:
        if ord(char) > 127:  # Non-ASCII characters
            width += 2
        else:
            width += 1
    return width


def pad_text_to_width(text: str, target_width: int, align: str = "left") -> str:
    """Pad text to a target display width."""
    current_width = get_display_width(text)
    padding_needed = target_width - current_width

    if padding_needed <= 0:
        return text

    if align == "left":
        return text + " " * padding_needed
    elif align == "right":
        return " " * padding_needed + text
    else:  # center
        left_padding = padding_needed // 2
        right_padding = padding_needed - left_padding
        return " " * left_padding + text + " " * right_padding


class BaseJSONConfig(BaseModel):
    version: ClassVar[Union[str, int]] = 0
    olds: ClassVar[Optional[List[Type["BaseJSONConfig"]]]] = None
    is_current: ClassVar[bool] = False

    @classmethod
    def valid(cls, d):
        try:
            instance = cls.model_validate(d)
        except (ValidationError, TypeError):
            return None
        return instance

    def to_jsonable(self):
        return self.model_dump(mode="json")

    @classmethod
    def to_current(cls, obj: Self):
        return obj

    @classmethod
    def load(cls, d: dict) -> Optional[Tuple[Self, bool]]:
        if instance := cls.valid(d):
            return instance, False
        for old in cls.olds or []:
            if old_inst := old.valid(d):
                return old.to_current(old_inst), True
        return None


class SignConfigV1(BaseJSONConfig):
    version = 1

    chat_id: int
    sign_text: str
    sign_at: time
    random_seconds: int

    @classmethod
    def to_current(cls, obj: "SignConfigV1"):
        return SignConfigV2(
            chats=[
                SignChatV2(
                    chat_id=obj.chat_id,
                    sign_text=obj.sign_text,
                    delete_after=None,
                )
            ],
            sign_at=str(obj.sign_at),
            random_seconds=obj.random_seconds,
        )


class SignChatV2(BaseJSONConfig):
    version: ClassVar = 2
    chat_id: int
    delete_after: Optional[int] = None
    sign_text: Union[str, Literal["🎲", "🎯", "🏀", "⚽", "🎳", "🎰"]]
    as_dice: bool = False  # Send as a Telegram dice emoji
    text_of_btn_to_click: Optional[str] = None  # Button text to click
    choose_option_by_image: bool = False  # Choose an option from an image
    has_calculation_problem: bool = False  # Whether a calculation prompt is expected

    @property
    def need_response(self):
        return (
            bool(self.text_of_btn_to_click)
            or self.choose_option_by_image
            or self.has_calculation_problem
        )


class SignConfigV2(BaseJSONConfig):
    version: ClassVar = 2
    olds: ClassVar = [SignConfigV1]
    is_current: ClassVar = False

    chats: List[SignChatV2]
    sign_at: str  # Check-in time as time or cron expression
    random_seconds: int = 0
    sign_interval: int = 1  # Interval between chats in seconds

    @classmethod
    def to_current(cls, obj: Union["SignConfigV2", "SignConfigV1"]):
        if isinstance(obj, SignConfigV1):
            obj = SignConfigV1.to_current(obj)
        v3_chats = []
        for chat in obj.chats:
            actions = []
            if chat.sign_text:
                if chat.as_dice:
                    actions.append(SendDiceAction(dice=chat.sign_text))
                else:
                    actions.append(SendTextAction(text=chat.sign_text))
            if chat.text_of_btn_to_click:
                actions.append(
                    ClickKeyboardByTextAction(text=chat.text_of_btn_to_click)
                )
            if chat.choose_option_by_image:
                actions.append(ChooseOptionByImageAction())
            if chat.has_calculation_problem:
                actions.append(ReplyByCalculationProblemAction())
            v3_chats.append(
                SignChatV3(
                    chat_id=chat.chat_id,
                    delete_after=chat.delete_after,
                    actions=actions,
                )
            )
        return SignConfigV3(
            sign_at=obj.sign_at,
            random_seconds=obj.random_seconds,
            sign_interval=obj.sign_interval,
            chats=v3_chats,
        )


class SupportAction(int, Enum):
    SEND_TEXT = 1  # Send text
    SEND_DICE = 2  # Send dice emoji
    CLICK_KEYBOARD_BY_TEXT = 3  # Click keyboard by text
    CHOOSE_OPTION_BY_IMAGE = 4  # Choose option by image
    REPLY_BY_CALCULATION_PROBLEM = 5  # Reply to calculation prompt
    SOLVE_SLOT_MACHINE_CAPTCHA = 6  # Click slot-machine captcha buttons

    @property
    def desc(self):
        return {
            SupportAction.SEND_TEXT: "Send text",
            SupportAction.SEND_DICE: "Send dice emoji",
            SupportAction.CLICK_KEYBOARD_BY_TEXT: "Click keyboard by text",
            SupportAction.CHOOSE_OPTION_BY_IMAGE: "Choose option by image",
            SupportAction.REPLY_BY_CALCULATION_PROBLEM: "Reply to calculation prompt",
            SupportAction.SOLVE_SLOT_MACHINE_CAPTCHA: "Click slot-machine captcha buttons",
        }[self]


class SignAction(BaseModel):
    action: SupportAction


class SendTextAction(SignAction):
    action: Literal[SupportAction.SEND_TEXT] = SupportAction.SEND_TEXT
    text: str


class SendDiceAction(SignAction):
    action: Literal[SupportAction.SEND_DICE] = SupportAction.SEND_DICE
    dice: Union[Literal["🎲", "🎯", "🏀", "⚽", "🎳", "🎰"], str]


class ClickKeyboardByTextAction(SignAction):
    action: Literal[SupportAction.CLICK_KEYBOARD_BY_TEXT] = (
        SupportAction.CLICK_KEYBOARD_BY_TEXT
    )
    text: str


class ChooseOptionByImageAction(SignAction):
    action: Literal[SupportAction.CHOOSE_OPTION_BY_IMAGE] = (
        SupportAction.CHOOSE_OPTION_BY_IMAGE
    )


class ReplyByCalculationProblemAction(SignAction):
    action: Literal[SupportAction.REPLY_BY_CALCULATION_PROBLEM] = (
        SupportAction.REPLY_BY_CALCULATION_PROBLEM
    )


class SolveSlotMachineCaptchaAction(SignAction):
    action: Literal[SupportAction.SOLVE_SLOT_MACHINE_CAPTCHA] = (
        SupportAction.SOLVE_SLOT_MACHINE_CAPTCHA
    )
    if_text: Optional[str] = None
    if_regex: Optional[str] = None
    if_dice_emoji: Optional[str] = None

    @property
    def has_condition(self) -> bool:
        return bool(self.if_text or self.if_regex or self.if_dice_emoji)


ActionT: TypeAlias = Union[
    SendTextAction,
    SendDiceAction,
    ClickKeyboardByTextAction,
    ChooseOptionByImageAction,
    ReplyByCalculationProblemAction,
    SolveSlotMachineCaptchaAction,
]


class SignChatV3(BaseJSONConfig):
    version: ClassVar = 3
    chat_id: ChatId
    message_thread_id: Optional[int] = None
    name: Optional[str] = None
    delete_after: Optional[int] = None
    actions: List[ActionT]
    action_interval: float = 1  # Interval between actions in seconds

    @field_validator("chat_id", mode="before")
    @classmethod
    def _parse_chat_id(cls, value):
        return parse_chat_id_or_username(value)

    def __repr__(self) -> str:
        return (
            f"SignChatV3(chat_id={self.chat_id}, "
            f"message_thread_id={self.message_thread_id}, "
            f"delete_after={self.delete_after}, "
            f"actions=[{len(self.actions)} actions]),"
            f"action_interval={self.action_interval}"
        )

    def __str__(self) -> str:
        # Set content width
        content_width = 48

        # Build borders
        top_border = "╔" + "═" * content_width + "╗"
        bottom_border = "╚" + "═" * content_width + "╝"
        separator = "╟" + "─" * content_width + "╢"

        # Build title
        chat_id_text = f"Chat ID: {self.chat_id}"
        title = f"║ {pad_text_to_width(chat_id_text, content_width - 2)} ║"

        # Build name
        name_text = f"Name: {self.name or '-'}"
        name_info = f"║ {pad_text_to_width(name_text, content_width - 2)} ║"

        # Build message_thread_id
        thread_id_text = f"Message Thread ID: {self.message_thread_id or '-'}"
        thread_id_info = f"║ {pad_text_to_width(thread_id_text, content_width - 2)} ║"

        # Build deletion info
        delete_text = f"Delete After: {self.delete_after or '-'}"
        delete_info = f"║ {pad_text_to_width(delete_text, content_width - 2)} ║"

        # Build action lines
        actions_header_text = "Actions Flow:"
        actions_header = (
            f"║ {pad_text_to_width(actions_header_text, content_width - 2)} ║"
        )
        actions_lines = []

        for i, action in enumerate(self.actions, 1):
            action_type = action.action.desc
            details = ""

            if isinstance(action, SendTextAction):
                text_preview = (
                    action.text[:15] + "..." if len(action.text) > 15 else action.text
                )
                details = f"Text: {text_preview}"
            elif isinstance(action, SendDiceAction):
                details = f"Dice: {action.dice}"
            elif isinstance(action, ClickKeyboardByTextAction):
                text_preview = (
                    action.text[:15] + "..." if len(action.text) > 15 else action.text
                )
                details = f"Click: {text_preview}"

            if details:
                action_text = f"{i}. [{action_type}] {details}"
            else:
                action_text = f"{i}. [{action_type}]"

            action_line = f"║ {pad_text_to_width(action_text, content_width - 2)} ║"
            actions_lines.append(action_line)

        # Join all parts
        result = [
            top_border,
            title,
            name_info,
            thread_id_info,
            delete_info,
            separator,
            actions_header,
            *actions_lines,
            bottom_border,
        ]

        return "\n".join(result)

    @property
    def requires_ai(self) -> bool:
        ai_actions = {
            SupportAction.CHOOSE_OPTION_BY_IMAGE,
            SupportAction.REPLY_BY_CALCULATION_PROBLEM,
        }
        return any(action.action in ai_actions for action in self.actions)


class SignConfigV3(BaseJSONConfig):
    version: ClassVar = 3
    olds: ClassVar = [SignConfigV2]
    is_current: ClassVar = True

    _version: Literal[3] = 3
    chats: List[SignChatV3]
    sign_at: str  # Check-in time as time or cron expression
    random_seconds: int = 0
    sign_interval: int = 1  # Interval between chats in seconds

    @property
    def requires_ai(self) -> bool:
        return any(chat.requires_ai for chat in self.chats)




