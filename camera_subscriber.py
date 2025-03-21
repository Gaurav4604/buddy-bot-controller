import asyncio
import cv2
import numpy as np
import base64
from buddy_bot_communication.client import Node
import json


class CameraSubscriber:
    def __init__(self, server_url):
        self.node = Node(server_url)
        self.left_image = None
        self.right_image = None
        self.combined_image = None
        self.display_window_name = "T265 Fisheye Streams (Press q to exit)"
        self.running = False

    async def connect(self):
        await self.node.connect(
            ["/control", "/vision-channel-1", "/vision-channel-2", "/data"]
        )

        # Subscribe to both vision channels
        await self.node.subscribe("/vision-channel-1", self.handle_left_image)
        await self.node.subscribe("/vision-channel-2", self.handle_right_image)

    async def disconnect(self):
        await self.node.disconnect()

    async def handle_left_image(self, data):
        try:
            data = json.loads(data)
            # Decode the base64 image
            img_data = base64.b64decode(data["image"])
            # Convert to numpy array
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            # Decode the JPEG image
            self.left_image = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)

            # Update the combined image if both images are available
            if self.left_image is not None and self.right_image is not None:
                self.combined_image = np.hstack((self.left_image, self.right_image))
        except Exception as e:
            print(f"Error processing left image: {e}")

    async def handle_right_image(self, data):
        try:
            data = json.loads(data)
            # Decode the base64 image
            img_data = base64.b64decode(data["image"])
            # Convert to numpy array
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            # Decode the JPEG image
            self.right_image = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)

            # Update the combined image if both images are available
            if self.left_image is not None and self.right_image is not None:
                self.combined_image = np.hstack((self.left_image, self.right_image))
        except Exception as e:
            print(f"Error processing right image: {e}")

    async def display_frames(self):
        self.running = True

        while self.running:
            if self.combined_image is not None:
                cv2.imshow(self.display_window_name, self.combined_image)

                # Process key presses (q to quit)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.running = False
                    break

            await asyncio.sleep(0.01)  # Small delay to prevent CPU hogging

    def stop(self):
        self.running = False
        cv2.destroyAllWindows()


async def main():
    server_url = "http://172.22.7.122:7000"  # Replace with your server address
    camera_subscriber = CameraSubscriber(server_url)

    await camera_subscriber.connect()

    try:
        print("Camera subscriber started. Press 'q' in the display window to exit.")
        await camera_subscriber.display_frames()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        camera_subscriber.stop()
        await camera_subscriber.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
