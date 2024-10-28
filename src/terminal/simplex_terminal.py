import serial
import time
from typing import List, Dict
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SimplexTerminal:
    def __init__(self, port: str, baudrate: int = 19200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self._connect()

    def _connect(self):
        """Establish serial connection."""
        try:
            logger.info(f"Connecting to {self.port} at {self.baudrate} baud...")
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            logger.info("Serial connection established")
        except Exception as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            raise

    def _read_response(self, timeout: int = 2) -> str:
        """Read response from panel until we get a complete response."""
        response = ""
        start_time = time.time()
        end_time = start_time + timeout

        print("\nPanel response: ", end='', flush=True)

        while time.time() < end_time:
            if self.serial.in_waiting:
                char = self.serial.read()
                try:
                    decoded_char = char.decode('latin1')
                    print(decoded_char, end='', flush=True)  # Immediately print the character
                    response += decoded_char

                    # Reset timeout if we're still receiving data
                    if self.serial.in_waiting:
                        end_time = time.time() + timeout

                    # If we see a complete response (ends with prompt), we can stop
                    if response.rstrip().endswith('-'):
                        if not self.serial.in_waiting:  # Make sure buffer is empty
                            time.sleep(0.1)  # Small delay to ensure we got everything
                            if not self.serial.in_waiting:
                                break

                except Exception as e:
                    logger.error(f"Error decoding character: {e}")

        print()  # New line after complete response
        total_time = time.time() - start_time
        logger.debug(f"Response received in {total_time:.2f} seconds")
        logger.debug(f"Complete response: {repr(response)}")
        return response

    def send_command(self, command: str) -> str:
        """Send a command and get complete response."""
        try:
            logger.info(f"Sending command: {command}")
            print(f"\nSending: {command}")

            # Clear any leftover data
            self.serial.reset_input_buffer()

            # Send the command
            self.serial.write(f"{command}\r".encode())

            # Get the complete response
            response = self._read_response(timeout=3)  # Longer timeout for CLIST
            return response

        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return ""

    def login(self, passcode: str) -> bool:
        """Login to the panel."""
        try:
            logger.info("Attempting login...")

            # Send LOGIN command and wait for prompt
            response = self.send_command("LOGIN")

            # Send passcode
            logger.debug("Sending passcode...")
            response = self.send_command(passcode)

            success = "ACCESS GRANTED" in response
            logger.info("Login successful" if success else "Login failed")
            return success

        except Exception as e:
            logger.error(f"Login failed with error: {e}")
            return False

    def get_clist(self) -> List[Dict[str, str]]:
        """Get point status list."""
        try:
            response = self.send_command("CLIST")
            points = self._parse_clist(response)
            logger.debug(f"Parsed {len(points)} points from CLIST")
            return points

        except Exception as e:
            logger.error(f"CLIST command failed: {e}")
            return []

    def _parse_clist(self, response: str) -> List[Dict[str, str]]:
        """Parse CLIST response."""
        points = []
        for line in response.split('\n'):
            line = line.strip()
            if not line or line == "-" or "CLIST" in line:
                continue
            try:
                parts = line.split()
                if len(parts) >= 2:
                    points.append({
                        'id': parts[0],
                        'status': parts[1]
                    })
            except Exception as e:
                logger.error(f"Error parsing line '{line}': {e}")
        return points

    def close(self):
        """Close the serial connection."""
        if self.serial and self.serial.is_open:
            logger.info("Closing serial connection")
            self.serial.close()