from facp_connection import FACPConnection, CommunicationError
import serial


def main():
    facp = FACPConnection('COM1')

    try:
        # Test connection
        print("Testing connection...")
        facp.send_command("TERMINAL")
        response = facp.read_response()
        print(f"Terminal response: {response}")

        # Get current time
        print("Getting current time...")
        facp.send_command("CTIME")
        response = facp.read_response()
        print(f"Current time: {response}")

        # Get system revision
        print("Getting system revision...")
        facp.send_command("REV")
        response = facp.read_response()
        print(f"System revision: {response}")

    except CommunicationError as e:
        print(f"Communication error: {e}")
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    finally:
        facp.close()


if __name__ == "__main__":
    main()