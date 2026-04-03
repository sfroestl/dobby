"""
Natural language home automation agent using Claude + tool use.
Talks to the dobby FastAPI server running on localhost.
"""
import os
import logging
import httpx
from dotenv import load_dotenv
import anthropic
from anthropic import beta_tool

# Load variables from .env
load_dotenv()

_logger = logging.getLogger(__name__)

BASE_URL = os.getenv("DOBBY_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

_headers = {"X-API-Key": API_KEY} if API_KEY else {}


@beta_tool
def list_devices() -> str:
    """List all smart home devices and their current status."""
    # r = httpx.get(f"{BASE_URL}/devices", headers=_headers, timeout=10)
    # r.raise_for_status()
    # return r.text


@beta_tool
def turn_on(device_name: str) -> str:
    """Turn on a smart plug or light by name.

    Args:
        device_name: The name of the device, e.g. 'kitchen' or 'living room'.
    """
    # r = httpx.post(f"{BASE_URL}/plugs/{device_name}/on", headers=_headers, timeout=10)
    # r.raise_for_status()
    # return r.text


@beta_tool
def turn_off(device_name: str) -> str:
    """Turn off a smart plug or light by name.

    Args:
        device_name: The name of the device, e.g. 'kitchen' or 'living room'.
    """
    # r = httpx.post(f"{BASE_URL}/plugs/{device_name}/off", headers=_headers, timeout=10)
    # r.raise_for_status()
    # return r.text


@beta_tool
def get_device_status(device_name: str) -> str:
    """Get the current status of a specific device.

    Args:
        device_name: The name of the device, e.g. 'kitchen' or 'living room'.
    """
    # r = httpx.get(f"{BASE_URL}/plugs/{device_name}/status", headers=_headers, timeout=10)
    # r.raise_for_status()
    # return r.text


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

TOOLS = [list_devices, turn_on, turn_off, get_device_status]

SYSTEM = """You are a smart home assistant controlling devices via the Dobby home automation system.
You have access to tools to list, turn on/off, and check the status of smart plugs and lights.
Be concise. When the user asks you to do something, just do it and confirm."""


def run(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]
    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM,
        tools=TOOLS,
        messages=messages,
    )
    last = None
    for msg in runner:
        last = msg
    if last is None:
        return ""
    return next((b.text for b in last.content if b.type == "text"), "")


def main():
    print("Dobby Agent — type 'exit' to quit\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() == "exit":
            break
        response = run(user_input)
        print(f"Agent: {response}\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(name)s: %(message)s",
    )
    main()
