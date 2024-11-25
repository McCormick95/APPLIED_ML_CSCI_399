import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from vtk.util import numpy_support
import vtk
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloverLeafVisualizer:
    def __init__(self, input_dir, output_dir, npy_dir=None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.npy_dir = Path(npy_dir) if npy_dir else Path(output_dir) / 'npy_data'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.npy_dir.mkdir(parents=True, exist_ok=True)
        
    def read_vtk_file(self, filename):
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
            
            # Get cell-centered data
            n_cell_arrays = cell_data.GetNumberOfArrays()
            logger.info(f"Available cell-centered arrays:")
            for i in range(n_cell_arrays):
                name = cell_data.GetArrayName(i)
                logger.info(f"  {name}")
                array = numpy_support.vtk_to_numpy(cell_data.GetArray(i))
                array = array.reshape((len(y_coords)-1, len(x_coords)-1))
                result['cell_data'][name] = array
            
            # Get point-centered data
            n_point_arrays = point_data.GetNumberOfArrays()
            logger.info(f"Available point-centered arrays:")
            for i in range(n_point_arrays):
                name = point_data.GetArrayName(i)
                logger.info(f"  {name}")
                array = numpy_support.vtk_to_numpy(point_data.GetArray(i))
                array = array.reshape((len(y_coords), len(x_coords)))
                result['point_data'][name] = array
                
            # Calculate velocity magnitude if velocity components exist
            if 'x_vel' in result['point_data'] and 'y_vel' in result['point_data']:
                xvel = result['point_data']['x_vel']
                yvel = result['point_data']['y_vel']
                result['point_data']['velocity_magnitude'] = np.sqrt(xvel**2 + yvel**2)

            return result
            
        except Exception as e:
            logger.error(f"Error reading VTK file: {str(e)}")
            raise
    
    def save_timestep_data(self, data, timestep):
        """Save all data from one timestep as a single NPY file"""
        try:
            # Create 2D coordinate arrays
            x_coords_2d = np.tile(data['x_coords'], (len(data['y_coords']), 1))
            y_coords_2d = np.tile(data['y_coords'], (len(data['x_coords']), 1)).T
            
            # Get velocity components and calculate magnitude
            xvel = data['point_data']['x_vel']
            yvel = data['point_data']['y_vel']
            magnitude = data['point_data']['velocity_magnitude']
            
            # Stack all arrays
            data_array = np.stack([magnitude, xvel, yvel, x_coords_2d, y_coords_2d], axis=0)
            
            # Save to a single NPY file
            filename = self.npy_dir / f'timestep_{timestep:04d}.npy'
            np.save(filename, data_array)
            logger.info(f"Saved timestep {timestep} to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving timestep {timestep}: {str(e)}")
            raise

    def process_all_files(self):
        """Process all VTK files and save each timestep as a single NPY file"""
        vtk_files = sorted(list(self.input_dir.glob("*.vtk")))
        logger.info(f"Processing {len(vtk_files)} VTK files...")
        
        for i, vtk_file in enumerate(vtk_files):
            logger.info(f"Processing timestep {i} from {vtk_file.name}")
            data = self.read_vtk_file(vtk_file)
            self.save_timestep_data(data, i)
        
        logger.info(f"Saved all timesteps to {self.npy_dir}")
        
        return metadata

    def create_animation(self, variable='velocity_magnitude', data_type='point_data'):
        """Create animation for specified variable"""
        # Original animation code remains the same
        vtk_files = sorted(list(self.input_dir.glob("*.vtk")))
        
        if not vtk_files:
            logger.error(f"No VTK files found in {self.input_dir}")
            return
            
        logger.info(f"Found {len(vtk_files)} VTK files")
        
        # Set up figure
        dpi = 100
        figsize = (10, 10)
        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax = plt.Axes(fig, [0.1, 0.1, 0.8, 0.8])
        fig.add_axes(ax)
        
        # Read first frame
        data = self.read_vtk_file(vtk_files[0])
        if variable not in data[data_type]:
            raise ValueError(f"Variable '{variable}' not found in {data_type}")
        
        x = data['x_coords']
        y = data['y_coords']
        if data_type == 'cell_data':
            x = x[:-1]
            y = y[:-1]
        
        def update(frame):
            ax.clear()
            data = self.read_vtk_file(vtk_files[frame])
            values = data[data_type][variable]
            
            contour = ax.contourf(x, y, values, levels=20, cmap='viridis')
            if frame == 0:
                plt.colorbar(contour, ax=ax, label=variable)
            
            ax.set_title(f'{variable.replace("_", " ").title()} - Frame {frame}')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_aspect('equal')
        
        logger.info(f"Creating animation for {variable}...")
        anim = FuncAnimation(fig, update, frames=len(vtk_files),
                           interval=200, blit=False)
        
        output_file = self.output_dir / f'{variable}_evolution.mp4'
        logger.info(f"Saving animation to {output_file}")
        
        writer = FFMpegWriter(fps=5, metadata=dict(artist='CloverLeaf Visualizer'),
                            bitrate=2000)
        
        anim.save(str(output_file), writer=writer)
        plt.close(fig)
        logger.info("Animation complete")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CloverLeaf data processing and visualization')
    parser.add_argument('--input-dir', type=str, default='new_data',
                      help='Directory containing VTK files')
    parser.add_argument('--output-dir', type=str, default='visualizations',
                      help='Directory to save visualizations')
    parser.add_argument('--npy-dir', type=str, default=None,
                      help='Directory to save NPY files (default: output_dir/npy_data)')
    parser.add_argument('--variable', type=str, default='velocity_magnitude',
                      help='Variable to visualize')
    parser.add_argument('--data-type', type=str, default='point_data',
                      choices=['cell_data', 'point_data'],
                      help='Type of data to visualize')
    parser.add_argument('--save-npy', action='store_true',
                      help='Save data as NPY files')
    
    args = parser.parse_args()
    
    visualizer = CloverLeafVisualizer(args.input_dir, args.output_dir, args.npy_dir)
    
    if args.save_npy:
        metadata = visualizer.process_all_files()
        logger.info("Saved NPY files with metadata")
    
    visualizer.create_animation(variable=args.variable, data_type=args.data_type)