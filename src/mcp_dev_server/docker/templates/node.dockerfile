# Node.js development environment
FROM node:{{ node_version }}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

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

{% if global_packages %}
# Install global packages
RUN npm install -g {% for package in global_packages %}{{ package }} {% endfor %}
{% endif %}

# Set Node.js environment variables
ENV NODE_ENV=development

{% if command %}
# Default command
CMD {{ command }}
{% endif %}