"""Dockerfile templates for different environments."""
from typing import Dict, Optional
from jinja2 import Template

class DockerTemplates:
    """Manages Dockerfile templates for different environments."""
    
    @staticmethod
    def get_template(environment: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Get Dockerfile template for specific environment."""
        config = config or {}
        
        if environment == "python":
            return Template("""
FROM python:{{ python_version|default('3.12-slim') }}

WORKDIR /app

{% if requirements_file %}
COPY {{ requirements_file }} .
RUN pip install -r {{ requirements_file }}
{% endif %}

{% if install_dev_deps %}
RUN pip install pytest mypy black
{% endif %}

{% for cmd in additional_commands|default([]) %}
RUN {{ cmd }}
{% endfor %}

COPY . .

CMD ["python", "{{ entry_point|default('main.py') }}"]
""").render(config)
            
        elif environment == "node":
            return Template("""
FROM node:{{ node_version|default('20-slim') }}

WORKDIR /app

COPY package*.json ./

RUN npm install {% if install_dev_deps %}--include=dev{% endif %}

{% for cmd in additional_commands|default([]) %}
RUN {{ cmd }}
{% endfor %}

COPY . .

CMD ["npm", "{{ npm_command|default('start') }}"]
""").render(config)
            
        else:
            raise ValueError(f"Unknown environment: {environment}")