"""Development tools integration for environments."""
import shutil
import subprocess
from typing import Dict, Optional, Any
from pathlib import Path

from ..utils.logging import setup_logging
from ..utils.errors import ToolError

logger = setup_logging(__name__)

class ToolManager:
    """Manages development tools in environments."""
    
    def __init__(self, env_manager):
        self.env_manager = env_manager
        
    async def setup_package_manager(
        self,
        environment: str,
        package_manager: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Set up package manager in an environment."""
        try:
            config = config or {}
            
            if package_manager == "npm":
                return await self._setup_npm(environment, config)
            elif package_manager == "pip":
                return await self._setup_pip(environment, config)
            else:
                raise ToolError(f"Unsupported package manager: {package_manager}")
                
        except Exception as e:
            raise ToolError(f"Failed to setup package manager: {str(e)}")
            
    async def setup_build_tool(
        self,
        environment: str,
        build_tool: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Set up build tool in an environment."""
        try:
            config = config or {}
            
            if build_tool == "webpack":
                return await self._setup_webpack(environment, config)
            elif build_tool == "vite":
                return await self._setup_vite(environment, config)
            else:
                raise ToolError(f"Unsupported build tool: {build_tool}")
                
        except Exception as e:
            raise ToolError(f"Failed to setup build tool: {str(e)}")
            
    async def setup_test_framework(
        self,
        environment: str,
        test_framework: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Set up testing framework in an environment."""
        try:
            config = config or {}
            
            if test_framework == "jest":
                return await self._setup_jest(environment, config)
            elif test_framework == "pytest":
                return await self._setup_pytest(environment, config)
            else:
                raise ToolError(f"Unsupported test framework: {test_framework}")
                
        except Exception as e:
            raise ToolError(f"Failed to setup test framework: {str(e)}")
            
    async def _setup_npm(self, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up NPM package manager."""
        try:
            # Initialize package.json if needed
            if not config.get('skip_init'):
                result = await self.env_manager.execute_in_environment(
                    environment,
                    'npm init -y'
                )
                if result['exit_code'] != 0:
                    raise ToolError(f"npm init failed: {result['error']}")
            
            # Install dependencies if specified
            if deps := config.get('dependencies'):
                deps_str = ' '.join(deps)
                result = await self.env_manager.execute_in_environment(
                    environment,
                    f'npm install {deps_str}'
                )
                if result['exit_code'] != 0:
                    raise ToolError(f"npm install failed: {result['error']}")
                    
            return {"status": "success"}
            
        except Exception as e:
            raise ToolError(f"NPM setup failed: {str(e)}")
            
    async def _setup_pip(self, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Pip package manager."""
        try:
            # Create virtual environment if needed
            if not config.get('skip_venv'):
                result = await self.env_manager.execute_in_environment(
                    environment,
                    'python -m venv .venv'
                )
                if result['exit_code'] != 0:
                    raise ToolError(f"venv creation failed: {result['error']}")
            
            # Install dependencies if specified
            if deps := config.get('dependencies'):
                deps_str = ' '.join(deps)
                result = await self.env_manager.execute_in_environment(
                    environment,
                    f'pip install {deps_str}'
                )
                if result['exit_code'] != 0:
                    raise ToolError(f"pip install failed: {result['error']}")
                    
            return {"status": "success"}
            
        except Exception as e:
            raise ToolError(f"Pip setup failed: {str(e)}")
            
    async def _setup_webpack(self, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Webpack build tool."""
        try:
            # Install webpack and dependencies
            result = await self.env_manager.execute_in_environment(
                environment,
                'npm install webpack webpack-cli --save-dev'
            )
            if result['exit_code'] != 0:
                raise ToolError(f"webpack installation failed: {result['error']}")
                
            # Create webpack config if not exists
            config_content = """
            const path = require('path');
            
            module.exports = {
              entry: './src/index.js',
              output: {
                path: path.resolve(__dirname, 'dist'),
                filename: 'bundle.js'
              }
            };
            """
            
            config_path = Path(self.env_manager.environments[environment]['path']) / 'webpack.config.js'
            config_path.write_text(config_content)
            
            return {"status": "success"}
            
        except Exception as e:
            raise ToolError(f"Webpack setup failed: {str(e)}")
            
    async def _setup_vite(self, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Vite build tool."""
        try:
            # Install vite
            result = await self.env_manager.execute_in_environment(
                environment,
                'npm install vite --save-dev'
            )
            if result['exit_code'] != 0:
                raise ToolError(f"vite installation failed: {result['error']}")
                
            # Create vite config if not exists
            config_content = """
            export default {
              root: 'src',
              build: {
                outDir: '../dist'
              }
            }
            """
            
            config_path = Path(self.env_manager.environments[environment]['path']) / 'vite.config.js'
            config_path.write_text(config_content)
            
            return {"status": "success"}
            
        except Exception as e:
            raise ToolError(f"Vite setup failed: {str(e)}")
            
    async def _setup_jest(self, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Jest testing framework."""
        try:
            # Install jest and dependencies
            result = await self.env_manager.execute_in_environment(
                environment,
                'npm install jest @types/jest --save-dev'
            )
            if result['exit_code'] != 0:
                raise ToolError(f"jest installation failed: {result['error']}")
                
            # Create jest config if not exists
            config_content = """
            module.exports = {
              testEnvironment: 'node',
              testMatch: ['**/*.test.js'],
              collectCoverage: true
            };
            """
            
            config_path = Path(self.env_manager.environments[environment]['path']) / 'jest.config.js'
            config_path.write_text(config_content)
            
            return {"status": "success"}
            
        except Exception as e:
            raise ToolError(f"Jest setup failed: {str(e)}")
            
    async def _setup_pytest(self, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Pytest testing framework."""
        try:
            # Install pytest and dependencies
            result = await self.env_manager.execute_in_environment(
                environment,
                'pip install pytest pytest-cov'
            )
            if result['exit_code'] != 0:
                raise ToolError(f"pytest installation failed: {result['error']}")
                
            # Create pytest config if not exists
            config_content = """
            [pytest]
            testpaths = tests
            python_files = test_*.py
            addopts = --cov=src
            """
            
            config_path = Path(self.env_manager.environments[environment]['path']) / 'pytest.ini'
            config_path.write_text(config_content)
            
            return {"status": "success"}
            
        except Exception as e:
            raise ToolError(f"Pytest setup failed: {str(e)}")
