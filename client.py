#!/usr/bin/env python3
# File: banking-assistant/client.py

import asyncio
import sys
from src.interfaces.terminal_interface import TerminalInterface

async def main():
    """Main entry point for the client application"""
    # Get custom server URL if provided
    server_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print(f"Connecting to server at {server_url}")
    interface = TerminalInterface(base_url=server_url)
    await interface.run()

if __name__ == "__main__":
    asyncio.run(main())
