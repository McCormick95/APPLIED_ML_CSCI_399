#!/bin/bash

# Get the absolute path of the repository root (assuming script is in bash_scripts directory)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Define directory paths relative to repository root
CLOVER_DIR="${REPO_ROOT}/CloverLeaf_Serial"
OUTPUT_DIR="${REPO_ROOT}/data_processing/new_data"
VISUALIZATION_SCRIPT="${REPO_ROOT}/data_processing/visualize.py"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Navigate to CloverLeaf directory and run simulation
cd "$CLOVER_DIR"
if [ ! -f "clover_leaf" ]; then
    echo "Error: clover_leaf executable not found. Building..."
    make clean
    make COMPILER=GNU
fi

# Run the simulation
echo "Starting CloverLeaf simulation..."
./clover_leaf

# Check if simulation completed successfully by looking for completion message in clover.out
if grep -q "Calculation complete" clover.out; then
    echo "Simulation completed successfully. Moving files..."
    
    # Move VTK and other output files to the output directory
    mv *.vtk "$OUTPUT_DIR/"
    mv clover.visit "$OUTPUT_DIR/"
    mv clover.out "$OUTPUT_DIR/"
    
    echo "Files moved to $OUTPUT_DIR/"
    echo "Number of files in output directory:"
    ls -l "$OUTPUT_DIR" | wc -l
    
    # Run visualization script
    echo "Running visualization script..."
    cd "$REPO_ROOT/data_processing"
    python3 visualize.py
    
    # Create TAR file with date
    echo "Creating TAR archive of VTK files..."
    DATE_STAMP=$(date +%Y%m%d_%H%M%S)
    cd "$OUTPUT_DIR"
    tar -czf "vtk_files_${DATE_STAMP}.tar.gz" *.vtk
    
    echo "Archive created: vtk_files_${DATE_STAMP}.tar.gz"
else
    echo "Simulation did not complete successfully. Files will remain in place."
    echo "Check clover.out for details."
    exit 1
fi

# Return to original directory
cd - > /dev/null