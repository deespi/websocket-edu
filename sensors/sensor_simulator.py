"""
IoT Sensor Simulation Logic
"""

import random
import time
import math
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from models.sensor_reading import SensorReading, SensorType, SensorStatus

class BaseSensor(ABC):
    """
    Abstract base class for all IoT sensors
    """
    
    def __init__(self, sensor_id: str, location: str, name: Optional[str] = None):
        """
        Initialize base sensor
        
        Args:
            sensor_id: Unique sensor identifier
            location: Physical location of sensor
            name: Human-readable sensor name
        """
        self.sensor_id = sensor_id
        self.location = location
        self.name = name or f"Sensor {sensor_id}"
        self.is_active = True
        self.last_reading_time = None
        self._reading_count = 0
        self._status = SensorStatus.ACTIVE
        
        # Metadata for sensor management
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'total_readings': 0,
            'last_error': None,
            'calibration_status': 'calibrated'
        }
    
    @abstractmethod
    def _generate_reading(self) -> float:
        """
        Generate a sensor reading value
        
        Must be implemented by subclasses to provide sensor-specific logic
        
        Returns:
            Sensor reading value
        """
        pass
    
    @abstractmethod
    def get_sensor_type(self) -> SensorType:
        """
        Get the sensor type
        
        Returns:
            SensorType enum value
        """
        pass
    
    @abstractmethod
    def get_unit(self) -> str:
        """
        Get the unit of measurement for this sensor
        
        Returns:
            Unit string (e.g., "°C", "%", "lux")
        """
        pass
    
    def read(self) -> SensorReading:
        """
        Read data from the sensor
        
        Returns:
            SensorReading object with current sensor data
        """
        if not self.is_active:
            return SensorReading(
                sensor_id=self.sensor_id,
                sensor_type=self.get_sensor_type(),
                value=0.0,
                unit=self.get_unit(),
                status=SensorStatus.INACTIVE,
                location=self.location,
                name=self.name,
                reading_count=self._reading_count
            )
        
        try:
            reading_value = self._generate_reading()
            self.last_reading_time = time.time()
            self._reading_count += 1
            self.metadata['total_readings'] = self._reading_count
            
            return SensorReading(
                sensor_id=self.sensor_id,
                sensor_type=self.get_sensor_type(),
                value=reading_value,
                unit=self.get_unit(),
                status=SensorStatus.ACTIVE,
                location=self.location,
                name=self.name,
                reading_count=self._reading_count,
                metadata=self.metadata.copy()
            )
            
        except Exception as e:
            self.metadata['last_error'] = str(e)
            return SensorReading(
                sensor_id=self.sensor_id,
                sensor_type=self.get_sensor_type(),
                value=0.0,
                unit=self.get_unit(),
                status=SensorStatus.ERROR,
                location=self.location,
                name=self.name,
                reading_count=self._reading_count,
                metadata={'error': str(e)}
            )
    
    @property
    def reading_count(self) -> int:
        """Get the total number of readings taken"""
        return self._reading_count
    
    def reset_counter(self):
        """Reset the reading counter"""
        self._reading_count = 0
        self.metadata['total_readings'] = 0
    
    def calibrate(self):
        """Simulate sensor calibration"""
        self.metadata['calibration_status'] = 'calibrated'
        self.metadata['last_calibration'] = datetime.now().isoformat()
    
    def __str__(self) -> str:
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({self.sensor_id}) - {status}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.sensor_id}', '{self.location}')"


class TemperatureSensor(BaseSensor):
    """
    Temperature sensor simulation
    """
    
    def __init__(self, sensor_id: str, location: str, name: Optional[str] = None, 
                 base_temp: float = 22.0, variation: float = 5.0):
        super().__init__(sensor_id, location, name)
        self.base_temperature = base_temp  # Base temperature in Celsius
        self.variation = variation         # Maximum variation from base
        self._current_trend = 0.0         # Current temperature trend
        self._trend_duration = 0          # How long current trend lasts
        self._daily_cycle_position = random.uniform(0, 360)  # Daily temperature cycle
    
    def get_sensor_type(self) -> SensorType:
        return SensorType.TEMPERATURE
    
    def get_unit(self) -> str:
        return "°C"
    
    def _generate_reading(self) -> float:
        """
        Generate realistic temperature reading with trends and daily cycles
        """
        # Daily cycle component (simulates day/night temperature variation)
        daily_variation = math.sin(math.radians(self._daily_cycle_position)) * 3
        self._daily_cycle_position += 0.5  # Advance cycle slowly
        
        # Update trend occasionally
        if self._trend_duration <= 0:
            self._current_trend = random.uniform(-0.5, 0.5)
            self._trend_duration = random.randint(5, 15)
        
        self._trend_duration -= 1
        
        # Generate reading with multiple components
        trend_component = self._current_trend
        random_component = random.uniform(-0.3, 0.3)
        
        # Calculate temperature
        temperature = (self.base_temperature + 
                      daily_variation + 
                      trend_component + 
                      random_component)
        
        # Apply bounds checking
        temperature = max(temperature, self.base_temperature - self.variation)
        temperature = min(temperature, self.base_temperature + self.variation)
        
        # Slowly drift base temperature for long-term variation
        self.base_temperature += random.uniform(-0.02, 0.02)
        
        return round(temperature, 1)
    
    def set_base_temperature(self, temp: float):
        """Set the base temperature for the sensor"""
        self.base_temperature = temp


class HumiditySensor(BaseSensor):
    """
    Humidity sensor simulation
    """
    
    def __init__(self, sensor_id: str, location: str, name: Optional[str] = None,
                 base_humidity: float = 45.0):
        super().__init__(sensor_id, location, name)
        self.base_humidity = base_humidity
        self._cycle_position = random.uniform(0, 360)  # For cyclical variation
        self._weather_factor = random.uniform(0.8, 1.2)  # Simulates weather influence
    
    def get_sensor_type(self) -> SensorType:
        return SensorType.HUMIDITY
    
    def get_unit(self) -> str:
        return "%"
    
    def _generate_reading(self) -> float:
        """
        Generate humidity reading with cyclical patterns
        """
        # Cyclical component (daily humidity cycle)
        cycle_component = math.sin(math.radians(self._cycle_position)) * 8
        self._cycle_position += random.uniform(1, 3)  # Advance cycle
        
        # Weather influence (slow changes)
        if random.random() < 0.1:  # 10% chance to change weather
            self._weather_factor = random.uniform(0.8, 1.2)
        
        weather_component = (self._weather_factor - 1) * 10
        
        # Random variation
        random_component = random.uniform(-3, 3)
        
        # Calculate humidity
        humidity = (self.base_humidity + 
                   cycle_component + 
                   weather_component + 
                   random_component)
        
        # Ensure humidity stays within realistic bounds (20-80%)
        humidity = max(20.0, min(80.0, humidity))
        
        return round(humidity, 1)


class MotionSensor(BaseSensor):
    """
    Motion sensor simulation
    """
    
    def __init__(self, sensor_id: str, location: str, name: Optional[str] = None,
                 detection_probability: float = 0.15):
        super().__init__(sensor_id, location, name)
        self.detection_probability = detection_probability
        self._motion_state = False
        self._state_duration = 0
        self._cooldown_timer = 0
        self._activity_pattern = self._generate_activity_pattern()
    
    def get_sensor_type(self) -> SensorType:
        return SensorType.MOTION
    
    def get_unit(self) -> str:
        return "detected"
    
    def _generate_activity_pattern(self):
        """Generate daily activity pattern (higher probability during certain hours)"""
        # Simulate higher activity during day hours (8-22)
        pattern = {}
        for hour in range(24):
            if 8 <= hour <= 22:
                pattern[hour] = 1.5  # Higher activity during day
            else:
                pattern[hour] = 0.3  # Lower activity during night
        return pattern
    
    def _generate_reading(self) -> float:
        """
        Generate motion detection reading
        
        Returns 1.0 for motion detected, 0.0 for no motion
        Uses probability, state duration, and activity patterns
        """
        # Apply cooldown
        if self._cooldown_timer > 0:
            self._cooldown_timer -= 1
            return 0.0
        
        # If currently detecting motion, continue for duration
        if self._motion_state and self._state_duration > 0:
            self._state_duration -= 1
            if self._state_duration == 0:
                self._motion_state = False
                self._cooldown_timer = random.randint(3, 8)  # Cooldown period
            return 1.0
        
        # Check for new motion based on time-dependent probability
        current_hour = datetime.now().hour
        activity_multiplier = self._activity_pattern.get(current_hour, 1.0)
        adjusted_probability = self.detection_probability * activity_multiplier
        
        if random.random() < adjusted_probability:
            self._motion_state = True
            self._state_duration = random.randint(2, 8)  # Motion lasts 2-8 readings
            return 1.0
        
        return 0.0
    
    @property
    def is_motion_detected(self) -> bool:
        """Check if motion is currently detected"""
        return self._motion_state
    
    def set_sensitivity(self, probability: float):
        """Adjust motion detection sensitivity (0.0 to 1.0)"""
        self.detection_probability = max(0.0, min(1.0, probability))


class LightSensor(BaseSensor):
    """
    Light sensor simulation
    """
    
    def __init__(self, sensor_id: str, location: str, name: Optional[str] = None):
        super().__init__(sensor_id, location, name)
        self.time_offset = random.uniform(0, 24)  # Random time offset
        self._cloud_factor = 1.0  # Simulates cloud cover
        self._indoor_factor = 0.3 if 'indoor' in location.lower() else 1.0
    
    def get_sensor_type(self) -> SensorType:
        return SensorType.LIGHT
    
    def get_unit(self) -> str:
        return "lux"
    
    def _generate_reading(self) -> float:
        """
        Generate light intensity reading with realistic day/night patterns
        """
        # Get current hour (with offset for variety)
        current_hour = (datetime.now().hour + self.time_offset) % 24
        
        # Calculate base light level
        if 6 <= current_hour <= 18:  # Daytime
            # Peak at solar noon (hour 12)
            sun_angle = abs(current_hour - 12) / 6
            base_light = 1000 * (1 - sun_angle * 0.8)  # Max 1000 lux at noon
        else:  # Nighttime
            base_light = random.uniform(0.1, 2.0)  # Very low light
        
        # Apply cloud factor (changes slowly)
        if random.random() < 0.05:  # 5% chance to change cloud cover
            self._cloud_factor = random.uniform(0.3, 1.0)
        
        base_light *= self._cloud_factor
        
        # Apply indoor factor
        base_light *= self._indoor_factor
        
        # Add some random variation
        variation = random.uniform(-20, 20)
        light_level = max(0, base_light + variation)
        
        return round(light_level, 1)


# Factory function for creating sensors
def create_sensor(sensor_type: str, sensor_id: str, location: str, **kwargs) -> BaseSensor:
    """
    Factory function to create sensor instances
    
    Args:
        sensor_type: Type of sensor to create
        sensor_id: Unique sensor identifier
        location: Sensor location
        **kwargs: Additional sensor-specific parameters
        
    Returns:
        BaseSensor instance
    """
    sensor_classes = {
        'temperature': TemperatureSensor,
        'humidity': HumiditySensor,
        'motion': MotionSensor,
        'light': LightSensor
    }
    
    if sensor_type.lower() not in sensor_classes:
        raise ValueError(f"Unknown sensor type: {sensor_type}")
    
    sensor_class = sensor_classes[sensor_type.lower()]
    return sensor_class(sensor_id, location, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    print("🔬 Testing Sensor Classes")
    print("-" * 30)
    
    # Create test sensors
    sensors = [
        TemperatureSensor("temp_01", "Living Room"),
        HumiditySensor("hum_01", "Bedroom"),
        MotionSensor("motion_01", "Hallway"),
        LightSensor("light_01", "Kitchen")
    ]
    
    # Test sensor readings
    for sensor in sensors:
        print(f"\n{sensor}")
        for i in range(3):
            reading = sensor.read()
            print(f"  Reading {i+1}: {reading.get_display_value()}")
            print(f"    Status: {reading.status.value}")
            print(f"    Type: {reading.sensor_type.value}")
    
    # Test factory function
    print(f"\n🏭 Testing Factory Function:")
    factory_sensor = create_sensor('temperature', 'factory_temp', 'Test Location')
    factory_reading = factory_sensor.read()
    print(f"Factory sensor: {factory_reading.get_display_value()}")
    
    # Test sensor state management
    print(f"\n🔧 Testing State Management:")
    temp_sensor = sensors[0]
    print(f"Initial readings: {temp_sensor.reading_count}")
    temp_sensor.read()
    temp_sensor.read()
    print(f"After 2 readings: {temp_sensor.reading_count}")
    
    temp_sensor.is_active = False
    inactive_reading = temp_sensor.read()
    print(f"Inactive sensor status: {inactive_reading.status.value}")
    
    print("\n✅ Sensor testing complete!")