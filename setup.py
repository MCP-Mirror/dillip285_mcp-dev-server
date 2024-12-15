from setuptools import setup, find_packages

setup(
    name="mcp-dev-server",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp",            # Base MCP package
        "aiohttp>=3.8.0",
        "websockets>=10.0",
        "uvicorn>=0.15.0",
        "fastapi>=0.68.0",
        "typing_extensions>=4.5.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-dev-server=mcp_dev_server:main",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    description="MCP Development Server"
)