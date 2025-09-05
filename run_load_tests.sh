#!/bin/bash

# Load Testing Script for Python ML API
# This script runs Locust tests with different configurations and saves results

set -e  # Exit on any error

# Configuration
API_HOST="http://localhost:8080"
RESULTS_DIR="load_test_results"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if API server is running
check_api_server() {
    log "Checking if API server is running on $API_HOST..."
    if curl -s "$API_HOST/docs" > /dev/null; then
        success "API server is running"
        return 0
    else
        error "API server is not running on $API_HOST"
        error "Please start your API server with: uv run python run.py"
        return 1
    fi
}

# Wait for API to be ready
wait_for_api() {
    log "Waiting for API to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$API_HOST/docs" > /dev/null; then
            success "API is ready after $attempt attempts"
            return 0
        fi
        log "Attempt $attempt/$max_attempts - API not ready yet, waiting..."
        sleep 2
        ((attempt++))
    done
    
    error "API did not become ready after $max_attempts attempts"
    return 1
}

# Run a single load test
run_load_test() {
    local test_name="$1"
    local users="$2"
    local spawn_rate="$3"
    local run_time="$4"
    local description="$5"
    
    log "Running test: $test_name"
    log "Configuration: $users users, $spawn_rate spawn rate, $run_time duration"
    log "Description: $description"
    
    # Run locust test
    uv run locust \
        -f load_test.py \
        --host "$API_HOST" \
        --users "$users" \
        --spawn-rate "$spawn_rate" \
        --run-time "$run_time" \
        --headless \
        --csv "$RESULTS_DIR/$test_name" \
        --loglevel INFO
    
    if [ $? -eq 0 ]; then
        success "Test '$test_name' completed successfully"
        return 0
    else
        error "Test '$test_name' failed"
        return 1
    fi
}

# Main load testing scenarios
run_all_tests() {
    log "Starting comprehensive load testing suite..."
    
    # Test 1: Light Load - Baseline
    run_load_test "light_load" 50 5 "60s" "Light load baseline test"
    sleep 10  # Cooldown period
    
    # Test 2: Medium Load - Normal usage
    run_load_test "medium_load" 100 10 "60s" "Medium load usage test"
    sleep 10
    
    # Test 3: High Load - Peak usage
    run_load_test "high_load" 500 20 "60s" "High load usage test"
    sleep 10
    
    # Test 4: Stress Test - System limits
    run_load_test "stress_test" 1000 50 "60s" "Stress test"
    
    success "All load tests completed!"
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    # Kill any remaining locust processes
    pkill -f "locust" || true
    success "Cleanup completed"
}

# Main execution
main() {
    log "Starting Load Testing Suite"

    # Set up cleanup trap
    trap cleanup EXIT
    
    if ! check_api_server; then
        exit 1
    fi
    
    if ! wait_for_api; then
        exit 1
    fi
    
    run_all_tests    
    
    success "Load testing suite completed successfully!"
    log "Check the '$RESULTS_DIR' directory for all results"
}

# Run main function
main
