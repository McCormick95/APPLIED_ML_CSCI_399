import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import vtk
from vtk.util import numpy_support
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloverLeafVisualizer:
    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def read_vtk_file(self, filename):
        """Read density data from VTK file"""
        try:
            logger.info(f"Reading file: {filename}")
            
            reader = vtk.vtkRectilinearGridReader()
            reader.SetFileName(str(filename))
            reader.ReadAllScalarsOn()
            reader.Update()
            
            data = reader.GetOutput()
            point_data = data.GetPointData()
            
            # Get dimensions and coordinates
            x_coords = numpy_support.vtk_to_numpy(data.GetXCoordinates())
            y_coords = numpy_support.vtk_to_numpy(data.GetYCoordinates())
            
            # Log available arrays
            n_arrays = point_data.GetNumberOfArrays()
            logger.info(f"Available arrays:")
            for i in range(n_arrays):
                logger.info(f"  {point_data.GetArrayName(i)}")
            
            # Get velocity data and calculate magnitude
            xvel = numpy_support.vtk_to_numpy(point_data.GetArray('x_vel'))
            yvel = numpy_support.vtk_to_numpy(point_data.GetArray('y_vel'))
            
            # Reshape arrays
            nx = len(x_coords)
            ny = len(y_coords)
            xvel = xvel.reshape((ny, nx))
            yvel = yvel.reshape((ny, nx))
            
            # Calculate velocity magnitude
            magnitude = np.sqrt(xvel**2 + yvel**2)
            
            return magnitude, x_coords, y_coords
            
        except Exception as e:
            logger.error(f"Error reading VTK file: {str(e)}")
            raise

    def create_animation(self):
        """Create clean contour animation"""
        vtk_files = sorted(list(self.input_dir.glob("*.vtk")))
        
        if not vtk_files:
            logger.error(f"No VTK files found in {self.input_dir}")
            return
            
        logger.info(f"Found {len(vtk_files)} VTK files")
        
        # Set up figure with no margins or padding
        fig = plt.figure(figsize=(10, 10))
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        
        # Read first frame to get dimensions
        magnitude, x, y = self.read_vtk_file(vtk_files[0])
        
        def update(frame):
            ax.clear()
            ax.set_axis_off()
            
            magnitude, x, y = self.read_vtk_file(vtk_files[frame])
            
            # Create contour plot without any extra elements
            ax.contourf(x, y, magnitude, levels=20, cmap='viridis')
            
            # Remove all spacing and borders
            plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
            plt.margins(0,0)
            ax.xaxis.set_major_locator(plt.NullLocator())
            ax.yaxis.set_major_locator(plt.NullLocator())
        
        logger.info("Creating animation...")
        anim = FuncAnimation(fig, update, frames=len(vtk_files),
                           interval=200, blit=False)
        
        # Save with minimal encoding settings
        output_file = self.output_dir / 'fluid_interaction.mp4'
        logger.info(f"Saving animation to {output_file}")
        anim.save(output_file,
                 writer='ffmpeg', dpi=300,
                 savefig_kwargs={'pad_inches': 0, 'bbox_inches': 'tight'},
                 extra_args=['-vcodec', 'libx264'])
        
        plt.close(fig)
        logger.info("Animation complete")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean CloverLeaf fluid visualization')
    parser.add_argument('--input-dir', type=str, default='new_data',
                      help='Directory containing VTK files')
    parser.add_argument('--output-dir', type=str, default='visualizations',
                      help='Directory to save visualization')
    
    args = parser.parse_args()
    
    visualizer = CloverLeafVisualizer(args.input_dir, args.output_dir)
    visualizer.create_animation()