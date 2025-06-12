"""
Real-time Matplotlib Visualization
"""

import asyncio
import websockets
import json
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for better compatibility
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
from collections import deque, defaultdict
import threading
import queue
import numpy as np
import time

# Configure matplotlib for better compatibility
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

class RealTimeGraphClient:
    """
    Real-time graphing client for sensor data visualization
    """
    
    def __init__(self, server_url="ws://localhost:8765", max_points=50):
        """
        Initialize the graphing client
        
        Args:
            server_url: WebSocket server URL
            max_points: Maximum data points to display per sensor
        """
        self.server_url = server_url
        self.max_points = max_points
        
        # Thread-safe data storage
        self.data_queue = queue.Queue()
        self.sensor_data = {
            'temperature': {'timestamps': deque(maxlen=max_points), 'values': deque(maxlen=max_points)},
            'humidity': {'timestamps': deque(maxlen=max_points), 'values': deque(maxlen=max_points)},
            'motion': {'timestamps': deque(maxlen=max_points), 'values': deque(maxlen=max_points)}
        }
        
        # WebSocket connection state
        self.websocket = None
        self.is_running = False
        self.connected = False
        
        # Colors for different sensors
        self.colors = {
            'temperature': '#ff6b6b',  # Red
            'humidity': '#4ecdc4',     # Teal
            'motion': '#45b7d1'        # Blue
        }
        
        # Setup matplotlib
        self._setup_plots()
        self.animation = None
    
    def _setup_plots(self):
        """Initialize the matplotlib plot layout"""
        try:
            # Create figure and subplots
            self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
            self.fig.suptitle('IoT Sensor Data - Real-time Monitoring', fontsize=14, fontweight='bold')
            
            # Flatten axes for easier access
            self.axes = self.axes.flatten()
            
            # Configure each subplot
            titles = ['Temperature (°C)', 'Humidity (%)', 'Motion Detection', 'All Sensors']
            ylabels = ['Temperature', 'Humidity', 'Motion', 'Normalized Values']
            
            for i, (ax, title, ylabel) in enumerate(zip(self.axes, titles, ylabels)):
                ax.set_title(title, fontweight='bold', fontsize=10)
                ax.set_ylabel(ylabel, fontsize=9)
                ax.set_xlabel('Time', fontsize=9)
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='both', which='major', labelsize=8)
            
            # Set specific limits for motion sensor
            self.axes[2].set_ylim(-0.1, 1.1)
            
            plt.tight_layout()
            
        except Exception as e:
            print(f"Error setting up plots: {e}")
            raise
    
    async def connect_websocket(self):
        """Connect to WebSocket server"""
        try:
            print(f"Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)
            self.is_running = True
            self.connected = True
            print("Connected to IoT server!")
            
            # Request sensor list
            command = {'command': 'get_sensors', 'timestamp': datetime.now().isoformat()}
            await self.websocket.send(json.dumps(command))
            
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            raise
    
    async def listen_for_data(self):
        """Listen for sensor data from WebSocket"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('type') == 'sensor_data':
                        sensor_data = data.get('data', {})
                        if sensor_data.get('status') == 'active':
                            # Put data in queue for GUI thread
                            self.data_queue.put(sensor_data)
                            
                    elif data.get('type') == 'sensor_list':
                        sensors = data.get('sensors', [])
                        print(f"Found {len(sensors)} sensors")
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue
                    
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            self.is_running = False
            self.connected = False
        except Exception as e:
            print(f"Error receiving data: {e}")
            self.is_running = False
            self.connected = False
    
    def process_data_queue(self):
        """Process incoming data from queue (called by animation)"""
        processed_count = 0
        max_process = 10  # Limit processing per frame
        
        while not self.data_queue.empty() and processed_count < max_process:
            try:
                sensor_data = self.data_queue.get_nowait()
                sensor_id = sensor_data.get('sensor_id', '')
                
                # Map sensor IDs to our data structure
                if 'temperature' in sensor_id.lower():
                    key = 'temperature'
                elif 'humidity' in sensor_id.lower():
                    key = 'humidity'
                elif 'motion' in sensor_id.lower():
                    key = 'motion'
                else:
                    continue
                
                try:
                    value = float(sensor_data.get('value', 0))
                    timestamp = datetime.now()
                    
                    # Store data
                    self.sensor_data[key]['timestamps'].append(timestamp)
                    self.sensor_data[key]['values'].append(value)
                    
                    processed_count += 1
                    
                except (ValueError, TypeError):
                    continue
                
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error processing data: {e}")
                break
    
    def update_plots(self, frame):
        """Update plots with new data (animation callback)"""
        if not self.is_running:
            return
        
        try:
            # Process new data
            self.process_data_queue()
            
            # Clear all plots
            for ax in self.axes:
                ax.clear()
            
            # Reconfigure plots
            titles = ['Temperature (°C)', 'Humidity (%)', 'Motion Detection', 'All Sensors']
            ylabels = ['Temperature', 'Humidity', 'Motion', 'Normalized']
            
            for i, (ax, title, ylabel) in enumerate(zip(self.axes, titles, ylabels)):
                ax.set_title(title, fontweight='bold', fontsize=10)
                ax.set_ylabel(ylabel, fontsize=9)
                ax.set_xlabel('Time', fontsize=9)
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='both', which='major', labelsize=8)
            
            # Plot individual sensors
            sensor_keys = ['temperature', 'humidity', 'motion']
            overview_data = {}
            
            for i, key in enumerate(sensor_keys):
                ax = self.axes[i]
                data = self.sensor_data[key]
                
                if len(data['timestamps']) > 0 and len(data['values']) > 0:
                    timestamps = list(data['timestamps'])
                    values = list(data['values'])
                    color = self.colors.get(key, '#333333')
                    x_positions = range(len(values))
                    
                    if key == 'motion':
                        # Bar chart for motion
                        bars = ax.bar(x_positions, values, color=color, alpha=0.7)
                        ax.set_ylim(-0.1, 1.1)
                        ax.set_ylabel('Motion (0/1)')
                        
                        # Add value labels on bars
                        for j, (bar, value) in enumerate(zip(bars, values)):
                            if value > 0:  # Only show labels for motion detected
                                ax.text(bar.get_x() + bar.get_width()/2, value + 0.05,
                                       f'{value:.0f}', ha='center', va='bottom',
                                       fontsize=8, fontweight='bold', color=color)
                    else:
                        # Line chart for continuous data
                        line = ax.plot(x_positions, values, color=color, linewidth=2, 
                                      marker='o', markersize=4, markerfacecolor=color,
                                      markeredgecolor='white', markeredgewidth=1)
                        
                        # Add value labels on points (show every 3rd point to avoid clutter)
                        for j in range(0, len(values), max(1, len(values)//5)):  # Show ~5 labels max
                            value = values[j]
                            x_pos = x_positions[j]
                            
                            # Position label above or below point based on trend
                            y_offset = 0.02 * (max(values) - min(values)) if len(values) > 1 else 0.5
                            label_y = value + y_offset
                            
                            ax.annotate(f'{value:.1f}', 
                                       xy=(x_pos, value),
                                       xytext=(x_pos, label_y),
                                       ha='center', va='bottom',
                                       fontsize=8, fontweight='bold',
                                       bbox=dict(boxstyle='round,pad=0.2', 
                                               facecolor=color, alpha=0.8, 
                                               edgecolor='white'),
                                       color='white')
                        
                        # Highlight latest point with larger marker and value
                        if len(values) > 0:
                            latest_x = x_positions[-1]
                            latest_y = values[-1]
                            
                            # Large marker for latest point
                            ax.plot(latest_x, latest_y, marker='o', markersize=8, 
                                   markerfacecolor='yellow', markeredgecolor=color, 
                                   markeredgewidth=2, zorder=10)
                            
                            # Latest value label with special styling
                            ax.annotate(f'Latest\n{latest_y:.1f}', 
                                       xy=(latest_x, latest_y),
                                       xytext=(10, 20), textcoords='offset points',
                                       ha='left', va='bottom',
                                       fontsize=9, fontweight='bold',
                                       bbox=dict(boxstyle='round,pad=0.3', 
                                               facecolor='yellow', alpha=0.9, 
                                               edgecolor=color, linewidth=2),
                                       arrowprops=dict(arrowstyle='->', 
                                                     connectionstyle='arc3,rad=0.1',
                                                     color=color, lw=1.5))
                    
                    # Store for overview
                    if len(values) > 0:
                        overview_data[key] = {
                            'values': values,
                            'color': color,
                            'name': key.title()
                        }
                        
                        # Statistics display in corner
                        if len(values) > 1:
                            avg_val = sum(values) / len(values)
                            min_val = min(values)
                            max_val = max(values)
                            stats_text = f'Avg: {avg_val:.1f}\nMin: {min_val:.1f}\nMax: {max_val:.1f}'
                        else:
                            stats_text = f'Value: {values[0]:.1f}'
                        
                        ax.text(0.02, 0.98, stats_text, 
                               transform=ax.transAxes, fontsize=8,
                               verticalalignment='top', ha='left',
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor='white', alpha=0.8, 
                                       edgecolor=color, linewidth=1))
            
            # Overview plot (normalized)
            overview_ax = self.axes[3]
            overview_ax.set_title('All Sensors (Normalized)', fontweight='bold', fontsize=10)
            overview_ax.set_ylabel('Normalized (0-1)', fontsize=9)
            overview_ax.set_xlabel('Time', fontsize=9)
            overview_ax.grid(True, alpha=0.3)
            
            for key, data in overview_data.items():
                if len(data['values']) > 1:
                    values = np.array(data['values'])
                    # Normalize to 0-1
                    if values.max() != values.min():
                        normalized = (values - values.min()) / (values.max() - values.min())
                    else:
                        normalized = np.zeros_like(values)
                    
                    x_positions = range(len(normalized))
                    line = overview_ax.plot(x_positions, normalized, 
                                          color=data['color'], linewidth=2, 
                                          label=data['name'], alpha=0.8,
                                          marker='o', markersize=3)
                    
                    # Add latest value marker for overview
                    if len(normalized) > 0:
                        latest_x = x_positions[-1]
                        latest_y = normalized[-1]
                        overview_ax.plot(latest_x, latest_y, marker='s', markersize=6, 
                                       markerfacecolor=data['color'], markeredgecolor='white', 
                                       markeredgewidth=1, zorder=10)
            
            if overview_data:
                overview_ax.legend(loc='upper right', fontsize=8)
                overview_ax.set_ylim(-0.1, 1.1)
            
            # Timestamp only
            current_time = datetime.now().strftime('%H:%M:%S')
            self.fig.text(0.98, 0.02, f"Updated: {current_time}", 
                         fontsize=8, color='gray', ha='right')
            
            plt.tight_layout()
            
        except Exception as e:
            print(f"Error updating plots: {e}")

    
    def start_websocket_thread(self):
        """Start WebSocket connection in separate thread"""
        def websocket_worker():
            """WebSocket worker function"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def run():
                    try:
                        await self.connect_websocket()
                        await self.listen_for_data()
                    except Exception as e:
                        print(f"WebSocket error: {e}")
                    finally:
                        self.is_running = False
                        self.connected = False
                
                loop.run_until_complete(run())
                
            except Exception as e:
                print(f"WebSocket thread error: {e}")
                self.is_running = False
                self.connected = False
        
        websocket_thread = threading.Thread(target=websocket_worker, daemon=True)
        websocket_thread.start()
        return websocket_thread
    
    def run(self):
        """Start the real-time graphing client"""
        print("Starting Real-time IoT Data Visualization")
        print("Close the plot window to stop")
        print("-" * 50)
        
        try:
            # Start WebSocket in background thread
            websocket_thread = self.start_websocket_thread()
            
            # Give WebSocket time to connect
            time.sleep(1)
            
            # Start animation with longer interval for stability
            self.animation = animation.FuncAnimation(
                self.fig, self.update_plots, interval=1000, blit=False, cache_frame_data=False
            )
            
            # Show plot
            plt.show()
            
        except KeyboardInterrupt:
            print("Visualization stopped by user")
        except Exception as e:
            print(f"Visualization error: {e}")
        finally:
            self.is_running = False
            self.connected = False
            try:
                plt.close('all')
            except:
                pass

def main():
    """Main function to start visualization"""
    try:
        client = RealTimeGraphClient()
        client.run()
        
    except ImportError as e:
        print("Required libraries missing:")
        print("Install them with: pip install matplotlib numpy")
        print(f"Error: {e}")
    except Exception as e:
        print(f"Visualization error: {e}")

if __name__ == "__main__":
    main()