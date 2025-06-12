#!/usr/bin/env python3
"""
WebSocket IoT Simulator - Main Entry Point

Educational WebSocket application demonstrating:
- Real-time IoT sensor simulation
- WebSocket server/client architecture
- Data visualization and processing

Usage:
    python main.py

Interactive menu will guide you through the options.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger

logger = setup_logger(__name__)

def show_menu():
    """Display the main menu and get user choice"""
    print("\n" + "=" * 50)
    print("   WebSocket IoT Simulator")
    print("   Educational Application")
    print("=" * 50)
    print()
    print("Choose what you want to run:")
    print()
    print("  1. Start IoT Server")
    print("     (Simulates sensors and serves data)")
    print()
    print("  2. Start Text Client") 
    print("     (View sensor data in text format)")
    print()
    print("  3. Start Graphing Client")
    print("     (View real-time charts and graphs)")
    print()
    print("  4. Exit")
    print()
    print("-" * 50)
    
    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("Please enter 1, 2, 3, or 4")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception:
            print("Please enter a valid number (1-4)")

async def run_server():
    """Run the WebSocket server"""
    from websocket.websocket_app import WebSocketServer
    
    print("\n🌐 Starting WebSocket IoT Simulator Server...")
    print("📡 Server will listen on ws://localhost:8765")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        server = WebSocketServer(host='localhost', port=8765)
        await server.start()
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully")
    except Exception as e:
        print(f"❌ Server error: {e}")
        input("Press Enter to continue...")

async def run_text_client():
    """Run the simple text client"""
    from websocket.websocket_client import run_simple_client
    
    print("\n📱 Starting Text Client...")
    print("📡 Connecting to ws://localhost:8765")
    print("🔧 Press Ctrl+C to stop the client")
    print("-" * 50)
    
    try:
        await run_simple_client("ws://localhost:8765")
    except KeyboardInterrupt:
        print("\n👋 Client stopped by user")
    except ConnectionRefusedError:
        print("\n❌ Cannot connect to server!")
        print("Make sure the server is running first (option 1)")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"\n❌ Client error: {e}")
        input("Press Enter to continue...")

def run_graph_client():
    """Run the real-time graphing client"""
    try:
        from visualization.visualizer import RealTimeGraphClient
        
        print("\n📊 Starting Real-time Graphing Client...")
        print("📡 Connecting to ws://localhost:8765")
        print("🔧 Close the plot window to stop")
        print("-" * 50)
        
        client = RealTimeGraphClient(server_url="ws://localhost:8765")
        client.run()
        
    except ImportError:
        print("\n❌ Graphing libraries not installed!")
        print("Install them with: pip install matplotlib pandas numpy")
        input("Press Enter to continue...")
    except ConnectionRefusedError:
        print("\n❌ Cannot connect to server!")
        print("Make sure the server is running first (option 1)")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"\n❌ Graphing error: {e}")
        input("Press Enter to continue...")

def show_instructions():
    """Show helpful instructions"""
    print("\n💡 Quick Start Instructions:")
    print("-" * 30)
    print("1. First, start the server (option 1)")
    print("2. Then open another terminal/command prompt")
    print("3. Run 'python main.py' again")
    print("4. Choose option 2 (text) or 3 (graphs)")
    print()
    print("This way you can have the server and client")
    print("running at the same time!")
    print()

async def main():
    """Main application loop"""
    # Show welcome message
    print("Welcome to the WebSocket IoT Simulator!")
    show_instructions()
    
    while True:
        try:
            choice = show_menu()
            
            if choice == 1:
                # Start server
                await run_server()
                
            elif choice == 2:
                # Start text client
                await run_text_client()
                
            elif choice == 3:
                # Start graphing client
                run_graph_client()
                
            elif choice == 4:
                # Exit
                print("\n👋 Thank you for using the IoT Simulator!")
                print("Happy learning! 🎓")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Application terminated by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            input("Press Enter to continue...")

def main_entry():
    """Entry point that handles async setup"""
    try:
        # Check for special command line arguments (for advanced users)
        if len(sys.argv) > 1:
            arg = sys.argv[1].lower()
            if arg == '--server':
                asyncio.run(run_server())
                return
            elif arg == '--client':
                asyncio.run(run_text_client())
                return
            elif arg == '--graph':
                run_graph_client()
                return
            elif arg == '--help':
                print("WebSocket IoT Simulator")
                print("Usage: python main.py")
                print("       python main.py --server")
                print("       python main.py --client") 
                print("       python main.py --graph")
                return
        
        # Default: show interactive menu
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_entry()