"""Container output streaming and file synchronization."""
import os
import time
import asyncio
import hashlib
import collections
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator, Any
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..utils.logging import setup_logging
from ..utils.errors import StreamError, SyncError

logger = setup_logging(__name__)

class OutputFormat(str, Enum):
    """Output stream formats."""
    STDOUT = "stdout"
    STDERR = "stderr"
    COMBINED = "combined"
    FORMATTED = "formatted"

class StreamConfig:
    """Stream configuration."""
    def __init__(
        self,
        format: OutputFormat = OutputFormat.COMBINED,
        buffer_size: int = 1024,
        filters: Optional[List[str]] = None,
        timestamp: bool = False
    ):
        self.format = format
        self.buffer_size = buffer_size
        self.filters = filters or []
        self.timestamp = timestamp

class SyncConfig:
    """Synchronization configuration."""
    def __init__(
        self,
        ignore_patterns: Optional[List[str]] = None,
        sync_interval: float = 1.0,
        atomic: bool = True
    ):
        self.ignore_patterns = ignore_patterns or []
        self.sync_interval = sync_interval
        self.atomic = atomic

class StreamInfo:
    """Information about an active stream."""
    def __init__(self, task: asyncio.Task, config: StreamConfig):
        self.task = task
        self.config = config
        self.start_time = datetime.now()

class EnhancedOutputStreamManager:
    """Enhanced streaming output manager."""
    
    def __init__(self, docker_manager):
        self.docker_manager = docker_manager
        self.active_streams: Dict[str, StreamInfo] = {}
        self._buffer = collections.deque(maxlen=1000)  # Keep last 1000 messages
        
    async def start_stream(
        self,
        container_name: str,
        command: str,
        config: StreamConfig,
        callback: Optional[callable] = None
    ) -> AsyncGenerator[str, None]:
        """Start enhanced output stream."""
        try:
            container = self.docker_manager.containers.get(container_name)
            if not container:
                raise StreamError(f"Container not found: {container_name}")

            # Create execution with specified format
            exec_result = container.exec_run(
                command,
                stream=True,
                demux=True,
                socket=True  # Use socket for better streaming
            )

            async def stream_handler():
                buffer = []
                try:
                    async for data in exec_result.output:
                        # Apply format and filtering
                        processed_data = self._process_stream_data(data, config)
                        
                        if processed_data:
                            buffer.extend(processed_data)
                            if len(buffer) >= config.buffer_size:
                                output = ''.join(buffer)
                                buffer.clear()
                                
                                self._buffer.append(output)
                                
                                if callback:
                                    await callback(output)
                                yield output
                except Exception as e:
                    logger.error(f"Stream processing error: {str(e)}")
                    raise StreamError(f"Stream processing error: {str(e)}")
                finally:
                    if buffer:
                        output = ''.join(buffer)
                        self._buffer.append(output)
                        if callback:
                            await callback(output)
                        yield output

                    if container_name in self.active_streams:
                        del self.active_streams[container_name]

            # Create and store stream task
            stream_task = asyncio.create_task(stream_handler())
            self.active_streams[container_name] = StreamInfo(stream_task, config)
            
            async for output in stream_task:
                yield output

        except Exception as e:
            logger.error(f"Failed to start stream: {str(e)}")
            raise StreamError(f"Failed to start stream: {str(e)}")

    def _process_stream_data(
        self,
        data: bytes,
        config: StreamConfig
    ) -> Optional[str]:
        """Process stream data according to config."""
        if not data:
            return None
            
        # Split streams if demuxed
        stdout, stderr = data if isinstance(data, tuple) else (data, None)
        
        # Apply format
        if config.format == OutputFormat.STDOUT and stdout:
            output = stdout.decode()
        elif config.format == OutputFormat.STDERR and stderr:
            output = stderr.decode()
        elif config.format == OutputFormat.COMBINED:
            output = ''
            if stdout:
                output += stdout.decode()
            if stderr:
                output += stderr.decode()
        elif config.format == OutputFormat.FORMATTED:
            output = self._format_output(stdout, stderr)
        else:
            return None
            
        # Apply filters
        for filter_pattern in config.filters:
            if filter_pattern in output:
                return None
                
        # Add timestamp if requested
        if config.timestamp:
            output = f"[{datetime.now().isoformat()}] {output}"
            
        return output
        
    @staticmethod
    def _format_output(stdout: Optional[bytes], stderr: Optional[bytes]) -> str:
        """Format output with colors and prefixes."""
        output = []
        
        if stdout:
            output.append(f"\033[32m[OUT]\033[0m {stdout.decode()}")
        if stderr:
            output.append(f"\033[31m[ERR]\033[0m {stderr.decode()}")
            
        return '\n'.join(output)

    async def stop_stream(self, container_name: str) -> None:
        """Stop streaming from a container."""
        if stream_info := self.active_streams.get(container_name):
            stream_info.task.cancel()
            try:
                await stream_info.task
            except asyncio.CancelledError:
                pass
            del self.active_streams[container_name]

class BiDirectionalSync:
    """Enhanced bi-directional file synchronization."""
    
    def __init__(self, docker_manager):
        self.docker_manager = docker_manager
        self.sync_handlers: Dict[str, EnhancedSyncHandler] = {}
        self.observer = Observer()
        self.observer.start()
        
    async def start_sync(
        self,
        container_name: str,
        host_path: str,
        container_path: str,
        config: SyncConfig
    ) -> None:
        """Start bi-directional file sync."""
        try:
            # Validate paths
            if not os.path.exists(host_path):
                raise SyncError(f"Host path does not exist: {host_path}")
            
            container = self.docker_manager.containers.get(container_name)
            if not container:
                raise SyncError(f"Container not found: {container_name}")
            
            # Create sync handler
            handler = EnhancedSyncHandler(
                container=container,
                container_path=container_path,
                host_path=host_path,
                config=config
            )
            
            # Start watching both directions
            self.observer.schedule(
                handler,
                host_path,
                recursive=True
            )
            
            # Start container file watcher
            await handler.start_container_watcher()
            
            self.sync_handlers[container_name] = handler
            logger.info(f"Started bi-directional sync for container: {container_name}")
            
        except Exception as e:
            raise SyncError(f"Failed to start sync: {str(e)}")

    async def stop_sync(self, container_name: str) -> None:
        """Stop synchronization for a container."""
        if handler := self.sync_handlers.get(container_name):
            self.observer.unschedule_all()
            await handler.stop_container_watcher()
            del self.sync_handlers[container_name]
            logger.info(f"Stopped sync for container: {container_name}")

    async def cleanup(self) -> None:
        """Clean up all synchronization handlers."""
        for container_name in list(self.sync_handlers.keys()):
            await self.stop_sync(container_name)
        self.observer.stop()
        self.observer.join()

class EnhancedSyncHandler(FileSystemEventHandler):
    """Enhanced sync handler with bi-directional support."""
    
    def __init__(
        self,
        container,
        container_path: str,
        host_path: str,
        config: SyncConfig
    ):
        super().__init__()
        self.container = container
        self.container_path = container_path
        self.host_path = host_path
        self.config = config
        self.sync_lock = asyncio.Lock()
        self.pending_syncs: Dict[str, float] = {}
        self._container_watcher: Optional[asyncio.Task] = None
        
    async def start_container_watcher(self) -> None:
        """Start watching container files."""
        cmd = f"""
        inotifywait -m -r -e modify,create,delete,move {self.container_path}
        """
        
        exec_result = self.container.exec_run(
            cmd,
            stream=True,
            detach=True
        )
        
        self._container_watcher = asyncio.create_task(
            self._handle_container_events(exec_result.output)
        )
        
    async def stop_container_watcher(self) -> None:
        """Stop container file watcher."""
        if self._container_watcher:
            self._container_watcher.cancel()
            try:
                await self._container_watcher
            except asyncio.CancelledError:
                pass
            self._container_watcher = None
        
    async def _handle_container_events(self, output_stream: AsyncGenerator) -> None:
        """Handle container file events."""
        try:
            async for event in output_stream:
                await self._handle_container_change(event.decode())
        except Exception as e:
            logger.error(f"Container watcher error: {str(e)}")
            
    async def _handle_container_change(self, event: str) -> None:
        """Handle container file change."""
        try:
            # Parse inotify event
            parts = event.strip().split()
            if len(parts) >= 3:
                path = parts[0]
                change_type = parts[1]
                filename = parts[2]
                
                container_path = os.path.join(path, filename)
                host_path = self._container_to_host_path(container_path)
                
                # Apply filters
                if self._should_ignore(host_path):
                    return
                    
                async with self.sync_lock:
                    # Check if change is from host sync
                    if host_path in self.pending_syncs:
                        if time.time() - self.pending_syncs[host_path] < self.config.sync_interval:
                            return
                            
                    # Sync from container to host
                    await self._sync_to_host(container_path, host_path)
                    
        except Exception as e:
            logger.error(f"Error handling container change: {str(e)}")
            
    def _container_to_host_path(self, container_path: str) -> str:
        """Convert container path to host path."""
        rel_path = os.path.relpath(container_path, self.container_path)
        return os.path.join(self.host_path, rel_path)

    def _should_ignore(self, path: str) -> bool:
        """Check if path should be ignored."""
        return any(pattern in path for pattern in self.config.ignore_patterns)
        
    async def _sync_to_host(
        self,
        container_path: str,
        host_path: str
    ) -> None:
        """Sync file from container to host."""
        try:
            # Get file from container
            stream, stat = self.container.get_archive(container_path)
            
            # Create parent directories
            os.makedirs(os.path.dirname(host_path), exist_ok=True)
            
            if self.config.atomic:
                # Save file atomically using temporary file
                tmp_path = f"{host_path}.tmp"
                with open(tmp_path, 'wb') as f:
                    for chunk in stream:
                        f.write(chunk)
                os.rename(tmp_path, host_path)
            else:
                # Direct write
                with open(host_path, 'wb') as f:
                    for chunk in stream:
                        f.write(chunk)
            
            # Update sync tracking
            self.pending_syncs[host_path] = time.time()
            
        except Exception as e:
            logger.error(f"Error syncing to host: {str(e)}")
            raise SyncError(f"Failed to sync file {container_path}: {str(e)}")