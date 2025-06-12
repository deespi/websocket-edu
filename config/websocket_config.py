"""
WebSocket Configuration Settings
"""

import os
from typing import Dict, Any, Union

# Server Configuration
SERVER_CONFIG = {
    'host': os.getenv('WEBSOCKET_HOST', 'localhost'),
    'port': int(os.getenv('WEBSOCKET_PORT', 8765)),
    'sensor_read_interval': float(os.getenv('SENSOR_INTERVAL', 2.0)),  # seconds
    'max_clients': int(os.getenv('MAX_CLIENTS', 10)),
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'enable_ssl': os.getenv('ENABLE_SSL', 'False').lower() == 'true'
}

# Sensor Configuration
SENSOR_CONFIG = {
    'temperature': {
        'default_base_temp': 22.0,  # Celsius
        'default_variation': 5.0,
        'update_interval': 2.0,
        'min_temp': -10.0,
        'max_temp': 50.0
    },
    'humidity': {
        'default_base_humidity': 45.0,  # Percentage
        'min_humidity': 20.0,
        'max_humidity': 80.0,
        'update_interval': 2.0,
        'cycle_duration': 360  # degrees for daily cycle
    },
    'motion': {
        'default_detection_probability': 0.15,
        'update_interval': 1.0,
        'detection_duration_range': (2, 8)  # readings
    },
    'light': {
        'default_max_lux': 1000,
        'update_interval': 5.0,
        'min_lux': 0,
        'max_lux': 1200
    }
}

# Data Storage Configuration
DATA_CONFIG = {
    'max_readings_per_sensor': int(os.getenv('MAX_READINGS', 1000)),
    'cache_duration': 30,  # seconds
    'export_formats': ['json', 'csv'],
    'backup_interval': 3600,  # seconds (1 hour)
    'enable_persistence': os.getenv('ENABLE_PERSISTENCE', 'False').lower() == 'true',
    'data_retention_days': int(os.getenv('DATA_RETENTION_DAYS', 7))
}

# Application Configuration
APP_CONFIG = {
    'name': 'WebSocket IoT Simulator',
    'version': '1.0.0',
    'author': 'Educational Python Project',
    'description': 'WebSocket-based IoT sensor simulation for learning',
    'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
    'supported_protocols': ['websocket'],
    'default_encoding': 'utf-8'
}

# Visualization Configuration
VISUALIZATION_CONFIG = {
    'max_plot_points': int(os.getenv('MAX_PLOT_POINTS', 100)),
    'update_interval_ms': int(os.getenv('PLOT_UPDATE_MS', 500)),
    'colors': {
        'temperature': '#ff6b6b',  # Red
        'humidity': '#4ecdc4',     # Teal
        'motion': '#45b7d1',       # Blue
        'light': '#feca57'         # Yellow
    },
    'plot_style': 'seaborn-v0_8',  # matplotlib style
    'figure_size': (15, 10),
    'dpi': 100
}

# Alert Configuration
ALERT_CONFIG = {
    'temperature': {
        'high_threshold': float(os.getenv('TEMP_HIGH_ALERT', 28.0)),
        'low_threshold': float(os.getenv('TEMP_LOW_ALERT', 15.0)),
        'enabled': True
    },
    'humidity': {
        'high_threshold': float(os.getenv('HUMIDITY_HIGH_ALERT', 70.0)),
        'low_threshold': float(os.getenv('HUMIDITY_LOW_ALERT', 30.0)),
        'enabled': True
    },
    'motion': {
        'enabled': True,
        'cooldown_seconds': 5  # Prevent spam alerts
    },
    'light': {
        'low_threshold': float(os.getenv('LIGHT_LOW_ALERT', 10.0)),
        'enabled': False  # Disabled by default
    }
}

def get_config(section: str) -> Dict[str, Any]:
    """
    Get configuration for a specific section
    
    Args:
        section: Configuration section name
        
    Returns:
        Configuration dictionary for the section
    """
    configs = {
        'server': SERVER_CONFIG,
        'sensor': SENSOR_CONFIG,
        'data': DATA_CONFIG,
        'app': APP_CONFIG,
        'visualization': VISUALIZATION_CONFIG,
        'alert': ALERT_CONFIG
    }
    
    return configs.get(section, {})

def update_config(section: str, key: str, value: Union[str, int, float, bool]) -> bool:
    """
    Update a configuration value
    
    Args:
        section: Configuration section name
        key: Configuration key
        value: New value
        
    Returns:
        True if updated successfully, False otherwise
    """
    configs = {
        'server': SERVER_CONFIG,
        'sensor': SENSOR_CONFIG,
        'data': DATA_CONFIG,
        'app': APP_CONFIG,
        'visualization': VISUALIZATION_CONFIG,
        'alert': ALERT_CONFIG
    }
    
    if section in configs and key in configs[section]:
        configs[section][key] = value
        return True
    
    return False

def validate_config() -> Dict[str, str]:
    """
    Validate configuration values
    
    Returns:
        Dictionary of validation errors (empty if all valid)
    """
    errors = {}
    
    # Validate server config
    if SERVER_CONFIG['port'] < 1 or SERVER_CONFIG['port'] > 65535:
        errors['server.port'] = 'Port must be between 1 and 65535'
    
    if SERVER_CONFIG['sensor_read_interval'] < 0.1:
        errors['server.sensor_read_interval'] = 'Sensor read interval must be at least 0.1 seconds'
    
    if SERVER_CONFIG['max_clients'] < 1:
        errors['server.max_clients'] = 'Max clients must be at least 1'
    
    # Validate data config
    if DATA_CONFIG['max_readings_per_sensor'] < 10:
        errors['data.max_readings_per_sensor'] = 'Max readings must be at least 10'
    
    if DATA_CONFIG['cache_duration'] < 1:
        errors['data.cache_duration'] = 'Cache duration must be at least 1 second'
    
    # Validate sensor config
    for sensor_type, config in SENSOR_CONFIG.items():
        if 'update_interval' in config and config['update_interval'] < 0.1:
            errors[f'sensor.{sensor_type}.update_interval'] = f'{sensor_type} update interval must be at least 0.1 seconds'
    
    # Validate visualization config
    if VISUALIZATION_CONFIG['max_plot_points'] < 10:
        errors['visualization.max_plot_points'] = 'Max plot points must be at least 10'
    
    if VISUALIZATION_CONFIG['update_interval_ms'] < 100:
        errors['visualization.update_interval_ms'] = 'Plot update interval must be at least 100ms'
    
    return errors

def print_config():
    """Print current configuration (for debugging)"""
    print("🔧 Current Configuration")
    print("=" * 40)
    
    sections = [
        ('Server', SERVER_CONFIG),
        ('Sensors', SENSOR_CONFIG),
        ('Data', DATA_CONFIG),
        ('Visualization', VISUALIZATION_CONFIG),
        ('Alerts', ALERT_CONFIG),
        ('Application', APP_CONFIG)
    ]
    
    for section_name, config in sections:
        print(f"\n{section_name}:")
        for key, value in config.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")

def setup_environment():
    """Set up environment variables if not already set"""
    default_env_vars = {
        'WEBSOCKET_HOST': 'localhost',
        'WEBSOCKET_PORT': '8765',
        'SENSOR_INTERVAL': '2.0',
        'MAX_CLIENTS': '10',
        'LOG_LEVEL': 'INFO',
        'MAX_READINGS': '1000',
        'MAX_PLOT_POINTS': '100',
        'PLOT_UPDATE_MS': '500',
        'DEBUG': 'False',
        'ENABLE_SSL': 'False',
        'ENABLE_PERSISTENCE': 'False',
        'DATA_RETENTION_DAYS': '7',
        'TEMP_HIGH_ALERT': '28.0',
        'TEMP_LOW_ALERT': '15.0',
        'HUMIDITY_HIGH_ALERT': '70.0',
        'HUMIDITY_LOW_ALERT': '30.0',
        'LIGHT_LOW_ALERT': '10.0'
    }
    
    for var, default_value in default_env_vars.items():
        if var not in os.environ:
            os.environ[var] = default_value

# Initialize environment on import
setup_environment()

# Validate configuration on import
config_errors = validate_config()
if config_errors:
    print("⚠️  Configuration validation warnings:")
    for key, error in config_errors.items():
        print(f"  {key}: {error}")

if __name__ == "__main__":
    print_config()
    
    # Test configuration validation
    errors = validate_config()
    if errors:
        print("\n❌ Configuration Errors:")
        for key, error in errors.items():
            print(f"  {key}: {error}")
    else:
        print("\n✅ Configuration is valid!")