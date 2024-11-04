import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import vtk
from vtk.util import numpy_support
import os
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_vtk_file(filename):
    """Read data from VTK file with error checking"""
    try:
        logger.info(f"Reading file: {filename}")
        
        reader = vtk.vtkRectilinearGridReader()
        reader.SetFileName(str(filename))
        reader.ReadAllVectorsOn()
        reader.ReadAllScalarsOn()
        reader.Update()
        
        data = reader.GetOutput()
        point_data = data.GetPointData()
        
        # Get dimensions and coordinates
        dims = data.GetDimensions()
        x_coords = numpy_support.vtk_to_numpy(data.GetXCoordinates())
        y_coords = numpy_support.vtk_to_numpy(data.GetYCoordinates())
        
        # Debug print dimensions
        logger.info(f"Data dimensions: {dims}")
        logger.info(f"X coordinates shape: {x_coords.shape}")
        logger.info(f"Y coordinates shape: {y_coords.shape}")
        
        # Get velocity components
        xvel = None
        yvel = None
        
        n_arrays = point_data.GetNumberOfArrays()
        logger.info(f"Number of arrays: {n_arrays}")
        
        for i in range(n_arrays):
            array_name = point_data.GetArrayName(i)
            logger.info(f"Found array: {array_name}")
            if array_name == 'x_vel':
                xvel = numpy_support.vtk_to_numpy(point_data.GetArray(i))
            elif array_name == 'y_vel':
                yvel = numpy_support.vtk_to_numpy(point_data.GetArray(i))
        
        if xvel is None or yvel is None:
            raise RuntimeError("Velocity data not found in file")
            
        # Reshape arrays
        nx = len(x_coords)
        ny = len(y_coords)
        xvel = xvel.reshape((ny, nx))
        yvel = yvel.reshape((ny, nx))
        
        # Calculate velocity magnitude as substitute for pressure
        magnitude = np.sqrt(xvel**2 + yvel**2)
        
        return magnitude, xvel, yvel, x_coords, y_coords
        
    except Exception as e:
        logger.error(f"Error reading VTK file: {str(e)}")
        logger.error(f"File path: {filename}")
        raise

def plot_frame(magnitude, xvel, yvel, x_coords, y_coords, time_step):
    """Create a single frame plot"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Plot 1: Velocity magnitude with vectors
    im1 = ax1.pcolormesh(x_coords, y_coords, magnitude, shading='auto', cmap='viridis')
    
    # Downsample for vectors
    skip = max(len(x_coords)//30, len(y_coords)//30)
    
    ax1.quiver(x_coords[::skip], y_coords[::skip], 
               xvel[::skip, ::skip], yvel[::skip, ::skip],
               scale=50, color='white', alpha=0.7)
    
    ax1.set_title('Velocity Magnitude with Vectors')
    fig.colorbar(im1, ax=ax1, label='Velocity magnitude')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    
    # Plot 2: Velocity magnitude contours
    im2 = ax2.contourf(x_coords, y_coords, magnitude, 
                       levels=20, cmap='viridis')
    ax2.set_title('Velocity Magnitude Contours')
    fig.colorbar(im2, ax=ax2, label='Velocity magnitude')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    
    plt.suptitle(f'State Analysis - Step {time_step}')
    
    return fig

def create_visualization(input_dir, output_dir):
    """Create both static plot and animation"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for file naming
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    vtk_files = sorted([f for f in input_dir.glob("*.vtk")])
    
    if not vtk_files:
        logger.error(f"No VTK files found in {input_dir}")
        return
    
    logger.info(f"Found {len(vtk_files)} VTK files")
    
    try:
        # Create static plot of final state with timestamp
        final_vtk = vtk_files[-1]
        magnitude, xvel, yvel, x_coords, y_coords = read_vtk_file(final_vtk)
        fig = plot_frame(magnitude, xvel, yvel, x_coords, y_coords, len(vtk_files)-1)
        fig.savefig(output_dir / f'final_state_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # Create animation with timestamp
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        def update(frame):
            ax1.clear()
            ax2.clear()
            
            magnitude, xvel, yvel, x_coords, y_coords = read_vtk_file(vtk_files[frame])
            
            # Plot 1: Velocity magnitude with vectors
            im1 = ax1.pcolormesh(x_coords, y_coords, magnitude, shading='auto', cmap='viridis')
            skip = max(len(x_coords)//30, len(y_coords)//30)
            ax1.quiver(x_coords[::skip], y_coords[::skip],
                      xvel[::skip, ::skip], yvel[::skip, ::skip],
                      scale=50, color='white', alpha=0.7)
            ax1.set_title('Velocity Magnitude with Vectors')
            
            # Plot 2: Velocity magnitude contours
            im2 = ax2.contourf(x_coords, y_coords, magnitude, levels=20, cmap='viridis')
            ax2.set_title('Velocity Magnitude Contours')
            
            plt.suptitle(f'State Analysis - Step {frame}')
            
            return im1, im2
        
        anim = FuncAnimation(fig, update, frames=len(vtk_files),
                           interval=200, blit=False)
        
        anim.save(output_dir / f'state_evolution_{timestamp}.mp4', writer='ffmpeg')
        plt.close(fig)
        
        logger.info(f"Saved visualizations with timestamp {timestamp}")
        
    except Exception as e:
        logger.error(f"Error during visualization: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create visualizations from VTK files')
    parser.add_argument('--input-dir', type=Path, default=Path('new_data'),
                      help='Directory containing VTK files')
    parser.add_argument('--output-dir', type=Path, default=Path('visualizations'),
                      help='Directory to save visualizations')
    args = parser.parse_args()
    
    logger.info(f"Reading VTK files from: {args.input_dir}")
    logger.info(f"Saving visualizations to: {args.output_dir}")
    
    create_visualization(args.input_dir, args.output_dir)