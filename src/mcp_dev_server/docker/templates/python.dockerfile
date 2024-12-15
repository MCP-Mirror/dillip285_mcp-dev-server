# Python development environment
FROM python:{{ python_version }}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

{% if install_poetry %}
# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
{% endif %}

{% if requirements_file %}
# Install Python dependencies
COPY {{ requirements_file }} .
RUN pip install -r {{ requirements_file }}
{% endif %}

{% if additional_packages %}
# Install additional packages
RUN pip install {% for package in additional_packages %}{{ package }} {% endfor %}
{% endif %}

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

{% if command %}
# Default command
CMD {{ command }}
{% endif %}