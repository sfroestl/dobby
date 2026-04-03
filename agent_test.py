"""
Natural language home automation agent using Claude + tool use.
Connects directly to the Philips Hue bridge.
"""
import json
import os
import logging
from dotenv import load_dotenv
import anthropic
from anthropic import beta_tool
from phue import Bridge

# Load variables from .env
load_dotenv()

_logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
HUE_BRIDGE_IP = os.getenv("HUE_BRIDGE_IP")

bridge = Bridge(HUE_BRIDGE_IP)


@beta_tool
def list_devices() -> str:
    """List all Hue lights and groups with their name, on/off state, and brightness."""
    _logger.info("list_devices()")
    lights = bridge.get_light()
    groups = bridge.get_group()
    lights_list = []
    for light_id in sorted(lights.keys(), key=lambda x: int(x)):
        light = lights[light_id]
        state = light["state"]
        lights_list.append({
            "id": light_id,
            "name": light["name"],
            "on": state["on"],
            "brightness": state.get("bri"),
            "reachable": state.get("reachable"),
        })
    groups_list = []
    for group_id in sorted(groups.keys(), key=lambda x: int(x)):
        group = groups[group_id]
        action = group.get("action", {})
        groups_list.append({
            "id": group_id,
            "name": group["name"],
            "on": action.get("on"),
            "brightness": action.get("bri"),
            "lights": group.get("lights", []),
        })
    return json.dumps({"lights": lights_list, "groups": groups_list})


@beta_tool
def turn_on(light_name: str, brightness: int = 254) -> str:
    """Turn on a Hue light by name, with optional brightness.

    Args:
        light_name: The name of the light as shown in the Hue app.
        brightness: Brightness level from 1 (min) to 254 (max). Defaults to 254.
    """
    _logger.info("turn_on(light_name=%r, brightness=%r)", light_name, brightness)
    bridge.set_light(light_name, {"on": True, "bri": max(1, min(254, brightness))})
    return json.dumps({"success": True, "light": light_name, "state": "on", "brightness": brightness})


@beta_tool
def set_brightness(light_name: str, brightness: int) -> str:
    """Set the brightness of a Hue light without changing its on/off state.

    Args:
        light_name: The name of the light as shown in the Hue app.
        brightness: Brightness level from 1 (min) to 254 (max).
    """
    _logger.info("set_brightness(light_name=%r, brightness=%r)", light_name, brightness)
    bridge.set_light(light_name, "bri", max(1, min(254, brightness)))
    return json.dumps({"success": True, "light": light_name, "brightness": brightness})


@beta_tool
def turn_off(light_name: str) -> str:
    """Turn off a Hue light by name.

    Args:
        light_name: The name of the light as shown in the Hue app.
    """
    _logger.info("turn_off(light_name=%r)", light_name)
    bridge.set_light(light_name, "on", False)
    return json.dumps({"success": True, "light": light_name, "state": "off"})


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

TOOLS = [list_devices, turn_on, set_brightness, turn_off, get_device_status]

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
        _logger.warning(f"response: {msg.content}")
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
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    main()
