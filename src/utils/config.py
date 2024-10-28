import yaml
import os
from typing import Dict, Any


class ConfigurationError(Exception):
    """Raised when there's an error with the configuration."""
    pass


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    Falls back to default values if no file is found.
    """
    # Default configuration
    default_config = {
        'serial': {
            'port': 'COM1',
            'baudrate': 19200,
            'timeout': 1
        },
        'monitor': {
            'poll_interval': 60,  # seconds
            'retry_delay': 5,  # seconds between retries
            'max_retries': 3  # maximum number of login retries
        },
        'panel': {
            'passcode': None,  # Must be set in config file or environment
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/monitor.log',
            'max_size': 1048576,  # 1MB
            'backup_count': 5,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

    # If no config path provided, look for it in standard locations
    if config_path is None:
        possible_locations = [
            'config/config.yaml',
            'config.yaml',
            os.path.expanduser('~/.simplex-monitor/config.yaml'),
            '/etc/simplex-monitor/config.yaml'
        ]

        for loc in possible_locations:
            if os.path.exists(loc):
                config_path = loc
                break

    # Load config file if it exists
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                # Deep update of default config with file config
                deep_update(default_config, file_config)
        except Exception as e:
            raise ConfigurationError(f"Error loading config file: {e}")

    # Check for environment variables
    env_mapping = {
        'SIMPLEX_PORT': ('serial', 'port'),
        'SIMPLEX_BAUDRATE': ('serial', 'baudrate'),
        'SIMPLEX_POLL_INTERVAL': ('monitor', 'poll_interval'),
        'SIMPLEX_PASSCODE': ('panel', 'passcode'),
        'SIMPLEX_LOG_LEVEL': ('logging', 'level'),
        'SIMPLEX_LOG_FILE': ('logging', 'file')
    }

    # Update config with environment variables if they exist
    for env_var, config_path in env_mapping.items():
        if env_var in os.environ:
            set_nested_value(default_config, config_path, os.environ[env_var])

    # Validate required settings
    if not default_config['panel']['passcode']:
        raise ConfigurationError("Panel passcode must be set in config file or SIMPLEX_PASSCODE environment variable")

    return default_config


def deep_update(base_dict: dict, update_dict: dict) -> None:
    """Recursively update a dictionary."""
    for key, value in update_dict.items():
        if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
            deep_update(base_dict[key], value)
        else:
            base_dict[key] = value


def set_nested_value(d: dict, path: tuple, value: Any) -> None:
    """Set a value in a nested dictionary using a path tuple."""
    current = d
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value


def create_default_config(path: str = 'config/config.yaml'):
    """Create a default configuration file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    default_config = {
        'serial': {
            'port': 'COM9',
            'baudrate': 19200,
            'timeout': 1
        },
        'monitor': {
            'poll_interval': 60,
            'retry_delay': 5,
            'max_retries': 3
        },
        'panel': {
            'passcode': 'CHANGE_ME'  # Remember to change this
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/monitor.log',
            'max_size': 1048576,
            'backup_count': 5,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

    with open(path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)


if __name__ == '__main__':
    # If run directly, create a default config file
    create_default_config()