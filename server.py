import socket
import struct
import cv2
import numpy as np
import threading
import sys

class RemoteServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = None
        self.screen_window = None
        # self.setup_mouse_click_handler()

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print("Server listening on", self.host, ":", self.port)

        while True:
            self.client_socket, _ = self.server_socket.accept()
            print("Client connected from", self.client_socket.getpeername())
            threading.Thread(target=self.handle_client).start()

    def send_message(self, msg_type, data):
        # Pack message type and size into header
        msg_size = len(data)
        header = struct.pack("!II", msg_type, msg_size)
        # Send header
        self.client_socket.sendall(header)
        # Send data
        self.client_socket.sendall(data)

    def handle_client(self):
        try:
            while True:
                # Receive message header
                header_data = self.client_socket.recv(8)
                if not header_data:
                    break
                msg_type, msg_size = struct.unpack("!II", header_data)
                # Handle message based on type
                if msg_type == 1:  # Screenshot message
                    screenshot_data = self.recvall(msg_size)
                    self.show_screenshot(screenshot_data)
                elif msg_type == 2:  # Mouse click message
                    click_data = self.recvall(msg_size)
                    self.handle_mouse_click(click_data)
        finally:
            print("Client disconnected")
            self.client_socket.close()

    def recvall(self, size):
        data = b""
        while len(data) < size:
            packet = self.client_socket.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def show_screenshot(self, screenshot_data):
        #print(f"Received screenshot data size: {len(screenshot_data)} bytes")  # Debugging line
        # Decode screenshot data and display in a window
        screenshot_np = cv2.imdecode(np.frombuffer(screenshot_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if screenshot_np is not None:
            #print(f"Decoded image dimensions: {screenshot_np.shape}")  # Debugging line
            if screenshot_np.shape[0] > 0 and screenshot_np.shape[1] > 0:
                if self.screen_window is None:
                    cv2.namedWindow('Remote Screen', cv2.WINDOW_NORMAL)
                    self.screen_window = 'Remote Screen'
                    cv2.setMouseCallback('Remote Screen', self.handle_mouse_click_event)
                cv2.imshow(self.screen_window, screenshot_np)
                cv2.waitKey(1)
            else:
                print("Invalid image dimensions or empty image")
        else:
            print("Failed to decode image data")

    def handle_mouse_click_event(self, event, x, y, flags, param):
        click_type = None
        if event == cv2.EVENT_LBUTTONDOWN:
            print("Left mouse click at:", x, y)
            click_type = 2  # Message type 2 for left click
        elif event == cv2.EVENT_RBUTTONDOWN:
            print("Right mouse click at:", x, y)
            click_type = 3  # Message type 3 for right click (or define as per your protocol)

        if click_type is not None:
            try:
                # Pack message type and mouse click coordinates
                click_data = struct.pack("!II", x, y)  # Pack x, y into binary data
                msg_size = len(click_data)
                header = struct.pack("!II", click_type, msg_size)
                
                # Send header and click data
                self.client_socket.sendall(header + click_data)
            except Exception as e:
                print("Error sending mouse click data to client:", e)




# Main
if __name__ == "__main__":
    server = RemoteServer('localhost', 5000)
    server.start()
