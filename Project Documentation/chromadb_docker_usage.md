# ChromaDB Docker Usage Guide

## Overview

This project uses ChromaDB for vector storage, deployed as a Docker container for ease of use and consistency across environments. The ChromaDB instance is configured to use basic authentication and persists data to a Docker volume.

## Prerequisites

- Docker and Docker Compose installed on your system
- Environment variables configured in `.env` file

## Environment Variables

The following environment variables in your `.env` file are used by the ChromaDB container:

```
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=documents
CHROMA_AUTH_ENABLED=true
CHROMA_USERNAME=admin
CHROMA_PASSWORD=admin123
```

## Managing ChromaDB

### Recommended Method: Using the PowerShell Script

This project includes a convenient PowerShell script for managing the ChromaDB container. This is the recommended approach:

```powershell
# Start ChromaDB
.\scripts\start_chroma_docker.ps1

# Check status
.\scripts\start_chroma_docker.ps1 status

# View logs
.\scripts\start_chroma_docker.ps1 logs

# Restart ChromaDB
.\scripts\start_chroma_docker.ps1 restart

# Stop ChromaDB
.\scripts\start_chroma_docker.ps1 stop
```

The script offers several advantages:
- Automatically navigates to the project root directory
- Checks if Docker is running before attempting operations
- Verifies if ChromaDB is already running
- Provides clear status messages

### Alternative: Using Docker Compose Directly

You can also use Docker Compose commands directly:

```powershell
# Navigate to the project directory
cd C:\Users\kevin\repos\kev-new-graph-rag

# Start the container in detached mode
docker-compose up -d
```

## Verifying ChromaDB is Running

To check if ChromaDB is running properly:

```powershell
# Check container status
docker-compose ps

# View logs
docker-compose logs chroma
```

You can also access the ChromaDB heartbeat endpoint to verify the service is running:
- http://localhost:8000/api/v1/heartbeat

## Accessing ChromaDB

The ChromaDB instance is available at:
- Host: localhost (or the value of `CHROMA_HOST`)
- Port: 8000 (or the value of `CHROMA_PORT`)
- Authentication: Basic auth using values from `CHROMA_USERNAME` and `CHROMA_PASSWORD`

## Stopping ChromaDB

To stop the ChromaDB container:

```powershell
# Stop the container
docker-compose down

# Stop and remove volumes (caution: this deletes all stored embeddings)
docker-compose down -v
```

## Troubleshooting

If you encounter issues:

1. Check if the container is running: `docker-compose ps`
2. Examine logs for errors: `docker-compose logs chroma`
3. Verify your `.env` file has the correct configuration values
4. Ensure port 8000 is not in use by another application
5. Try restarting the container: `docker-compose restart chroma`

## Data Persistence

ChromaDB data is stored in a Docker volume named `chroma-data`. This ensures your vector database persists between container restarts. 

### Important Notes About Data Persistence:

- Your data persists whether you use the PowerShell script or direct `docker-compose` commands
- Starting, stopping, or restarting the container does NOT delete or reset your data
- All embeddings, vectors, and metadata remain intact between sessions
- Container restarts or system reboots will not affect your stored data

### When Data Could Be Lost:

Your ChromaDB data will only be deleted in these specific scenarios:

1. If you explicitly remove the Docker volume with `docker-compose down -v`
2. If you manually delete the Docker volume through Docker Desktop
3. If there's corruption in the Docker volume (rare)
