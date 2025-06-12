"""
Main WebSocket Application Orchestrator
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any

from config.websocket_config import SERVER_CONFIG
from sensors.sensor_simulator import TemperatureSensor, HumiditySensor, MotionSensor, create_sensor
from data.data_processor import DataProcessor
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WebSocketServer:
    """
    Main WebSocket server for sensor simulation
    """
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the WebSocket server
        
        Args:
            host: Server host (defaults to config)
            port: Server port (defaults to config)
        """
        self.host = host or SERVER_CONFIG['host']
        self.port = port or SERVER_CONFIG['port']
        
        # Connection management
        self.connected_clients: Set = set()
        self.client_count = 0
        
        # Sensor management
        self.sensors = {}
        self.data_processor = DataProcessor()
        
        # Server state
        self.is_running = False
        self.server = None
        
        # Initialize sensors
        self._initialize_sensors()
    
    def _initialize_sensors(self):
        """Initialize sensor instances with realistic configurations"""
        sensor_configs = [
            {
                'type': 'temperature',
                'id': 'temperature',
                'location': 'Living Room',
                'name': 'Living Room Temperature',
                'base_temp': 22.0,
                'variation': 5.0
            },
            {
                'type': 'humidity', 
                'id': 'humidity',
                'location': 'Living Room',
                'name': 'Living Room Humidity',
                'base_humidity': 45.0
            },
            {
                'type': 'motion',
                'id': 'motion',
                'location': 'Front Door', 
                'name': 'Front Door Motion',
                'detection_probability': 0.15
            }
        ]
        
        for config in sensor_configs:
            sensor_type = config.pop('type')
            sensor_id = config.pop('id')
            location = config.pop('location')
            
            try:
                sensor = create_sensor(sensor_type, sensor_id, location, **config)
                self.sensors[sensor_id] = sensor
                logger.info(f"Initialized {sensor_type} sensor: {sensor_id}")
            except Exception as e:
                logger.error(f"Failed to initialize sensor {sensor_id}: {e}")
        
        logger.info(f"✅ Initialized {len(self.sensors)} sensors")
    
    async def register_client(self, websocket, path=None):
        """
        Register a new WebSocket client
        
        Args:
            websocket: WebSocket connection
            path: Connection path (optional)
        """
        self.connected_clients.add(websocket)
        self.client_count += 1
        
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"📱 Client connected: {client_info} (Total: {len(self.connected_clients)})")
        
        # Send initial sensor list to new client
        await self._send_sensor_list(websocket)
    
    async def unregister_client(self, websocket):
        """
        Unregister a WebSocket client
        
        Args:
            websocket: WebSocket connection to remove
        """
        self.connected_clients.discard(websocket)
        logger.info(f"📱 Client disconnected (Total: {len(self.connected_clients)})")
    
    async def _send_sensor_list(self, websocket):
        """
        Send list of available sensors to a client
        
        Args:
            websocket: Target WebSocket connection
        """
        sensor_info = {
            'type': 'sensor_list',
            'sensors': [
                {
                    'id': sensor.sensor_id,
                    'name': sensor.name,
                    'location': sensor.location,
                    'sensor_type': sensor.__class__.__name__,
                    'status': 'active' if sensor.is_active else 'inactive',
                    'unit': sensor.get_unit(),
                    'reading_count': sensor.reading_count
                }
                for sensor in self.sensors.values()
            ],
            'timestamp': datetime.now().isoformat(),
            'server_info': {
                'total_sensors': len(self.sensors),
                'connected_clients': len(self.connected_clients)
            }
        }
        
        try:
            await websocket.send(json.dumps(sensor_info))
            logger.debug(f"📤 Sent sensor list to client")
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
        except Exception as e:
            logger.error(f"Error sending sensor list: {e}")
    
    async def broadcast_sensor_data(self, sensor_reading):
        """
        Broadcast sensor data to all connected clients
        
        Args:
            sensor_reading: SensorReading object to broadcast
        """
        if not self.connected_clients:
            return
        
        message = {
            'type': 'sensor_data',
            'data': sensor_reading.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store data in processor
        self.data_processor.store_reading(sensor_reading)
        
        # Broadcast to all clients
        disconnected_clients = set()
        message_json = json.dumps(message)
        
        for client in self.connected_clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            await self.unregister_client(client)
        
        if len(self.connected_clients) > 0:
            logger.debug(f"📡 Broadcasted {sensor_reading.sensor_id} data to {len(self.connected_clients)} clients")
    
    async def handle_client_message(self, websocket, message: str):
        """
        Handle incoming messages from clients
        
        Args:
            websocket: Client WebSocket connection
            message: JSON message string
        """
        try:
            data = json.loads(message)
            command = data.get('command')
            
            logger.debug(f"📨 Received command: {command}")
            
            if command == 'get_sensors':
                await self._send_sensor_list(websocket)
                
            elif command == 'get_history':
                sensor_id = data.get('sensor_id')
                limit = data.get('limit', 50)
                
                if sensor_id in self.sensors:
                    history = self.data_processor.get_sensor_history(sensor_id, limit)
                    response = {
                        'type': 'sensor_history',
                        'sensor_id': sensor_id,
                        'history': history,
                        'total_readings': len(history)
                    }
                    await websocket.send(json.dumps(response))
                else:
                    logger.warning(f"History requested for unknown sensor: {sensor_id}")
                    
            elif command == 'get_statistics':
                sensor_id = data.get('sensor_id')
                
                if sensor_id:
                    # Statistics for specific sensor
                    stats = self.data_processor.get_sensor_statistics(sensor_id)
                else:
                    # Statistics for all sensors
                    stats = self.data_processor.get_all_sensor_stats()
                
                response = {
                    'type': 'statistics',
                    'sensor_id': sensor_id,
                    'statistics': stats
                }
                await websocket.send(json.dumps(response))
                
            elif command == 'toggle_sensor':
                sensor_id = data.get('sensor_id')
                
                if sensor_id in self.sensors:
                    sensor = self.sensors[sensor_id]
                    sensor.is_active = not sensor.is_active
                    status = 'activated' if sensor.is_active else 'deactivated'
                    logger.info(f"🔧 Sensor {sensor_id} {status}")
                    
                    # Broadcast updated sensor list to all clients
                    await self._broadcast_sensor_list()
                else:
                    logger.warning(f"Toggle requested for unknown sensor: {sensor_id}")
                    
            elif command == 'get_system_info':
                system_info = self.data_processor.get_system_info()
                system_info.update({
                    'server_uptime': datetime.now().isoformat(),
                    'connected_clients': len(self.connected_clients),
                    'total_client_connections': self.client_count
                })
                
                response = {
                    'type': 'system_info',
                    'info': system_info
                }
                await websocket.send(json.dumps(response))
                
            elif command == 'get_alerts':
                minutes = data.get('minutes', 60)
                active_only = data.get('active_only', False)
                
                alerts = self.data_processor.get_alerts(
                    active_only=active_only,
                    minutes=minutes
                )
                
                response = {
                    'type': 'alerts',
                    'alerts': [alert.to_dict() for alert in alerts],
                    'count': len(alerts)
                }
                await websocket.send(json.dumps(response))
                
            else:
                logger.warning(f"Unknown command received: {command}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received from client: {e}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            import traceback
            traceback.print_exc()
    
    async def _broadcast_sensor_list(self):
        """Broadcast sensor list to all connected clients"""
        if not self.connected_clients:
            return
            
        for client in list(self.connected_clients):
            await self._send_sensor_list(client)
    
    async def sensor_data_loop(self):
        """
        Main loop for generating and broadcasting sensor data
        """
        logger.info("🔄 Starting sensor data generation loop")
        
        while self.is_running:
            try:
                # Generate data from all active sensors
                for sensor in self.sensors.values():
                    if sensor.is_active:
                        sensor_reading = sensor.read()
                        await self.broadcast_sensor_data(sensor_reading)
                
                # Wait before next reading cycle
                await asyncio.sleep(SERVER_CONFIG['sensor_read_interval'])
                
            except Exception as e:
                logger.error(f"Error in sensor data loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def handle_client_connection(self, websocket, path=None):
        """
        Handle individual client connections
        
        Args:
            websocket: WebSocket connection
            path: Connection path (optional, for compatibility)
        """
        await self.register_client(websocket, path)
        
        try:
            # Listen for messages from this client
            async for message in websocket:
                await self.handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.debug("Client connection closed normally")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def start(self):
        """
        Start the WebSocket server and sensor data generation
        """
        self.is_running = True
        
        try:
            # Start the WebSocket server
            logger.info(f"🚀 Starting WebSocket server on {self.host}:{self.port}")
            
            self.server = await websockets.serve(
                self.handle_client_connection,
                self.host,
                self.port,
                max_size=2**20,  # 1MB max message size
                max_queue=32,    # Max queued messages per client
                compression=None # Disable compression for simplicity
            )
            
            logger.info(f"✅ WebSocket server listening on ws://{self.host}:{self.port}")
            
            # Start the sensor data generation loop
            sensor_task = asyncio.create_task(self.sensor_data_loop())
            
            try:
                # Keep the server running
                await self.server.wait_closed()
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown signal received")
            finally:
                # Cleanup
                self.is_running = False
                sensor_task.cancel()
                
                try:
                    await sensor_task
                except asyncio.CancelledError:
                    pass
                
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
                
                logger.info("✅ Server shutdown complete")
                
        except Exception as e:
            logger.error(f"❌ Server startup failed: {e}")
            raise
    
    async def stop(self):
        """Stop the WebSocket server"""
        logger.info("🛑 Stopping WebSocket server...")
        self.is_running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("✅ WebSocket server stopped")

# Example usage and testing
if __name__ == "__main__":
    async def main():
        server = WebSocketServer()
        await server.start()
    
    print("🌐 WebSocket IoT Simulator Server")
    print("=" * 40)
    print(f"📡 Starting server on ws://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    print("🔧 Press Ctrl+C to stop")
    print("-" * 40)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")