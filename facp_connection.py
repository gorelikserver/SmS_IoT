import serial
import time


class FACPConnection:
    def __init__(self, port, baudrate=9600):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        self.sequence_number = 0x40  # Starting sequence number

    def _calculate_checksum(self, data):
        # Sum all characters modulo 4096 (12 bits)
        checksum = sum(data) % 4096

        # Take the 1's complement (invert)
        checksum = (~checksum) & 0xFFF

        # Split into two 6-bit values and add 0x40 to each
        msb = ((checksum >> 6) & 0x3F) + 0x40
        lsb = (checksum & 0x3F) + 0x40

        return bytes([msb, lsb])

    def _construct_message(self, message_body):
        self.sequence_number = (self.sequence_number - 0x40 + 1) % 64 + 0x40
        message = bytearray([0x1C, self.sequence_number])  # Start with BEGIN and sequence number
        message.extend(message_body.encode('ascii'))
        message.append(0x17)  # END character
        checksum = self._calculate_checksum(message[1:-1])  # Calculate checksum excluding BEGIN and END
        message.extend(checksum)
        return message

    def send_command(self, command):
        message = self._construct_message(command)
        self.ser.write(message)
        # Wait for ACK
        ack = self.ser.read(1)
        if ack != b'\x06':
            raise CommunicationError("Did not receive ACK")

    def read_response(self):
        response = bytearray()
        # Wait for BEGIN character
        while True:
            char = self.ser.read(1)
            if char == b'\x1C':  # BEGIN character
                response.extend(char)
                break
            elif not char:
                raise CommunicationError("Timeout waiting for BEGIN character")

        # Read until END character
        while True:
            char = self.ser.read(1)
            if not char:
                raise CommunicationError("Timeout waiting for END character")
            response.extend(char)
            if char == b'\x17':  # END character
                break

        # Read checksum (2 bytes)
        checksum = self.ser.read(2)
        if len(checksum) != 2:
            raise CommunicationError("Failed to read checksum")
        response.extend(checksum)

        # Validate checksum
        calculated_checksum = self._calculate_checksum(response[1:-3])  # Exclude BEGIN, END, and checksum itself
        if calculated_checksum != checksum:
            raise CommunicationError("Checksum mismatch")

        # Send ACK
        self.ser.write(b'\x06')

        # Process the message
        sequence_number = response[1]
        message_body = response[2:-3].decode('ascii')

        return message_body

    def close(self):
        self.ser.close()


class CommunicationError(Exception):
    pass