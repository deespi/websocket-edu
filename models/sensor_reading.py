"""
Data Models for Sensor Readings
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
from enum import Enum

class SensorStatus(Enum):
    """Sensor status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class SensorType(Enum):
    """Sensor type enumeration"""
    TEMPERATURE = "TemperatureSensor"
    HUMIDITY = "HumiditySensor"
    MOTION = "MotionSensor"
    LIGHT = "LightSensor"
    PRESSURE = "PressureSensor"
    AIR_QUALITY = "AirQualitySensor"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class SensorReading:
    """
    Data model for sensor readings
    """
    
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    status: SensorStatus = SensorStatus.ACTIVE
    timestamp: datetime = field(default_factory=datetime.now)
    location: str = ""
    name: str = ""
    reading_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Set default name if not provided
        if not self.name:
            self.name = f"Sensor {self.sensor_id}"
        
        # Ensure sensor_type is enum
        if isinstance(self.sensor_type, str):
            try:
                self.sensor_type = SensorType(self.sensor_type)
            except ValueError:
                # Handle unknown sensor types
                self.sensor_type = SensorType.TEMPERATURE
        
        # Ensure status is enum
        if isinstance(self.status, str):
            try:
                self.status = SensorStatus(self.status)
            except ValueError:
                self.status = SensorStatus.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert sensor reading to dictionary
        
        Returns:
            Dictionary representation of the sensor reading
        """
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type.value,
            'value': self.value,
            'unit': self.unit,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'location': self.location,
            'name': self.name,
            'reading_count': self.reading_count,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """
        Convert sensor reading to JSON string
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SensorReading':
        """
        Create sensor reading from dictionary
        
        Args:
            data: Dictionary containing sensor reading data
            
        Returns:
            SensorReading instance
        """
        # Parse timestamp if it's a string
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            sensor_id=data['sensor_id'],
            sensor_type=data['sensor_type'],
            value=float(data['value']),
            unit=data['unit'],
            status=data.get('status', SensorStatus.ACTIVE),
            timestamp=timestamp,
            location=data.get('location', ''),
            name=data.get('name', ''),
            reading_count=data.get('reading_count', 0),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SensorReading':
        """
        Create sensor reading from JSON string
        
        Args:
            json_str: JSON string containing sensor reading data
            
        Returns:
            SensorReading instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_numeric(self) -> bool:
        """Check if the sensor value is numeric"""
        try:
            float(self.value)
            return True
        except (ValueError, TypeError):
            return False
    
    def get_display_value(self) -> str:
        """Get formatted display value"""
        if self.is_numeric():
            return f"{self.value:.1f} {self.unit}"
        else:
            return f"{self.value} {self.unit}"
    
    def validate(self) -> List[str]:
        """
        Validate sensor reading data
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.sensor_id:
            errors.append("sensor_id is required")
        
        if not self.unit:
            errors.append("unit is required")
        
        if self.value is None:
            errors.append("value is required")
        
        if not isinstance(self.timestamp, datetime):
            errors.append("timestamp must be a datetime object")
        
        return errors

@dataclass
class SensorMetadata:
    """
    Metadata for sensor configuration and status
    """
    
    sensor_id: str
    sensor_type: SensorType
    name: str
    location: str
    description: str = ""
    manufacturer: str = ""
    model: str = ""
    firmware_version: str = ""
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    calibration_date: Optional[datetime] = None
    is_active: bool = True
    sampling_rate: float = 1.0  # Hz
    accuracy: Optional[float] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type.value,
            'name': self.name,
            'location': self.location,
            'description': self.description,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'firmware_version': self.firmware_version,
            'installation_date': self.installation_date.isoformat() if self.installation_date else None,
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'calibration_date': self.calibration_date.isoformat() if self.calibration_date else None,
            'is_active': self.is_active,
            'sampling_rate': self.sampling_rate,
            'accuracy': self.accuracy,
            'range_min': self.range_min,
            'range_max': self.range_max,
            'configuration': self.configuration
        }
    
    def is_due_for_maintenance(self, days: int = 30) -> bool:
        """Check if sensor is due for maintenance"""
        if not self.last_maintenance:
            return True
        
        days_since_maintenance = (datetime.now() - self.last_maintenance).days
        return days_since_maintenance >= days
    
    def is_calibration_current(self, days: int = 90) -> bool:
        """Check if sensor calibration is current"""
        if not self.calibration_date:
            return False
        
        days_since_calibration = (datetime.now() - self.calibration_date).days
        return days_since_calibration < days

@dataclass
class AlertEvent:
    """
    Data model for alert events
    
    Educational concepts:
    - Event modeling
    - Alert management
    - Notification patterns
    """
    
    alert_id: str
    sensor_id: str
    alert_type: str
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_by: str = ""
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure level is enum
        if isinstance(self.level, str):
            try:
                self.level = AlertLevel(self.level)
            except ValueError:
                self.level = AlertLevel.WARNING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'sensor_id': self.sensor_id,
            'alert_type': self.alert_type,
            'level': self.level.value,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'metadata': self.metadata
        }
    
    def acknowledge(self, user: str = "system"):
        """Acknowledge the alert"""
        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now()
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.now()
    
    def is_active(self) -> bool:
        """Check if alert is still active"""
        return not self.resolved
    
    def get_duration(self) -> Optional[float]:
        """Get alert duration in seconds"""
        if self.resolved_at:
            return (self.resolved_at - self.timestamp).total_seconds()
        else:
            return (datetime.now() - self.timestamp).total_seconds()

# Utility functions for working with sensor data
def create_temperature_reading(sensor_id: str, value: float, location: str = "") -> SensorReading:
    """Create a temperature sensor reading"""
    return SensorReading(
        sensor_id=sensor_id,
        sensor_type=SensorType.TEMPERATURE,
        value=value,
        unit="°C",
        location=location
    )

def create_humidity_reading(sensor_id: str, value: float, location: str = "") -> SensorReading:
    """Create a humidity sensor reading"""
    return SensorReading(
        sensor_id=sensor_id,
        sensor_type=SensorType.HUMIDITY,
        value=value,
        unit="%",
        location=location
    )

def create_motion_reading(sensor_id: str, detected: bool, location: str = "") -> SensorReading:
    """Create a motion sensor reading"""
    return SensorReading(
        sensor_id=sensor_id,
        sensor_type=SensorType.MOTION,
        value=1.0 if detected else 0.0,
        unit="detected",
        location=location
    )

def create_light_reading(sensor_id: str, value: float, location: str = "") -> SensorReading:
    """Create a light sensor reading"""
    return SensorReading(
        sensor_id=sensor_id,
        sensor_type=SensorType.LIGHT,
        value=value,
        unit="lux",
        location=location
    )

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Data Models")
    print("-" * 30)
    
    # Create test sensor readings
    temp_reading = create_temperature_reading("temp_01", 22.5, "Living Room")
    humidity_reading = create_humidity_reading("hum_01", 45.0, "Bedroom")
    motion_reading = create_motion_reading("motion_01", True, "Front Door")
    
    print("📊 Sample Sensor Readings:")
    print(f"Temperature: {temp_reading.get_display_value()}")
    print(f"Humidity: {humidity_reading.get_display_value()}")
    print(f"Motion: {motion_reading.get_display_value()}")
    
    # Test JSON serialization
    temp_json = temp_reading.to_json()
    temp_restored = SensorReading.from_json(temp_json)
    print(f"\n🔄 JSON serialization test: {temp_restored.sensor_id} = {temp_restored.value}")
    
    # Test alert creation
    from uuid import uuid4
    alert = AlertEvent(
        alert_id=str(uuid4()),
        sensor_id="temp_01",
        alert_type="high_temperature",
        level=AlertLevel.WARNING,
        message="Temperature above threshold",
        value=28.5,
        threshold=25.0
    )
    
    print(f"\n🚨 Alert created: {alert.message}")
    print(f"Alert level: {alert.level.value}")
    print(f"Alert active: {alert.is_active()}")
    
    print("\n✅ Data model testing complete!")