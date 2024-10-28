import serial
import time


class SimplexTerminal:
    def __init__(self, port: str, baudrate: int = 19200):
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    def read_response(self, timeout=2):
        response = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.serial.in_waiting:
                char = self.serial.read()
                decoded_char = char.decode('latin1')
                print(decoded_char, end='')
                response += decoded_char
        return response

    def login(self, passcode):
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        self.serial.write("LOGIN\r".encode())
        response = self.read_response()

        self.serial.write(f"{passcode}\r".encode())
        response = self.read_response()
        return "ACCESS GRANTED" in response

    def get_clist(self):
        """Get and parse CLIST results."""
        print("\nGetting point status list...")
        self.serial.write("CLIST\r".encode())
        response = self.read_response(timeout=3)  # Longer timeout for potentially long lists

        # Split response into lines and process each line
        points = []
        for line in response.split('\n'):
            # Skip empty lines and prompts
            line = line.strip()
            if not line or line == "-" or "CLIST" in line:
                continue

            # Try to parse the point information
            try:
                # Expecting format like: @5-1-0 F1* or ZN1 F1*
                parts = line.split()
                if len(parts) >= 2:
                    point_info = {
                        'id': parts[0],
                        'status': parts[1]
                    }
                    points.append(point_info)
            except Exception as e:
                print(f"Error parsing line: {line}")
                continue

        return points

    def close(self):
        if self.serial.is_open:
            self.serial.close()


# Example usage
if __name__ == "__main__":
    PORT = "COM9"  # Replace with your COM port

    terminal = SimplexTerminal(PORT)

    if terminal.login("333"):  # Replace with your actual passcode
        print("\nLogin successful!")

        # Get and display point status
        points = terminal.get_clist()

        if points:
            print("\nPoint Status Summary:")
            print("-" * 40)
            for point in points:
                print(f"Point ID: {point['id']}")
                print(f"Status: {point['status']}")
                print("-" * 40)
            print(f"Total points with abnormal status: {len(points)}")
        else:
            print("\nNo abnormal points found in system")
    else:
        print("\nLogin failed!")

    terminal.close()