"""
Simple WebSocket Client
"""

import asyncio
import websockets
import json
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)

async def handle_message(message):
    """
    Handle incoming sensor data messages
    
    Args:
        message: JSON message from server
    """
    try:
        data = json.loads(message)
        msg_type = data.get('type')
        
        if msg_type == 'sensor_data':
            sensor_data = data.get('data', {})
            if sensor_data.get('status') == 'active':
                timestamp = datetime.now().strftime('%H:%M:%S')
                name = sensor_data.get('name', 'Unknown')
                value = sensor_data.get('value')
                unit = sensor_data.get('unit', '')
                location = sensor_data.get('location', '')
                
                print(f"[{timestamp}] {name}: {value} {unit}")
                
                # Simple alerts
                sensor_type = sensor_data.get('sensor_type')
                try:
                    numeric_value = float(value) if value is not None else 0
                    
                    if sensor_type == 'TemperatureSensor':
                        if numeric_value > 25:
                            print(f"  >> HIGH TEMPERATURE ALERT: {value}°C in {location}!")
                        elif numeric_value < 18:
                            print(f"  >> LOW TEMPERATURE ALERT: {value}°C in {location}!")
                    elif sensor_type == 'HumiditySensor':
                        if numeric_value > 70:
                            print(f"  >> HIGH HUMIDITY ALERT: {value}% in {location}!")
                        elif numeric_value < 30:
                            print(f"  >> LOW HUMIDITY ALERT: {value}% in {location}!")
                    elif sensor_type == 'MotionSensor' and numeric_value == 1.0:
                        print(f"  >> MOTION DETECTED at {location}!")
                        
                except (ValueError, TypeError):
                    pass  # Skip non-numeric values
                    
        elif msg_type == 'sensor_list':
            sensors = data.get('sensors', [])
            server_info = data.get('server_info', {})
            
            print(f"\nConnected! Found {len(sensors)} sensors:")
            for sensor in sensors:
                status = "ACTIVE" if sensor['status'] == 'active' else "INACTIVE"
                print(f"  {sensor['name']} ({sensor['sensor_type']}) - {status}")
                print(f"    Location: {sensor['location']}")
            
            if server_info:
                print(f"\nServer: {server_info.get('connected_clients', 0)} clients connected")
            print("-" * 60)
            
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON message")
    except Exception as e:
        logger.error(f"Error handling message: {e}")

async def run_simple_client(uri: str = "ws://localhost:8765"):
    """
    Main simple client function
    
    Args:
        uri: WebSocket server URI
    """
    print("Simple WebSocket IoT Client")
    print("=" * 40)
    print("Connecting to IoT sensor simulator...")
    print("Press Ctrl+C to stop")
    print("-" * 40)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server!")
            
            # Send initial command
            command = {
                'command': 'get_sensors',
                'timestamp': datetime.now().isoformat()
            }
            await websocket.send(json.dumps(command))
            
            # Listen for messages
            message_count = 0
            try:
                async for message in websocket:
                    message_count += 1
                    await handle_message(message)
                    
                    # Show periodic status
                    if message_count % 20 == 0:
                        print(f"\n--- Received {message_count} messages ---")
                        
            except KeyboardInterrupt:
                print(f"\nFinal count: {message_count} messages received")
                
    except ConnectionRefusedError:
        print("Cannot connect to server!")
        print("Make sure the server is running: python main.py")
    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    """
    Simple WebSocket Client
    """
    
    try:
        asyncio.run(run_simple_client())
    except KeyboardInterrupt:
        print("\nClient stopped by user")
    except Exception as e:
        print(f"Error: {e}")