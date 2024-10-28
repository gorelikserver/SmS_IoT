import sys
from src.terminal import SimplexTerminal
from src.monitor import StatusMonitor
from src.utils.config import load_config
from src.utils.logging import setup_logging, get_logger

def main():
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")

        # Initialize terminal
        terminal = SimplexTerminal(
            port=config['serial']['port'],
            baudrate=config['serial']['baudrate']
        )

        # Initialize monitor
        monitor = StatusMonitor(
            terminal=terminal,
            poll_interval=config['monitor']['poll_interval']
        )

        # Start monitoring
        monitor.start_monitoring(config['panel']['passcode'])

    except KeyboardInterrupt:
        logger.info("Stopping monitor due to user interrupt...")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if 'terminal' in locals():
            terminal.close()

if __name__ == "__main__":
    main()