"""
Real-time Data Processing & Analytics
"""

import time
import statistics
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

from models.sensor_reading import SensorReading, AlertEvent, AlertLevel
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DataProcessor:
    """
    Real-time data processor for IoT sensor readings
    """
    
    def __init__(self, max_readings_per_sensor: int = 1000):
        """
        Initialize the data processor
        
        Args:
            max_readings_per_sensor: Maximum readings to store per sensor
        """
        self.max_readings = max_readings_per_sensor
        self._data_lock = threading.Lock()
        
        # Data storage using deque for efficient memory management
        self._sensor_data: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.max_readings)
        )
        
        # Statistics cache
        self._stats_cache: Dict[str, Dict] = {}
        self._cache_expiry: Dict[str, float] = {}
        self._cache_duration = 30  # seconds
        
        # Metadata tracking
        self._sensor_metadata: Dict[str, Dict] = {}
        self._total_readings = 0
        self._start_time = time.time()
        
        # Alert management
        self._alerts: List[AlertEvent] = []
        self._alert_thresholds = self._initialize_alert_thresholds()
    
    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize default alert thresholds"""
        return {
            'TemperatureSensor': {
                'high_threshold': 28.0,
                'low_threshold': 15.0
            },
            'HumiditySensor': {
                'high_threshold': 70.0,
                'low_threshold': 30.0
            },
            'LightSensor': {
                'low_threshold': 10.0
            }
        }
    
    def store_reading(self, reading: SensorReading) -> bool:
        """
        Store a sensor reading and process it
        
        Args:
            reading: SensorReading object to store
            
        Returns:
            True if stored successfully
        """
        try:
            with self._data_lock:
                sensor_id = reading.sensor_id
                
                # Store the reading
                self._sensor_data[sensor_id].append(reading)
                
                # Update metadata
                self._update_sensor_metadata(sensor_id, reading)
                
                # Invalidate cache for this sensor
                if sensor_id in self._stats_cache:
                    del self._stats_cache[sensor_id]
                    del self._cache_expiry[sensor_id]
                
                self._total_readings += 1
                
                # Check for alerts
                self._check_alerts(reading)
            
            logger.debug(f"Stored reading for {sensor_id}: {reading.value} {reading.unit}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing reading: {e}")
            return False
    
    def _update_sensor_metadata(self, sensor_id: str, reading: SensorReading):
        """Update metadata for a sensor"""
        if sensor_id not in self._sensor_metadata:
            self._sensor_metadata[sensor_id] = {
                'first_reading': reading.timestamp.isoformat(),
                'sensor_type': reading.sensor_type.value,
                'location': reading.location,
                'name': reading.name,
                'unit': reading.unit
            }
        
        self._sensor_metadata[sensor_id].update({
            'last_reading': reading.timestamp.isoformat(),
            'total_readings': len(self._sensor_data[sensor_id]),
            'status': reading.status.value
        })
    
    def _check_alerts(self, reading: SensorReading):
        """Check if reading triggers any alerts"""
        sensor_type = reading.sensor_type.value
        thresholds = self._alert_thresholds.get(sensor_type, {})
        
        if not thresholds or not reading.is_numeric():
            return
        
        value = reading.value
        alerts = []
        
        # Check high threshold
        if 'high_threshold' in thresholds and value > thresholds['high_threshold']:
            alert = AlertEvent(
                alert_id=f"{reading.sensor_id}_{int(time.time())}",
                sensor_id=reading.sensor_id,
                alert_type="high_threshold",
                level=AlertLevel.WARNING,
                message=f"{sensor_type} reading above threshold: {value} {reading.unit}",
                value=value,
                threshold=thresholds['high_threshold']
            )
            alerts.append(alert)
        
        # Check low threshold
        if 'low_threshold' in thresholds and value < thresholds['low_threshold']:
            alert = AlertEvent(
                alert_id=f"{reading.sensor_id}_{int(time.time())}",
                sensor_id=reading.sensor_id,
                alert_type="low_threshold",
                level=AlertLevel.WARNING,
                message=f"{sensor_type} reading below threshold: {value} {reading.unit}",
                value=value,
                threshold=thresholds['low_threshold']
            )
            alerts.append(alert)
        
        # Store alerts
        for alert in alerts:
            self._alerts.append(alert)
            logger.warning(f"🚨 Alert: {alert.message}")
    
    def get_sensor_history(self, sensor_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get historical readings for a sensor
        
        Args:
            sensor_id: ID of the sensor
            limit: Maximum number of readings to return
            
        Returns:
            List of sensor readings as dictionaries
        """
        with self._data_lock:
            if sensor_id not in self._sensor_data:
                return []
            
            readings = list(self._sensor_data[sensor_id])
            
            # Convert to dictionaries and reverse for most recent first
            reading_dicts = [reading.to_dict() for reading in reversed(readings)]
            
            if limit:
                reading_dicts = reading_dicts[:limit]
            
            return reading_dicts
    
    def get_recent_readings(self, sensor_id: str, minutes: int = 10) -> List[SensorReading]:
        """
        Get readings from the last N minutes
        
        Args:
            sensor_id: ID of the sensor
            minutes: Number of minutes to look back
            
        Returns:
            List of recent sensor readings
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self._data_lock:
            if sensor_id not in self._sensor_data:
                return []
            
            recent_readings = []
            for reading in reversed(self._sensor_data[sensor_id]):
                if reading.timestamp >= cutoff_time:
                    recent_readings.append(reading)
                else:
                    break  # Readings are ordered, so we can stop
            
            return recent_readings
    
    def get_sensor_statistics(self, sensor_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Calculate statistics for a sensor
        
        Args:
            sensor_id: ID of the sensor
            use_cache: Whether to use cached statistics
            
        Returns:
            Dictionary containing sensor statistics
        """
        # Check cache first
        if use_cache and self._is_cache_valid(sensor_id):
            return self._stats_cache[sensor_id].copy()
        
        with self._data_lock:
            if sensor_id not in self._sensor_data or not self._sensor_data[sensor_id]:
                return {}
            
            readings = list(self._sensor_data[sensor_id])
            
            # Extract numeric values from active readings
            values = []
            for reading in readings:
                if reading.status.value == 'active' and reading.is_numeric():
                    values.append(reading.value)
            
            if not values:
                return {}
            
            # Calculate statistics
            stats = {
                'sensor_id': sensor_id,
                'total_readings': len(readings),
                'active_readings': len(values),
                'min_value': min(values),
                'max_value': max(values),
                'average': round(statistics.mean(values), 2),
                'median': round(statistics.median(values), 2),
                'latest_value': values[-1] if values else None,
                'unit': readings[-1].unit if readings else '',
                'calculation_time': datetime.now().isoformat()
            }
            
            # Add standard deviation if we have enough data
            if len(values) > 1:
                stats['std_deviation'] = round(statistics.stdev(values), 2)
                stats['variance'] = round(statistics.variance(values), 2)
            
            # Add trend information
            if len(values) >= 5:
                recent_avg = statistics.mean(values[-5:])
                older_avg = statistics.mean(values[-10:-5]) if len(values) >= 10 else recent_avg
                
                if recent_avg > older_avg * 1.05:
                    trend = 'increasing'
                elif recent_avg < older_avg * 0.95:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
                
                stats['trend'] = trend
                stats['trend_change'] = round(((recent_avg - older_avg) / older_avg) * 100, 2) if older_avg != 0 else 0
            
            # Cache the results
            self._stats_cache[sensor_id] = stats.copy()
            self._cache_expiry[sensor_id] = time.time() + self._cache_duration
            
            return stats
    
    def _is_cache_valid(self, sensor_id: str) -> bool:
        """Check if cached statistics are still valid"""
        return (sensor_id in self._stats_cache and 
                sensor_id in self._cache_expiry and 
                time.time() < self._cache_expiry[sensor_id])
    
    def get_all_sensor_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all sensors"""
        stats = {}
        for sensor_id in self._sensor_data.keys():
            stats[sensor_id] = self.get_sensor_statistics(sensor_id)
        return stats
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get overall system information and statistics"""
        uptime = time.time() - self._start_time
        
        with self._data_lock:
            active_sensors = len([
                meta for meta in self._sensor_metadata.values() 
                if meta.get('total_readings', 0) > 0
            ])
            
            total_alerts = len(self._alerts)
            active_alerts = len([alert for alert in self._alerts if alert.is_active()])
        
        return {
            'total_sensors': len(self._sensor_data),
            'active_sensors': active_sensors,
            'total_readings': self._total_readings,
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'uptime_seconds': round(uptime, 2),
            'uptime_hours': round(uptime / 3600, 2),
            'memory_usage_mb': self._estimate_memory_usage(),
            'cache_hit_ratio': self._calculate_cache_hit_ratio(),
            'sensors': list(self._sensor_metadata.keys()),
            'processing_rate': round(self._total_readings / uptime, 2) if uptime > 0 else 0
        }
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB (rough approximation)"""
        total_items = sum(len(deque_obj) for deque_obj in self._sensor_data.values())
        estimated_bytes = total_items * 500  # Rough estimate per reading
        return round(estimated_bytes / (1024 * 1024), 2)
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        if not hasattr(self, '_cache_hits'):
            self._cache_hits = 0
            self._cache_misses = 0
        
        total_requests = self._cache_hits + self._cache_misses
        if total_requests == 0:
            return 0.0
        
        return round(self._cache_hits / total_requests, 2)
    
    def get_alerts(self, 
                   sensor_id: Optional[str] = None, 
                   active_only: bool = False,
                   minutes: Optional[int] = None) -> List[AlertEvent]:
        """
        Get alerts with optional filtering
        
        Args:
            sensor_id: Filter by sensor ID
            active_only: Only return active (unresolved) alerts
            minutes: Only return alerts from last N minutes
            
        Returns:
            List of matching alerts
        """
        filtered_alerts = self._alerts.copy()
        
        # Filter by sensor ID
        if sensor_id:
            filtered_alerts = [alert for alert in filtered_alerts if alert.sensor_id == sensor_id]
        
        # Filter by active status
        if active_only:
            filtered_alerts = [alert for alert in filtered_alerts if alert.is_active()]
        
        # Filter by time
        if minutes:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            filtered_alerts = [alert for alert in filtered_alerts if alert.timestamp >= cutoff_time]
        
        return filtered_alerts
    
    def export_data(self, 
                   sensor_id: Optional[str] = None, 
                   format_type: str = 'json',
                   include_metadata: bool = True) -> str:
        """
        Export sensor data
        
        Args:
            sensor_id: Specific sensor to export (None for all)
            format_type: Export format ('json' or 'csv')
            include_metadata: Include sensor metadata
            
        Returns:
            Exported data as string
        """
        with self._data_lock:
            if sensor_id:
                if sensor_id in self._sensor_data:
                    data = {sensor_id: [reading.to_dict() for reading in self._sensor_data[sensor_id]]}
                else:
                    data = {}
            else:
                data = {
                    sid: [reading.to_dict() for reading in readings] 
                    for sid, readings in self._sensor_data.items()
                }
            
            export_package = {
                'export_timestamp': datetime.now().isoformat(),
                'sensor_data': data
            }
            
            if include_metadata:
                export_package['metadata'] = self._sensor_metadata.copy()
                export_package['system_info'] = self.get_system_info()
        
        if format_type.lower() == 'json':
            return json.dumps(export_package, indent=2, default=str)
        elif format_type.lower() == 'csv':
            return self._export_as_csv(export_package['sensor_data'])
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_as_csv(self, data: Dict) -> str:
        """Export data as CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'sensor_id', 'sensor_type', 'timestamp', 'value', 'unit', 
            'status', 'location', 'name', 'reading_count'
        ])
        
        # Write data
        for sensor_id, readings in data.items():
            for reading in readings:
                writer.writerow([
                    reading.get('sensor_id', ''),
                    reading.get('sensor_type', ''),
                    reading.get('timestamp', ''),
                    reading.get('value', ''),
                    reading.get('unit', ''),
                    reading.get('status', ''),
                    reading.get('location', ''),
                    reading.get('name', ''),
                    reading.get('reading_count', '')
                ])
        
        return output.getvalue()
    
    def clear_sensor_data(self, sensor_id: Optional[str] = None):
        """Clear sensor data"""
        with self._data_lock:
            if sensor_id:
                if sensor_id in self._sensor_data:
                    self._sensor_data[sensor_id].clear()
                    if sensor_id in self._stats_cache:
                        del self._stats_cache[sensor_id]
                        del self._cache_expiry[sensor_id]
                    if sensor_id in self._sensor_metadata:
                        del self._sensor_metadata[sensor_id]
            else:
                self._sensor_data.clear()
                self._stats_cache.clear()
                self._cache_expiry.clear()
                self._sensor_metadata.clear()
                self._alerts.clear()
                self._total_readings = 0

# Example usage and testing
if __name__ == "__main__":
    from models.sensor_reading import create_temperature_reading, create_humidity_reading
    
    print("🧪 Testing Data Processor")
    print("-" * 30)
    
    # Create processor
    processor = DataProcessor(max_readings_per_sensor=100)
    
    # Add test data
    for i in range(20):
        temp_reading = create_temperature_reading(
            "temp_01", 
            22 + (i * 0.5), 
            "Test Room"
        )
        humidity_reading = create_humidity_reading(
            "hum_01", 
            45 + (i * 1.5), 
            "Test Room"
        )
        
        processor.store_reading(temp_reading)
        processor.store_reading(humidity_reading)
    
    # Test statistics
    temp_stats = processor.get_sensor_statistics('temp_01')
    print(f"📊 Temperature Stats: {temp_stats}")
    
    # Test system info
    system_info = processor.get_system_info()
    print(f"🖥️  System Info: {system_info}")
    
    # Test alerts
    alerts = processor.get_alerts()
    print(f"🚨 Total Alerts: {len(alerts)}")
    
    print("\n✅ Data processor testing complete!")