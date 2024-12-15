import asyncio
import json
import websockets
from typing import Callable, Any, Dict, Optional
import logging
import traceback

logger = logging.getLogger(__name__)

class Server:
    """Core server class implementing JSON-RPC 2.0 protocol."""
    
    def __init__(self, name: str):
        """Initialize the server.
        
        Args:
            name: Server name
        """
        self.name = name
        self.websocket = None
        self.input_request_handlers = {}
        self.input_response_handlers = {}
        self.initialized = False
        self.capabilities = {}
        
    async def start(self, host: str = "localhost", port: int = 8000):
        """Start the WebSocket server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
        """
        async def handler(websocket, path):
            self.websocket = websocket
            try:
                logger.info(f"New WebSocket connection from {websocket.remote_address}")
                async for message in websocket:
                    response = None
                    try:
                        # Parse JSON-RPC message
                        data = json.loads(message)
                        if not isinstance(data, dict):
                            raise ValueError("Invalid JSON-RPC message")
                            
                        # Handle message
                        response = await self.handle_jsonrpc(data)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {str(e)}")
                        response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32700,
                                "message": "Parse error",
                                "data": str(e)
                            },
                            "id": None
                        }
                        
                    except Exception as e:
                        logger.error(f"Error handling message: {str(e)}", exc_info=True)
                        response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32603,
                                "message": "Internal error",
                                "data": {
                                    "error": str(e),
                                    "traceback": traceback.format_exc()
                                }
                            },
                            "id": getattr(data, "id", None) if isinstance(data, dict) else None
                        }

                    # Ensure we always send a properly formatted JSON-RPC response
                    if response:
                        try:
                            if not isinstance(response, dict):
                                response = {"result": response}
                            
                            response["jsonrpc"] = "2.0"
                            if isinstance(data, dict) and "id" in data:
                                response["id"] = data["id"]
                                
                            # Validate JSON before sending
                            response_str = json.dumps(response)
                            await websocket.send(response_str)
                            
                        except Exception as e:
                            logger.error(f"Error sending response: {str(e)}", exc_info=True)
                            error_response = {
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": -32603,
                                    "message": "Error sending response",
                                    "data": str(e)
                                },
                                "id": data.get("id") if isinstance(data, dict) else None
                            }
                            await websocket.send(json.dumps(error_response))
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
            finally:
                self.websocket = None
                
        try:
            self.server = await websockets.serve(
                handler,
                host,
                port,
                ping_interval=20,
                ping_timeout=20
            )
            logger.info(f"Server started on ws://{host}:{port}")
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}", exc_info=True)
            raise
        
    async def handle_jsonrpc(self, data: Dict) -> Optional[Dict]:
        """Handle JSON-RPC message.
        
        Args:
            data: Parsed JSON-RPC message
            
        Returns:
            Optional response message
        """
        try:
            method = data.get("method")
            params = data.get("params", {})
            
            logger.info(f"Handling method: {method} with params: {params}")
            
            if method == "initialize":
                self.capabilities = params.get("capabilities", {})
                self.initialized = True
                return {
                    "result": {
                        "capabilities": self.capabilities
                    }
                }
                
            if not self.initialized:
                return {
                    "error": {
                        "code": -32002,
                        "message": "Server not initialized"
                    }
                }
                
            if method == "input/request":
                handler = self.input_request_handlers.get("input_request")
                if handler:
                    try:
                        result = await handler(
                            params.get("type", ""),
                            params.get("context", {})
                        )
                        return {"result": result}
                    except Exception as e:
                        logger.error(f"Error in input request handler: {str(e)}", exc_info=True)
                        return {
                            "error": {
                                "code": -32000,
                                "message": str(e),
                                "data": {
                                    "traceback": traceback.format_exc()
                                }
                            }
                        }
                        
            elif method == "input/response":
                handler = self.input_response_handlers.get("input_response")
                if handler:
                    try:
                        await handler(params)
                        return {"result": None}
                    except Exception as e:
                        logger.error(f"Error in input response handler: {str(e)}", exc_info=True)
                        return {
                            "error": {
                                "code": -32000,
                                "message": str(e),
                                "data": {
                                    "traceback": traceback.format_exc()
                                }
                            }
                        }
                        
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in handle_jsonrpc: {str(e)}", exc_info=True)
            return {
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                }
            }
                
    def request_input(self) -> Callable:
        """Decorator for input request handlers."""
        def decorator(func: Callable) -> Callable:
            self.input_request_handlers["input_request"] = func
            return func
        return decorator
        
    def handle_input(self) -> Callable:
        """Decorator for input response handlers."""
        def decorator(func: Callable) -> Callable:
            self.input_response_handlers["input_response"] = func
            return func
        return decorator