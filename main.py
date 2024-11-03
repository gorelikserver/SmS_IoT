import os
from datetime import datetime
from src.terminal import SimplexTerminal
from src.monitor import StatusMonitor
from src.points import PointsManager
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

        # Ensure points directories exist
        points_dir = os.path.dirname(config['points']['file'])
        export_dir = config['points']['export_dir']
        os.makedirs(points_dir, exist_ok=True)
        os.makedirs(export_dir, exist_ok=True)

        # Initialize points manager and load points file
        points_manager = PointsManager()
        try:
            points_manager.load_points_file(
                file_path=config['points']['file'],
                encoding=config['points']['encoding']
            )
            logger.info(f"Successfully loaded points file: {config['points']['file']}")
        except Exception as e:
            logger.error(f"Failed to load points file: {e}")
            raise

        # Initialize terminal
        terminal = SimplexTerminal(
            port=config['serial']['port'],
            baudrate=config['serial']['baudrate']
        )

        # Initialize monitor with points manager
        monitor = StatusMonitor(
            terminal=terminal,
            points_manager=points_manager,
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
        # Export final point status
        if 'points_manager' in locals():
            try:
                export_file = os.path.join(
                    config['points']['export_dir'],
                    f'point_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                )
                points_manager.export_points(
                    export_file,
                    encoding=config['points']['export_encoding']
                )
                logger.info(f"Exported final point status to: {export_file}")
            except Exception as e:
                logger.error(f"Failed to export points: {e}")

if __name__ == "__main__":
    main()