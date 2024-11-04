#!/bin/bash

# Function to format iteration number with leading zeros
format_iteration() {
    printf "%02d" $1
}

# Function to create archive and cleanup files
create_archive_and_cleanup() {
    local base_dir=$1
    local iteration=$2
    local output_dir=$3
    
    # Format date and iteration number
    local date_stamp=$(date +%Y%m%d_%H%M%S)
    local iter_num=$(format_iteration $iteration)
    local archive_name="clover_data_${date_stamp}_${iter_num}.tar.gz"
    
    # Create archive
    echo "Creating archive ${archive_name}..."
    cd "$output_dir"
    tar -czf "$archive_name" iteration_${iteration}
    
    # # Add archive pattern to .gitignore if not already present
    # local gitignore_file="${base_dir}/.gitignore"
    # local patterns=(
    #     "*.vtk"
    #     "*.tar.gz"
    #     "data_processing/new_data/*"
    #     "CloverLeaf_Serial/*.vtk"
    # )
    
    # # Create .gitignore if it doesn't exist
    # touch "$gitignore_file"
    
    # # Add patterns to .gitignore if they don't exist
    # for pattern in "${patterns[@]}"; do
    #     if ! grep -q "^${pattern}$" "$gitignore_file"; then
    #         echo "$pattern" >> "$gitignore_file"
    #         echo "Added ${pattern} to .gitignore"
    #     fi
    # done
    
    # Remove VTK files from CloverLeaf_Serial directory
    rm -f "${base_dir}/CloverLeaf_Serial/"*.vtk
    
    echo "Archive created and cleanup completed"
}