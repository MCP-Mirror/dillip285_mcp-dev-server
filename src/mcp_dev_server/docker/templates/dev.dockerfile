# Multi-language development environment
FROM ubuntu:{{ ubuntu_version }}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

{% if install_python %}
# Install Python
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python{{ python_version }} python{{ python_version }}-venv python{{ python_version }}-dev && \
    rm -rf /var/lib/apt/lists/*
{% endif %}

{% if install_node %}
# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_{{ node_version }}.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*
{% endif %}

{% if install_docker %}
# Install Docker
RUN curl -fsSL https://get.docker.com | sh && \
    rm -rf /var/lib/apt/lists/*
{% endif %}

# Set working directory
WORKDIR /workspace

{% if requirements_file %}
# Install Python dependencies
COPY {{ requirements_file }} .
RUN pip{{ python_version }} install -r {{ requirements_file }}
{% endif %}

{% if package_file %}
# Install Node.js dependencies
COPY {{ package_file }} .
{% if package_lock %}
COPY {{ package_lock }} .
RUN npm ci
{% else %}
RUN npm install
{% endif %}
{% endif %}

{% if additional_tools %}
# Install additional tools
RUN apt-get update && apt-get install -y \
    {% for tool in additional_tools %}{{ tool }} {% endfor %} \
    && rm -rf /var/lib/apt/lists/*
{% endif %}

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=development

{% if command %}
# Default command
CMD {{ command }}
{% endif %}