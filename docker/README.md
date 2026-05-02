# Docker

The Docker image contains the CLI-only Telegram Signer package.

Build locally:

```sh
docker build -t telegram-signer:latest -f docker/Dockerfile .
```

Run a check-in task:

```sh
docker run --rm -it \
  --name telegram-signer \
  --volume "$PWD:/opt/telegram-signer" \
  telegram-signer:latest \
  telegram-signer account_a run task_name
```
