import numpy as np
import matplotlib.pyplot as plt
from vtk import *
import vtk.util.numpy_support as vtk_np
import glob
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloverLeafFinalStateAnalyzer:
    def __init__(self, directory="."):
        self.directory = directory
        self.vtk_files = self._find_vtk_files()
        
    def _find_vtk_files(self):
        """Find all VTK files and return sorted by timestep"""
        pattern = os.path.join(self.directory, "*.vtk")
        files = glob.glob(pattern)
        return sorted(files, key=lambda x: int(x.split('.')[-2]))
    
    def get_final_state(self):
        """Get the last timestep file"""
        if not self.vtk_files:
            raise FileNotFoundError("No VTK files found")
        return self.vtk_files[-1]
    
    def read_vector_data(self, filename):
        """Read velocity components from VTK file"""
        reader = vtkRectilinearGridReader()
        reader.SetFileName(filename)
        reader.ReadAllVectorsOn()
        reader.ReadAllScalarsOn()
        reader.Update()
        
        grid = reader.GetOutput()
        point_data = grid.GetPointData()
        
        # Get dimensions and coordinates
        dims = grid.GetDimensions()
        x_coords = vtk_np.vtk_to_numpy(grid.GetXCoordinates())
        y_coords = vtk_np.vtk_to_numpy(grid.GetYCoordinates())
        
        # Get velocity components
        xvel = None
        yvel = None
        
        n_arrays = point_data.GetNumberOfArrays()
        logger.info(f"Found {n_arrays} arrays in the data")
        
        for i in range(n_arrays):
            array_name = point_data.GetArrayName(i)
            logger.info(f"Found array: {array_name}")
            if array_name == 'x_vel':
                xvel = vtk_np.vtk_to_numpy(point_data.GetArray(i))
            elif array_name == 'y_vel':
                yvel = vtk_np.vtk_to_numpy(point_data.GetArray(i))
        
        return x_coords, y_coords, xvel, yvel, dims

    def plot_final_state_velocity(self, output_file='final_state_velocity.png'):
        """Create combined vector field plot of the final state"""
        final_file = self.get_final_state()
        logger.info(f"Analyzing final state from: {os.path.basename(final_file)}")
        
        x_coords, y_coords, xvel, yvel, dims = self.read_vector_data(final_file)
        
        if xvel is None or yvel is None:
            logger.error("Velocity data not found in file")
            return
        
        # Create regular grid for plotting
        nx = len(x_coords)
        ny = len(y_coords)
        
        # Reshape velocity components
        u = xvel.reshape((ny, nx))
        v = yvel.reshape((ny, nx))
        
        # Calculate magnitude
        magnitude = np.sqrt(u**2 + v**2)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        # Plot 1: Velocity magnitude as background with vector overlay
        im1 = ax1.pcolormesh(x_coords, y_coords, magnitude, shading='auto', cmap='viridis')
        
        # Downsample for vector plot
        skip = max(nx//30, ny//30)  # Adjust this value to change vector density
        
        # Create vectors on a regular grid
        x_sub = x_coords[::skip]
        y_sub = y_coords[::skip]
        u_sub = u[::skip, ::skip]
        v_sub = v[::skip, ::skip]
        
        # Plot vectors
        ax1.quiver(x_sub, y_sub, u_sub, v_sub, 
                  scale=50,  # Adjust this value to change arrow size
                  color='white',
                  alpha=0.7)
        
        ax1.set_title('Velocity Magnitude with Vectors')
        fig.colorbar(im1, ax=ax1, label='Velocity magnitude')
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        
        # Plot 2: Velocity magnitude contour
        im2 = ax2.contourf(x_coords, y_coords, magnitude, 
                          levels=20, cmap='viridis')
        ax2.set_title('Velocity Magnitude Contours')
        fig.colorbar(im2, ax=ax2, label='Velocity magnitude')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        
        plt.suptitle(f'Final State Velocity Analysis\n{os.path.basename(final_file)}')
        
        # Save figure
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved final state visualization to {output_file}")
        
        # Print statistics
        logger.info("\nFinal State Statistics:")
        logger.info(f"Maximum velocity magnitude: {np.max(magnitude):.4f}")
        logger.info(f"Average velocity magnitude: {np.mean(magnitude):.4f}")
        logger.info(f"Minimum velocity magnitude: {np.min(magnitude):.4f}")
        
        # Create velocity magnitude histogram
        plt.figure(figsize=(10, 6))
        plt.hist(magnitude.flatten(), bins=50, density=True)
        plt.title('Distribution of Velocity Magnitudes in Final State')
        plt.xlabel('Velocity Magnitude')
        plt.ylabel('Density')
        plt.savefig('final_state_velocity_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return magnitude

def main():
    analyzer = CloverLeafFinalStateAnalyzer()
    
    try:
        magnitude = analyzer.plot_final_state_velocity()
        
    except Exception as e:
        logger.error(f"Error processing final state: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()