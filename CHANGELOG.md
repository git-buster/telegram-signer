# Changelog

## 1.0.7 - 2026-05-07

- Add attribution to `https://github.com/amchii/tg-signer` in the public README.
- Rewrite README in Traditional Chinese, Simplified Chinese, and English, with Traditional Chinese first.
- Document simplified release contents, added GitHub Actions friendly features, slot-machine captcha handling, and privacy separation.

## 1.0.6 - 2026-05-02

- Keep public README content English-only.
- Replace mojibake slot-machine emoji examples with the real `🎰` character.

## 1.0.5 - 2026-05-02

- Treat the `➖` slot-machine captcha button as BAR.
- Exclude the `🔙` button from BAR fallback matching.

## 1.0.4 - 2026-05-02

- Exclude arrow-style `BACK` buttons from the BAR fallback used for
  slot-machine captchas.
- Show slot-machine captcha value, decoded symbols, button labels, normalized
  labels, and callback data in logs.

## 1.0.3 - 2026-05-01

- Improve BAR matching for slot-machine captchas when Telegram renders the BAR
  button as dark block characters instead of the literal `BAR` text.
- Add diagnostic logging for received slot-machine captcha button labels.

## 1.0.2 - 2026-05-01

- Clarify and test the slot-machine captcha button layout as `BAR`, grape,
  lemon, `7`, and `back`.
- Keep support for the two-message slot-machine flow where the dice result and
  the answer buttons arrive in separate Telegram messages.
- Update the local GitHub Actions template to install `telegram-signer==1.0.2`.

## 1.0.1 - 2026-05-01

- Add slot-machine captcha solving for Telegram dice messages.
- Support storing a slot-machine result from one message and answering when the
  inline buttons arrive in a later message.
