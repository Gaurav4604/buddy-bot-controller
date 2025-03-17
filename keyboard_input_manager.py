import threading
import time
from pynput import keyboard
from buddy_bot_communication.client import Node
import asyncio


class KeyboardEventManager:
    """
    A class to handle keyboard events in a non-blocking way using a separate thread.
    Similar to input handling in game engines.
    """

    def __init__(self, loop=None):
        self.pressed_keys = set()
        self.key_callbacks = {
            "key_down": {},
            "key_up": {},
            "key_pressed": {},  # For continuous detection while key is held
        }
        self.running = False
        self.listener = None
        self.thread = None
        self.poll_interval = 0.01  # 10ms interval for checking pressed keys
        self.loop = loop  # Reference to the main asyncio event loop

    def on_press(self, key):
        """Callback function that's called when a key is pressed"""
        try:
            key_char = key.char
        except (AttributeError, TypeError):
            key_char = str(key)

        if key_char not in self.pressed_keys:
            self.pressed_keys.add(key_char)
            if key_char in self.key_callbacks["key_down"]:
                for callback in self.key_callbacks["key_down"][key_char]:
                    # Schedule the async callback on the main event loop
                    asyncio.run_coroutine_threadsafe(callback(), self.loop)

    def on_release(self, key):
        """Callback function that's called when a key is released"""
        try:
            key_char = key.char
        except (AttributeError, TypeError):
            key_char = str(key)

        if key_char in self.pressed_keys:
            self.pressed_keys.remove(key_char)
            if key_char in self.key_callbacks["key_up"]:
                for callback in self.key_callbacks["key_up"][key_char]:
                    asyncio.run_coroutine_threadsafe(callback(), self.loop)

    async def register_callback(self, event_type, key, callback):
        """
        Register a callback function for a specific key event

        Args:
            event_type: 'key_down', 'key_up', or 'key_pressed'
            key: The key to listen for
            callback: The async function to call when the event occurs
        """
        if event_type not in self.key_callbacks:
            raise ValueError(f"Unknown event type: {event_type}")
        if key not in self.key_callbacks[event_type]:
            self.key_callbacks[event_type][key] = []
        # Append the callback without awaiting it since append() is synchronous.
        self.key_callbacks[event_type][key].append(callback)

    def check_pressed_keys(self):
        """Continuously checks for pressed keys and triggers 'key_pressed' callbacks."""
        while self.running:
            for key in self.pressed_keys:
                if key in self.key_callbacks["key_pressed"]:
                    for callback in self.key_callbacks["key_pressed"][key]:
                        asyncio.run_coroutine_threadsafe(callback(), self.loop)
            time.sleep(self.poll_interval)

    def start(self):
        """Start the keyboard listener and the thread for continuous key press detection."""
        if self.running:
            return

        self.running = True

        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.listener.start()

        self.thread = threading.Thread(target=self.check_pressed_keys)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the keyboard listener and thread."""
        self.running = False
        if self.listener:
            self.listener.stop()
        if self.thread:
            self.thread.join(timeout=1.0)


# Example usage
async def main():
    loop = asyncio.get_running_loop()
    keyboard_manager = KeyboardEventManager(loop=loop)
    node = Node("http://172.22.7.122:7000")
    await node.connect()

    async def on_a_press():
        print("'a' key pressed!")
        await node.publish("/control", {"command": "a", "status": "down"})

    async def on_a_release():
        print("'a' key released!")
        await node.publish("/control", {"command": "a", "status": "release"})

    async def on_w_press():
        print("'w' key pressed!")
        await node.publish("/control", {"command": "w", "status": "down"})

    async def on_w_release():
        print("'w' key released!")
        await node.publish("/control", {"command": "w", "status": "release"})

    async def on_s_press():
        print("'s' key pressed!")
        await node.publish("/control", {"command": "s", "status": "down"})

    async def on_s_release():
        print("'s' key released!")
        await node.publish("/control", {"command": "s", "status": "release"})

    async def on_d_press():
        print("'d' key pressed!")
        await node.publish("/control", {"command": "d", "status": "down"})

    async def on_d_release():
        print("'d' key released!")
        await node.publish("/control", {"command": "d", "status": "release"})

    await keyboard_manager.register_callback("key_down", "a", on_a_press)
    await keyboard_manager.register_callback("key_up", "a", on_a_release)
    await keyboard_manager.register_callback("key_down", "w", on_w_press)
    await keyboard_manager.register_callback("key_up", "w", on_w_release)
    await keyboard_manager.register_callback("key_down", "s", on_s_press)
    await keyboard_manager.register_callback("key_up", "s", on_s_release)
    await keyboard_manager.register_callback("key_down", "d", on_d_press)
    await keyboard_manager.register_callback("key_up", "d", on_d_release)

    keyboard_manager.start()

    try:
        print("Keyboard event handler running. Press keys to see events.")
        print("Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        keyboard_manager.stop()
        await node.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
