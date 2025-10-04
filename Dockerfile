# Use the official Python runtime image
FROM python:3.13  

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

 
# Create the app directory
RUN mkdir /app
 
# Set the working directory inside the container
WORKDIR /app
 
# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 
 
# Upgrade pip
RUN pip install --upgrade pip 
 
# Copy the Django project  and install dependencies
COPY pyproject.toml  /app/
 
# run this command to install all dependencies 
# RUN uv pip install --no-cache-dir -r pyproject.toml

RUN uv sync
 
# Copy the Django project to the container
COPY . /app/

RUN chmod +x /app/entrypoint.sh

# Expose the Django port
EXPOSE 8000

# Use entrypoint script as the entry point
ENTRYPOINT ["/app/entrypoint.sh"]
