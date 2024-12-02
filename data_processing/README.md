Here's the complete updated README.md:

# CloverLeaf Workflow and Visualization

## Dependencies

The following dependencies are required before running the scripts:

- **Python 3.x** (preferably 3.8 or higher)
- **Matplotlib**: For visualization and animation
- **VTK**: For reading VTK files produced by CloverLeaf
- **Numpy**: For handling numerical data
- **FFmpeg**: For saving animations in video format

### Installing Dependencies

You can install the Python dependencies via `pip`:

```bash
pip install matplotlib vtk numpy
```

Additionally, you'll need **FFmpeg** installed on your system:

- **Ubuntu/Debian**:
    ```bash
    sudo apt-get install ffmpeg
    ```

- **macOS (Homebrew)**:
    ```bash
    brew install ffmpeg
    ```

- **Windows**:
    Download and install FFmpeg from [FFmpeg official website](https://ffmpeg.org/download.html).

## Scripts Overview

### 1. `run_cloverleaf.py`

`run_cloverleaf.py` is responsible for:

- **Generating input files** for the CloverLeaf simulation
- **Running the CloverLeaf simulation** with the specified parameters
- **Processing the generated VTK files** into `.npy` files
- **Zipping the output data** (both `.vtk` and `.npy` files) with a timestamp
- **Optionally visualizing** the results and creating an animation video

#### Usage

To run the simulation, use the following command:

```bash
python3 run_cloverleaf.py [options]
```

##### Available Options:
- `--cells`: Number of cells in both x and y directions (default: 64)
- `--steps`: Number of simulation steps (default: 500)
- `--visit-freq`: Frequency of VTK file generation (default: 1)
- `--base-dir`: Base directory for the CloverLeaf project (optional)
- `--visualize`: Flag to generate an animation video
- `--cleanup`: Clean the CloverLeaf directory after running
- Additional state parameters:
  - `--state1_density`: Density for state 1 (default: 0.2)
  - `--state1_energy`: Energy for state 1 (default: 1.0)
  - `--state2_density`: Density for state 2 (default: 1.0)
  - `--state2_energy`: Energy for state 2 (default: 2.5)
  - `--state2_xmin`: X minimum for state 2 (default: 0.0)
  - `--state2_xmax`: X maximum for state 2 (default: 1.0)
  - `--state2_ymin`: Y minimum for state 2 (default: 0.0)
  - `--state2_ymax`: Y maximum for state 2 (default: 1.0)
- Geometry parameters:
  - `--xmin`: Overall X minimum (default: 0.0)
  - `--xmax`: Overall X maximum (default: 5.0)
  - `--ymin`: Overall Y minimum (default: 0.0)
  - `--ymax`: Overall Y maximum (default: 5.0)
- Timestep parameters:
  - `--initial_timestep`: Initial timestep size (default: 0.04)
  - `--timestep_rise`: Timestep rise factor (default: 1.5)
  - `--max_timestep`: Maximum allowed timestep (default: 0.04)

#### Example:

```bash
python3 run_cloverleaf.py --cells 64 --steps 1000 --visit-freq 5 --visualize
```

This will run the simulation for 1000 steps with a 64x64 grid, generate VTK files every 5 steps, and create an animation video of the results.

### 2. `clover_vis.py`

`clover_vis.py` handles the visualization and animation generation from the VTK files produced by the CloverLeaf simulation. It performs the following tasks:

- **Reads VTK files** to extract simulation data
- **Processes data** (velocity, magnitude, etc.) and stores it in `.npy` files
- **Creates animations** based on simulation variables and saves them as `.mp4` files
- **Does not display color bars** in the animations for a cleaner output

#### Key Features:
- **Visualization of velocity magnitude** (or any other variable from the VTK data)
- **Supports automatic file naming** with timestamps to avoid overwriting
  
#### Methods:

- `create_animation(variable='velocity_magnitude')`: Generates an animation of the selected variable (default is `velocity_magnitude`) and saves it as an `.mp4` file
- `read_vtk_file(filename)`: Reads a VTK file and returns the simulation data (coordinates and values)
- `process_all_files()`: Processes all VTK files in the input directory and saves them as `.npy` files

## Notes

1. **Running the Simulation**: Make sure the CloverLeaf simulation is in the `CloverLeaf_Serial` directory.

2. **Data Processing**: The simulation data is processed from VTK files to `.npy` files for easier handling in further analysis or machine learning tasks.

3. **Animation**: The `--visualize` flag will create a video showing the evolution of the simulation over time. The video is stored with the timestamp and iteration number to ensure uniqueness.

4. **Error Handling**: The script checks if the required VTK files are available before generating the video and handles errors gracefully if files are missing.

## Example Workflow

Here is an example of a typical workflow:

1. **Run the simulation** with specified parameters:

    ```bash
    python3 run_cloverleaf.py --cells 64 --steps 500 --visit-freq 1
    ```

2. **Process the output**: The `.vtk` files will be archived and deleted, and the `.npy` files will be zipped. 

3. **To visualize the results**:

    ```bash
    python3 run_cloverleaf.py --visualize --cells 64 --steps 500 --visit-freq 1
    ```

    This will generate an animation video of the simulation evolution, saved with a timestamp in the `visualizations` directory.

## Troubleshooting

- **FFmpeg not found**: Make sure FFmpeg is installed and available in your system's PATH for video generation. You can verify by running `ffmpeg -version` in the terminal.

- **Missing VTK files**: If the VTK files are missing or corrupted, the `create_animation` method will fail. Ensure the simulation generated the correct output files.

- **Permissions**: Ensure you have appropriate permissions to write to the output directories, especially when dealing with large simulations.

---
