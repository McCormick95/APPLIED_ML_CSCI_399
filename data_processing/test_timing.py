import subprocess
import matplotlib.pyplot as plt

# List of cell sizes to test
# cells_array = [64, 128, 192, 256, 320, 384, 448, 512]

cells_array = [x for x in range(64, 576, 64)]

# Lists to store simulation data
cells = []
simulation_times = []

# Function to run the CloverLeaf script and capture the output
def run_cloverleaf(cells):
    # Run the python script and capture the output
    result = subprocess.run(['python3', 'run_cloverleaf.py', '--cells', str(cells)], capture_output=True, text=True)
    return result.stdout

# Function to extract the simulation time from the output
def extract_simulation_time(output):
    # Search for the line that contains the simulation time
    for line in output.split('\n'):
        if 'Simulation completed in' in line:
            # Extract the time using a simple regex pattern
            time_str = line.split('Simulation completed in')[1].split('seconds')[0].strip()
            return float(time_str)
    return None

# Run simulations and collect data
for cells_count in cells_array:
    print(f"Running simulation for {cells_count} cells...")
    
    # Run the CloverLeaf simulation
    output = run_cloverleaf(cells_count)
    
    # Extract simulation time from the output
    simulation_time = extract_simulation_time(output)
    
    if simulation_time is not None:
        # Store the result in memory
        cells.append(cells_count)
        simulation_times.append(simulation_time)
    else:
        print(f"Error: Could not extract simulation time for {cells_count} cells.")

# Plot the data
plt.figure(figsize=(8, 6))
plt.plot(cells, simulation_times, marker='o', linestyle='-', color='b')

# Set axis ticks to the actual values
plt.xticks(cells)  # Use the exact cell counts for the x-axis ticks
plt.yticks(simulation_times)  # Use the exact simulation times for the y-axis ticks

# Adding title and labels
plt.title('Simulation Time vs. Number of Cells')
plt.xlabel('Number of Cells')
plt.ylabel('Simulation Time (seconds)')

# Show grid
plt.grid(True)

# Save the plot as an image
plt.savefig('simulation_times_plot.png')

# Display the plot
plt.show()
