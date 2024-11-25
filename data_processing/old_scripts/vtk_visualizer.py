import numpy as np
import matplotlib.pyplot as plt
from vtk import *
import vtk.util.numpy_support as vtk_np
import glob
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloverLeafVTKReader:
    def __init__(self, directory="."):
        self.directory = directory
        self.vtk_files = self._find_vtk_files()
        
    def _find_vtk_files(self):
        """Find all VTK files in the directory"""
        pattern = os.path.join(self.directory, "*.vtk")
        files = glob.glob(pattern)
        if not files:
            logger.warning(f"No VTK files found in {self.directory}")
        else:
            logger.info(f"Found {len(files)} VTK files")
        return sorted(files)

    def read_vtk_file(self, filename):
        """Read VTK file and return all available data"""
        reader = vtkRectilinearGridReader()
        reader.SetFileName(filename)
        reader.ReadAllVectorsOn()
        reader.ReadAllScalarsOn()
        reader.Update()
        
        grid = reader.GetOutput()
        point_data = grid.GetPointData()
        
        # Get dimensions
        dims = grid.GetDimensions()
        
        # Get coordinates
        x_coords = vtk_np.vtk_to_numpy(grid.GetXCoordinates())
        y_coords = vtk_np.vtk_to_numpy(grid.GetYCoordinates())
        
        # Initialize data dictionary
        data = {
            'dimensions': dims,
            'x_coords': x_coords,
            'y_coords': y_coords
        }
        
        # Extract all arrays
        n_arrays = point_data.GetNumberOfArrays()
        logger.info(f"Found {n_arrays} arrays in {os.path.basename(filename)}")
        
        for i in range(n_arrays):
            array_name = point_data.GetArrayName(i)
            array = point_data.GetArray(i)
            if array is not None:
                array_data = vtk_np.vtk_to_numpy(array)
                logger.info(f"Reading array: {array_name} with shape {array_data.shape}")
                data[array_name] = array_data
                
        return data

    def plot_field(self, filename, field_name, output_dir="field_plots"):
        """Plot a scalar field and save to file"""
        data = self.read_vtk_file(filename)
        
        if field_name not in data:
            logger.error(f"Field {field_name} not found in file")
            logger.info(f"Available fields: {[k for k in data.keys() if k not in ['dimensions', 'x_coords', 'y_coords']]}")
            return
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Reshape data to 2D grid
        field_data = data[field_name]
        dims = data['dimensions']
        x_coords = data['x_coords']
        y_coords = data['y_coords']
        
        if len(field_data.shape) > 1:
            # Vector data - plot magnitude
            magnitude = np.sqrt(np.sum(field_data**2, axis=1))
            field_2d = magnitude.reshape((len(y_coords), len(x_coords)))
            title = f'{field_name} Magnitude'
        else:
            # Scalar data
            field_2d = field_data.reshape((len(y_coords), len(x_coords)))
            title = field_name
            
        # Create figure
        plt.figure(figsize=(12, 10))
        plt.pcolormesh(x_coords, y_coords, field_2d, shading='auto', cmap='viridis')
        plt.colorbar(label=title)
        plt.title(f'{title} - {os.path.basename(filename)}')
        plt.xlabel('X')
        plt.ylabel('Y')
        
        # Save plot
        output_file = os.path.join(output_dir, 
                                 f'{field_name}_{os.path.basename(filename)}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved {field_name} plot to {output_file}")

    def analyze_time_evolution(self, field_name, output_dir="time_evolution"):
        """Analyze how a field evolves over time"""
        os.makedirs(output_dir, exist_ok=True)
        
        max_values = []
        mean_values = []
        min_values = []
        timesteps = []
        
        for filename in self.vtk_files:
            data = self.read_vtk_file(filename)
            if field_name not in data:
                logger.error(f"Field {field_name} not found in {filename}")
                continue
                
            field_data = data[field_name]
            if len(field_data.shape) > 1:
                # Vector data - use magnitude
                values = np.sqrt(np.sum(field_data**2, axis=1))
            else:
                values = field_data
                
            max_values.append(np.max(values))
            mean_values.append(np.mean(values))
            min_values.append(np.min(values))
            
            # Extract timestep from filename
            timestep = int(filename.split('.')[-2])
            timesteps.append(timestep)
        
        # Plot time evolution
        plt.figure(figsize=(12, 6))
        plt.plot(timesteps, max_values, label='Maximum')
        plt.plot(timesteps, mean_values, label='Mean')
        plt.plot(timesteps, min_values, label='Minimum')
        plt.xlabel('Timestep')
        plt.ylabel(field_name)
        plt.title(f'{field_name} Evolution Over Time')
        plt.legend()
        plt.grid(True)
        
        output_file = os.path.join(output_dir, f'{field_name}_time_evolution.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved time evolution plot to {output_file}")

def main():
    # Initialize reader
    reader = CloverLeafVTKReader()
    
    if not reader.vtk_files:
        logger.error("No VTK files found")
        return
        
    # Read first file to get available fields
    data = reader.read_vtk_file(reader.vtk_files[0])
    available_fields = [k for k in data.keys() 
                       if k not in ['dimensions', 'x_coords', 'y_coords']]
    
    logger.info(f"Available fields: {available_fields}")
    
    # Create plots for each field at each timestep
    for field in available_fields:
        for vtk_file in reader.vtk_files:
            reader.plot_field(vtk_file, field)
        reader.analyze_time_evolution(field)
    
    logger.info("Processing complete. Check the output directories for plots.")

if __name__ == "__main__":
    main()