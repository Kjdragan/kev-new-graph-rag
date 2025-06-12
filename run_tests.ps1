#!/usr/bin/env pwsh
# Script to run the test suite for kev-graph-rag project

param (
    [Parameter(Mandatory=$false)]
    [switch]$unit = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$integration = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$all = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$coverage = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$module = ""
)

# Display help if no parameters provided
if (-not ($unit -or $integration -or $all -or $coverage -or $module)) {
    Write-Host "Usage: ./run_tests.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -unit        Run unit tests only"
    Write-Host "  -integration Run integration tests only (requires valid .env file)"
    Write-Host "  -all         Run both unit and integration tests"
    Write-Host "  -coverage    Generate coverage report"
    Write-Host "  -module      Run tests for a specific module, e.g. 'utils.document_parser'"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./run_tests.ps1 -unit"
    Write-Host "  ./run_tests.ps1 -unit -coverage"
    Write-Host "  ./run_tests.ps1 -integration"
    Write-Host "  ./run_tests.ps1 -all"
    Write-Host "  ./run_tests.ps1 -module 'utils.gdrive_reader'"
    exit 0
}

# Base command using uv run
$command = "uv run pytest"

# Add verbosity for better output
$command += " -v"

# Build the command based on parameters
if ($unit) {
    $command += " -m unit"
}
elseif ($integration) {
    $command += " -m integration"
}
elseif ($all) {
    # No specific marker means run all tests
}

# Add coverage flag if requested
if ($coverage) {
    $command += " --cov=utils --cov-report=term --cov-report=html:coverage_report"
}

# Add module if specified
if ($module) {
    $command += " tests/$(${module}.replace('.', '/').replace('utils/', ''))"
}

# Display the command being run
Write-Host "Running: $command"

# Run the command
Invoke-Expression $command

# If coverage report was generated, display the path
if ($coverage) {
    Write-Host "`nCoverage report generated: $(Get-Location)/coverage_report/index.html"
}
