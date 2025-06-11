# ChromaDB Docker Container Management Script

# Parse command line arguments
param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'status', 'restart', 'logs')]
    [string]$Action = 'start'
)

# Navigate to project root
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Function to check if ChromaDB is running
function Test-ChromaDBRunning {
    try {
        $containerStatus = docker ps --filter "name=chromadb" --format "{{.Status}}"
        return ![string]::IsNullOrEmpty($containerStatus)
    } catch {
        return $false
    }
}

# Handle different actions
switch ($Action) {
    'start' {
        if (Test-ChromaDBRunning) {
            Write-Host "ChromaDB is already running."
        } else {
            Write-Host "Starting ChromaDB container..."
            docker-compose up -d
            Write-Host "ChromaDB should be running at http://localhost:8000"
        }
    }
    'stop' {
        Write-Host "Stopping ChromaDB container..."
        docker-compose down
    }
    'restart' {
        Write-Host "Restarting ChromaDB container..."
        docker-compose down
        docker-compose up -d
        Write-Host "ChromaDB restarted and should be running at http://localhost:8000"
    }
    'status' {
        if (Test-ChromaDBRunning) {
            Write-Host "ChromaDB is running."
            docker ps --filter "name=chromadb"
        } else {
            Write-Host "ChromaDB is not running."
        }
    }
    'logs' {
        Write-Host "Showing ChromaDB logs (press Ctrl+C to exit):"
        docker-compose logs -f
    }
}
