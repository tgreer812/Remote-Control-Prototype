import socket
import pyautogui
import struct
import cv2
import numpy as np
import select

class RemoteClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setblocking(False)  # Set socket to non-blocking mode



    def connect(self):
        # Set socket to non-blocking mode
        self.client_socket.setblocking(False)

        while True:
            try:
                self.client_socket.connect((self.host, self.port))
                print("Connected to server")
                break
            except BlockingIOError:
                # Use select to wait for connection to complete
                _, write_ready, _ = select.select([], [self.client_socket], [])
                if self.client_socket in write_ready:
                    break
                continue


    def send_message(self, msg_type, data):
        # Pack message type and size into header
        msg_size = len(data)
        header = struct.pack("!II", msg_type, msg_size)
        
        try:
            # Send header
            self.client_socket.sendall(header)
            # Send data
            self.client_socket.sendall(data)
        except BlockingIOError:
            pass  # Data could not be sent immediately, continue with other operations


    def capture_screen(self):
        # Capture screen using pyautogui
        screenshot = pyautogui.screenshot()
        # Convert PIL image to numpy array
        screenshot_np = np.array(screenshot)
        # Encode numpy array to bytes using OpenCV
        _, screenshot_bytes = cv2.imencode('.png', screenshot_np)
        return screenshot_bytes

    def receive_data(self, size):
        data = b""
        try:
            while len(data) < size:
                packet = self.client_socket.recv(size - len(data))
                if not packet:
                    return None
                data += packet
        except BlockingIOError:
            pass
        return data

    def handle_mouse_click(self):
        # Receive mouse click coordinates from server
        try:
            header_data = self.client_socket.recv(8)
            if header_data:
                _, msg_size = struct.unpack("!II", header_data)
                click_data = self.receive_data(msg_size)
                if click_data:
                    # Extract mouse click coordinates
                    x, y = struct.unpack("!II", click_data)
                    # Perform mouse click action
                    pyautogui.click(x, y)
        except BlockingIOError:
            pass

    def run(self):
        self.connect()
        while True:
            # Capture screen and send to server
            screen_data = self.capture_screen()
            self.send_message(1, screen_data)  # 1 for screenshot message
            # Handle mouse click instructions from server
            self.handle_mouse_click()

# Main
if __name__ == "__main__":
    client = RemoteClient('localhost', 5000)
    client.run()
