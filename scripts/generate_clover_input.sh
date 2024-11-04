#!/bin/bash

OUTPUT_STEP_VALUE=5 # Adjust this to control how often VTK files are written

# Function to generate random number between min and max
generate_random() {
    local min=$1
    local max=$2
    echo "scale=1; $min + ($max - $min) * $RANDOM / 32767" | bc
}

# Function to generate a single clover.in file with random or specified parameters
generate_clover_input() {
    local output_file=$1
    local num_cells=${2:-960}  # Default to 512 if not specified
    local num_steps=${3:-87}   # Default to 100 if not specified
    
    # Generate random values
    local density1=$(generate_random 0.1 0.5)
    local density2=$(generate_random 0.8 1.5)
    local energy1=$(generate_random 0.8 1.2)
    local energy2=$(generate_random 2.0 3.0)
    local xmax=$(generate_random 4.0 6.0)
    local ymax=$(generate_random 1.5 2.5)
    
    # Create new clover.in file with random values
    cat > "$output_file" << EOF
*clover

 state 1 density=${density1} energy=${energy1}
 state 2 density=${density2} energy=${energy2} geometry=rectangle xmin=0.0 xmax=${xmax} ymin=0.0 ymax=${ymax}

 x_cells=${num_cells}
 y_cells=${num_cells}

 xmin=0.0
 ymin=0.0
 xmax=10.0
 ymax=10.0

 initial_timestep=0.04
 timestep_rise=1.5
 max_timestep=0.04
 end_step=${num_steps}
 test_problem 2

visit_frequency = ${OUTPUT_STEP_VALUE}   

*endclover
EOF

    # Print the generated values for reference
    echo "Generated parameters:"
    echo "State 1: density=${density1}, energy=${energy1}"
    echo "State 2: density=${density2}, energy=${energy2}, xmax=${xmax}, ymax=${ymax}"
    echo "Grid: ${num_cells} x ${num_cells} cells"
    echo "Steps: ${num_steps}"
}

# If script is run directly, use it to generate a single input file
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    output_file="${1:-clover.in}"  # Use provided filename or default to clover.in
    num_cells="${2:-960}"          # Use provided cells or default to 960
    num_steps="${3:-87}"           # Use provided steps or default to 87
    generate_clover_input "$output_file" "$num_cells" "$num_steps"
fi