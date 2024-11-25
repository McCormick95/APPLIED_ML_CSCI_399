import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from vtk.util import numpy_support
import vtk
from pathlib import Path
import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime

# Set the logging level to WARNING (or ERROR) to suppress INFO level logs
logger = logging.getLogger('clover_vis')
logger.setLevel(logging.WARNING)  # Change to ERROR if you want to suppress even more

class CloverVisualizer:
    def __init__(self, input_dir: str, output_dir: str, npy_dir: Optional[str] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.npy_dir = Path(npy_dir) if npy_dir else self.output_dir / "npy_files"
        self.npy_dir.mkdir(parents=True, exist_ok=True)
        
        self.timing_data = {'data_processing': 0, 'visualization': 0}
    
    def read_vtk_file(self, filename: str) -> Dict[str, Any]:
        """Read all data from VTK file"""
        try:
            logger.info(f"Reading file: {filename}")
            
            reader = vtk.vtkRectilinearGridReader()
            reader.SetFileName(str(filename))
            reader.ReadAllScalarsOn()
            reader.Update()
            
            data = reader.GetOutput()
            cell_data = data.GetCellData()
            point_data = data.GetPointData()
            
            # Get dimensions and coordinates
            x_coords = numpy_support.vtk_to_numpy(data.GetXCoordinates())
            y_coords = numpy_support.vtk_to_numpy(data.GetYCoordinates())
            
            result = {
                'x_coords': x_coords,
                'y_coords': y_coords,
                'cell_data': {},
                'point_data': {}
            }
            
            # Extract cell-centered data
            for i in range(cell_data.GetNumberOfArrays()):
                name = cell_data.GetArrayName(i)
                array = numpy_support.vtk_to_numpy(cell_data.GetArray(i))
                array = array.reshape((len(y_coords) - 1, len(x_coords) - 1))
                result['cell_data'][name] = array
            
            # Extract point-centered data
            for i in range(point_data.GetNumberOfArrays()):
                name = point_data.GetArrayName(i)
                array = numpy_support.vtk_to_numpy(point_data.GetArray(i))
                array = array.reshape((len(y_coords), len(x_coords)))
                result['point_data'][name] = array
            
            # Compute velocity magnitude if components exist
            if 'x_vel' in result['point_data'] and 'y_vel' in result['point_data']:
                xvel = result['point_data']['x_vel']
                yvel = result['point_data']['y_vel']
                result['point_data']['velocity_magnitude'] = np.sqrt(xvel**2 + yvel**2)
            
            return result
        except Exception as e:
            logger.error(f"Error reading VTK file: {e}")
            raise
    
    def save_timestep_data(self, data: Dict[str, Any], timestep: int) -> None:
        """Save all data from one timestep as a single NPY file"""
        try:
            # Create 2D coordinate arrays
            x_coords_2d = np.tile(data['x_coords'], (len(data['y_coords']), 1))
            y_coords_2d = np.tile(data['y_coords'], (len(data['x_coords']), 1)).T
            
            # Get velocity components and magnitude
            xvel = data['point_data']['x_vel']
            yvel = data['point_data']['y_vel']
            magnitude = data['point_data']['velocity_magnitude']
            
            # Stack arrays for saving
            data_array = np.stack([magnitude, xvel, yvel, x_coords_2d, y_coords_2d], axis=0)
            
            filename = self.npy_dir / f"timestep_{timestep:04d}.npy"
            np.save(filename, data_array)
            logger.info(f"Saved timestep {timestep} to {filename}")
        except Exception as e:
            logger.error(f"Error saving timestep {timestep}: {e}")
            raise
    
    def process_all_files(self) -> None:
        """Process all VTK files and save each timestep as a single NPY file."""
        vtk_files = sorted(list(self.input_dir.glob("*.vtk")))
        logger.info(f"Processing {len(vtk_files)} VTK files...")
        
        for i, vtk_file in enumerate(vtk_files):
            logger.debug(f"Processing timestep {i} from {vtk_file.name}")
            data = self.read_vtk_file(vtk_file)
            self.save_timestep_data(data, i)
        
        logger.info(f"Saved all timesteps to {self.npy_dir}")


    def create_animation(self, variable: str = 'velocity_magnitude') -> float:
        start_time = time.time()
        vtk_files = sorted(list(self.input_dir.glob("*.vtk")))
        
        if not vtk_files:
            logger.error(f"No VTK files found in {self.input_dir}")
            return 0
        
        fig = plt.figure(figsize=(10, 10))
        ax = plt.Axes(fig, [0.1, 0.1, 0.8, 0.8])
        fig.add_axes(ax)
        
        data = self.read_vtk_file(vtk_files[0])
        x, y = data['x_coords'], data['y_coords']
        
        def update(frame):
            ax.clear()
            data = self.read_vtk_file(vtk_files[frame])
            values = data['point_data'][variable]
            
            contour = ax.contourf(x, y, values, levels=20, cmap='viridis')
            
            ax.set_title(f'{variable.title()} - Frame {frame}')
            ax.set_aspect('equal')
            
            # Remove the color bar by commenting out the following line:
            # plt.colorbar(contour, ax=ax, label=variable)
        
        anim = FuncAnimation(fig, update, frames=len(vtk_files),
                            interval=200, blit=False)
        
        # Use the timestamp and iteration for consistent naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"velocity_magnitude_evolution_{timestamp}.mp4"
        writer = FFMpegWriter(fps=5, bitrate=2000)
        anim.save(str(output_file), writer=writer)
        plt.close(fig)
        
        elapsed_time = time.time() - start_time
        self.timing_data['visualization'] = elapsed_time
        return elapsed_time

    def get_timing_data(self) -> Dict[str, float]:
        return self.timing_data