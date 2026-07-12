import requests

API_URL = "http://127.0.0.1:8000/chat"


def ask(message: str) -> str:
    response = requests.post(
        API_URL,
        json={"message": message},
        timeout=60,
    )

    response.raise_for_status()

    return response.json()["response"]
