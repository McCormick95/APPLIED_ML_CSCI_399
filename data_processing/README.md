
---

# CloverLeaf Workflow and Visualization

- `run_cloverleaf.py`: Runs the CloverLeaf simulation, processes data, and optionally visualizes the results.
- `clover_vis.py`: Handles visualization and generates animation of simulation results.

## Requirements

Make sure the following dependencies are installed before running the scripts:

- **Python 3.x** (preferably 3.8 or higher)
- **Matplotlib**: For visualization and animation.
- **VTK**: To read VTK files produced by CloverLeaf.
- **Numpy**: For handling numerical data.
- **FFMpeg**: For saving animations in video format.

You can install the required dependencies via `pip`:

```bash
pip install matplotlib vtk numpy
```

Additionally, ensure that **FFmpeg** is installed on your system. You can install it using:

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

- **Generating input files** for the CloverLeaf simulation.
- **Running the CloverLeaf simulation** with the specified parameters.
- **Processing the generated VTK files** into `.npy` files.
- **Zipping the output data** (both `.vtk` and `.npy` files) with a timestamp to avoid overwriting previous outputs.
- **Optionally visualizing** the results and creating an animation video.

#### Usage

To run the simulation and generate an animation, use the following command:

```bash
python3 run_cloverleaf.py --visualize --cells <num_cells> --steps <num_steps> --visit-freq <visit_frequency> --base-dir <base_directory>
```

- `--visualize`: (Optional) Flag to generate an animation video. If not specified, the video generation is skipped.
- `--cells`: Number of cells in both the x and y directions. Default is `64`.
- `--steps`: Number of simulation steps. Default is `500`.
- `--visit-freq`: Frequency of VTK file generation. Default is `1`.
- `--base-dir`: (Optional) The base directory for the CloverLeaf project. If not specified, it is automatically detected.

#### Example:

```bash
python3 run_cloverleaf.py --visualize --cells 64 --steps 1000 --visit-freq 5
```

This will run the simulation for `1000` steps, process the VTK files into `.npy` files, and generate a video of the simulation with a frequency of every 5 steps.

---

### 2. `clover_vis.py`

`clover_vis.py` handles the visualization and animation generation from the VTK files produced by the CloverLeaf simulation. It performs the following tasks:

- **Reads VTK files** to extract simulation data.
- **Processes data** (velocity, magnitude, etc.) and stores it in `.npy` files.
- **Creates animations** based on simulation variables and saves them as `.mp4` files.
- **Does not display color bars** in the animations for a cleaner output.

#### Key Features:
- **Visualization of velocity magnitude** (or any other variable from the VTK data).
- **Supports automatic file naming** with timestamps to avoid overwriting.
  
#### Methods:

- `create_animation(variable='velocity_magnitude')`: Generates an animation of the selected variable (default is `velocity_magnitude`) and saves it as an `.mp4` file.

- `read_vtk_file(filename)`: Reads a VTK file and returns the simulation data (coordinates and values).

- `process_all_files()`: Processes all VTK files in the input directory and saves them as `.npy` files.

---
## Notes

1. **Running the Simulation**: Make sure the CloverLeaf simulation is properly compiled and executable in the `CloverLeaf_Serial` directory. The script assumes the executable is named `clover_leaf`.

2. **Data Processing**: The simulation data is processed from VTK files to `.npy` files for easier handling in further analysis or machine learning tasks.

3. **Animation**: The `--visualize` flag will create a video showing the evolution of the simulation over time. The video is stored with the timestamp and iteration number to ensure uniqueness.

4. **Error Handling**: The script checks if the required VTK files are available before generating the video and handles errors gracefully if files are missing.

---

## Example Workflow

Here is an example of a typical workflow:

1. **Run the simulation** with specified parameters:

    ```bash
    python3 run_cloverleaf.py --cells 64 --steps 500 --visit-freq 1
    ```

2. **Process the output**: The `.vtk` files will be archived and deleted, and the `.npy` files will be zipped. 

3. **Visualize the results**:

    ```bash
    python3 run_cloverleaf.py --visualize --cells 64 --steps 500 --visit-freq 1
    ```

    This will generate an animation video of the simulation evolution, saved with a timestamp in the `visualizations` directory.

---

## Troubleshooting

- **FFmpeg not found**: Make sure FFmpeg is installed and available in your system's PATH for video generation. You can verify by running `ffmpeg -version` in the terminal.

- **Missing VTK files**: If the VTK files are missing or corrupted, the `create_animation` method will fail. Ensure the simulation generated the correct output files.

- **Permissions**: Ensure you have appropriate permissions to write to the output directories, especially when dealing with large simulations.

---