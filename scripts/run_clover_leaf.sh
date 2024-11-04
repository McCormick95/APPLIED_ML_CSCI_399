#!/bin/bash

# Get the absolute path of the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Source utility scripts
source "${REPO_ROOT}/scripts/generate_clover_input.sh"
source "${REPO_ROOT}/scripts/archive_utils.sh"

# Define directory paths relative to repository root
CLOVER_DIR="${REPO_ROOT}/CloverLeaf_Serial"
OUTPUT_DIR="${REPO_ROOT}/data_processing/new_data"
VISUALIZATION_SCRIPT="${REPO_ROOT}/data_processing/visualize.py"
VISUALIZATIONS_DIR="${REPO_ROOT}/data_processing/visualizations"

# Default values
GENERATE_NEW_INPUT=0
NUM_ITERATIONS=1
NUM_CELLS=512  # Default value for both x and y cells
NUM_STEPS=100  # Default value for end_step

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --generate-input        Generate new random input for each iteration"
    echo "  --iterations N          Number of iterations to run (default: 1)"
    echo "  --cells N              Number of cells for both x and y (default: 960)"
    echo "  --steps N              Number of steps to run (default: 87)"
    echo "  --help                 Show this help message"
}

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --generate-input)
            GENERATE_NEW_INPUT=1
            shift
            ;;
        --iterations)
            if [[ $2 =~ ^[0-9]+$ ]]; then
                NUM_ITERATIONS="$2"
                shift 2
            else
                echo "Error: --iterations requires a number"
                exit 1
            fi
            ;;
        --cells)
            if [[ $2 =~ ^[0-9]+$ ]]; then
                NUM_CELLS="$2"
                shift 2
            else
                echo "Error: --cells requires a number"
                exit 1
            fi
            ;;
        --steps)
            if [[ $2 =~ ^[0-9]+$ ]]; then
                NUM_STEPS="$2"
                shift 2
            else
                echo "Error: --steps requires a number"
                exit 1
            fi
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown parameter: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$VISUALIZATIONS_DIR"

# Navigate to CloverLeaf directory
cd "$CLOVER_DIR"
if [ ! -f "clover_leaf" ]; then
    echo "Error: clover_leaf executable not found. Building..."
    make clean
    make COMPILER=GNU
fi

# Run multiple iterations
for (( i=1; i<=NUM_ITERATIONS; i++ )); do
    echo "Running iteration $i of $NUM_ITERATIONS"
    
    # When generating new input, pass the new parameters
    if [ $GENERATE_NEW_INPUT -eq 1 ]; then
        echo "Generating new input file for iteration $i"
        generate_clover_input "clover.in" $NUM_CELLS $NUM_STEPS
    fi
    
    # Run the simulation
    echo "Starting CloverLeaf simulation..."
    ./clover_leaf

    # Check if simulation completed successfully
    if grep -q "Calculation complete" clover.out; then
        echo "Simulation $i completed successfully. Moving files..."
        
        # Create iteration-specific directory
        ITER_DIR="${OUTPUT_DIR}/iteration_${i}"
        mkdir -p "$ITER_DIR"
        
        # Save the input file for reference
        cp clover.in "${ITER_DIR}/clover.in"
        
        # Move output files
        mv *.vtk "$ITER_DIR/"
        mv clover.visit "$ITER_DIR/"
        mv clover.out "$ITER_DIR/"
        
        echo "Running visualization script..."
        cd "$REPO_ROOT/data_processing"
        python3 visualize.py --input-dir "$ITER_DIR" --output-dir "$VISUALIZATIONS_DIR"
        
        # Create archive and cleanup
        create_archive_and_cleanup "$REPO_ROOT" "$i" "$OUTPUT_DIR"
    else
        echo "Simulation $i did not complete successfully. Check clover.out for details."
        exit 1
    fi
    
    echo "Completed iteration $i"
    echo "----------------------"
done

# Return to original directory
cd - > /dev/null

echo "All iterations completed successfully"