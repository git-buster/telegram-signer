from datetime import time

import pytest
from pydantic import ValidationError

from telegram_signer.config import (
    ChooseOptionByImageAction,
    ClickKeyboardByTextAction,
    ReplyByCalculationProblemAction,
    SendDiceAction,
    SendTextAction,
    SignChatV2,
    SignChatV3,
    SignConfigV1,
    SignConfigV2,
    SignConfigV3,
)


class TestSignConfigV2ToCurrent:
    """Test SignConfigV2.to_current."""

    def test_convert_basic_chat(self):
        """Test basic chat config conversion."""
        v2_config = SignConfigV2(
            chats=[
                SignChatV2(
                    chat_id=123,
                    sign_text="Hello",
                    delete_after=10,
                )
            ],
            sign_at="08:00",
            random_seconds=300,
        )

        v3_config = SignConfigV2.to_current(v2_config)

        assert isinstance(v3_config, SignConfigV3)
        assert v3_config.sign_at == "08:00"
        assert v3_config.random_seconds == 300
        assert len(v3_config.chats) == 1

        chat = v3_config.chats[0]
        assert chat.chat_id == 123
        assert chat.message_thread_id is None
        assert chat.delete_after == 10
        assert len(chat.actions) == 1
        assert isinstance(chat.actions[0], SendTextAction)
        assert chat.actions[0].text == "Hello"

    def test_convert_dice_chat(self):
        """Test dice emoji conversion."""
        v2_config = SignConfigV2(
            chats=[
                SignChatV2(
                    chat_id=123,
                    sign_text="🎲",
                    as_dice=True,
                )
            ],
            sign_at="08:00",
        )

        v3_config = SignConfigV2.to_current(v2_config)
        action = v3_config.chats[0].actions[0]

        assert isinstance(action, SendDiceAction)
        assert action.dice == "🎲"

    def test_convert_complex_chat(self):
        """Test config conversion with multiple actions."""
        v2_config = SignConfigV2(
            chats=[
                SignChatV2(
                    chat_id=123,
                    sign_text="check-in",
                    text_of_btn_to_click="click",
                    choose_option_by_image=True,
                    has_calculation_problem=True,
                )
            ],
            sign_at="08:00",
        )

        v3_config = SignConfigV2.to_current(v2_config)
        actions = v3_config.chats[0].actions

        assert len(actions) == 4
        assert isinstance(actions[0], SendTextAction)
        assert actions[0].text == "check-in"
        assert isinstance(actions[1], ClickKeyboardByTextAction)
        assert actions[1].text == "click"
        assert isinstance(actions[2], ChooseOptionByImageAction)
        assert isinstance(actions[3], ReplyByCalculationProblemAction)

    def test_convert_multiple_chats(self):
        """Test multiple chat config conversion."""
        v2_config = SignConfigV2(
            chats=[
                SignChatV2(chat_id=1, sign_text="Chat1"),
                SignChatV2(chat_id=2, sign_text="Chat2"),
            ],
            sign_at="08:00",
        )

        v3_config = SignConfigV2.to_current(v2_config)

        assert len(v3_config.chats) == 2
        assert v3_config.chats[0].chat_id == 1
        assert v3_config.chats[0].actions[0].text == "Chat1"
        assert v3_config.chats[1].chat_id == 2
        assert v3_config.chats[1].actions[0].text == "Chat2"

    def test_convert_empty_actions(self):
        """Test empty action list conversion."""
        v2_config = SignConfigV2(
            chats=[SignChatV2(chat_id=123, sign_text="")],
            sign_at="08:00",
        )

        v3_config = SignConfigV2.to_current(v2_config)

        assert len(v3_config.chats[0].actions) == 0

    def test_convert_from_v1(self):
        """Test V1 to V3 config upgrade."""
        v1_config = SignConfigV1(
            chat_id=123,
            sign_text="Old config",
            sign_at=time(8, 0),
            random_seconds=300,
        )

        # Trigger conversion through V2 load.
        v3_config = SignConfigV2.to_current(v1_config)

        assert isinstance(v3_config, SignConfigV3)
        assert v3_config.sign_at == "08:00:00"  # time object is converted to string
        assert v3_config.random_seconds == 300
        assert len(v3_config.chats) == 1
        assert v3_config.chats[0].chat_id == 123
        assert v3_config.chats[0].message_thread_id is None
        assert v3_config.chats[0].actions[0].text == "Old config"

    def test_sign_chat_v3_with_message_thread_id(self):
        chat = SignChatV3(
            chat_id=-1001234567890,
            message_thread_id=1,
            actions=[SendTextAction(text="checkin")],
        )
        assert chat.message_thread_id == 1

    def test_sign_chat_v3_supports_username_chat_id(self):
        chat = SignChatV3(
            chat_id="@neo",
            actions=[SendTextAction(text="checkin")],
        )

        assert chat.chat_id == "@neo"

    def test_sign_chat_v3_coerces_numeric_string_chat_id_to_int(self):
        chat = SignChatV3(
            chat_id="-1001234567890",
            actions=[SendTextAction(text="checkin")],
        )

        assert chat.chat_id == -1001234567890
        assert isinstance(chat.chat_id, int)

    def test_sign_chat_v3_rejects_username_without_at_prefix(self):
        with pytest.raises(ValidationError):
            SignChatV3(
                chat_id="neo",
                actions=[SendTextAction(text="checkin")],
            )



