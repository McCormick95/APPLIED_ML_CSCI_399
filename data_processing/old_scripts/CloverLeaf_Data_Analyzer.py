import numpy as np
import matplotlib.pyplot as plt
from vtk import *
import vtk.util.numpy_support as vtk_np
import glob
import os
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloverLeafAnalyzer:
    def __init__(self, directory="."):
        self.directory = directory
        self.vtk_files = self._find_vtk_files()
        self.output_data = self._parse_output_file()
        
    # [UPDATED METHOD]
    def _find_vtk_files(self):
        """Find all VTK files and sort them by timestep"""
        pattern = os.path.join(self.directory, "*.vtk")
        files = glob.glob(pattern)
        
        def get_timestep(filename):
            parts = filename.split('.')
            if len(parts) >= 5:  # Ensure we have all parts
                try:
                    return int(parts[-2])  # Get the timestep number
                except ValueError:
                    return 0
            return 0
        
        return sorted(files, key=get_timestep)
    
    def _parse_output_file(self, filename="clover.out"):
        """Parse the clover.out file for timestep data"""
        timestep_data = {}
        try:
            with open(filename, 'r') as f:
                content = f.read()
                
            # Find all timestep data blocks
            pattern = r"Time\s+(\d+\.\d+)\s+Volume\s+Mass\s+Density\s+Pressure\s+Internal Energy\s+Kinetic Energy\s+Total Energy\s+step:\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)"
            matches = re.finditer(pattern, content)
            
            for match in matches:
                time = float(match.group(1))
                step = int(match.group(2))
                timestep_data[step] = {
                    'time': time,
                    'volume': float(match.group(3)),
                    'mass': float(match.group(4)),
                    'density': float(match.group(5)),
                    'pressure': float(match.group(6)),
                    'internal_energy': float(match.group(7)),
                    'kinetic_energy': float(match.group(8)),
                    'total_energy': float(match.group(9))
                }
                
            logger.info(f"Parsed {len(timestep_data)} timesteps from output file")
            return timestep_data
            
        except Exception as e:
            logger.error(f"Error parsing output file: {str(e)}")
            return {}

    def read_vtk_data(self, filename):
        """Read all data from VTK file"""
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
        
        data = {
            'x_coords': x_coords,
            'y_coords': y_coords,
            'dims': dims
        }
        
        # Extract all arrays
        n_arrays = point_data.GetNumberOfArrays()
        for i in range(n_arrays):
            array_name = point_data.GetArrayName(i)
            array_data = vtk_np.vtk_to_numpy(point_data.GetArray(i))
            data[array_name] = array_data
            
        return data

    # [UPDATED METHOD]
    def create_combined_plot(self, timestep, output_dir="combined_plots"):
        """Create a combined visualization for a specific timestep"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Modified file matching logic
        vtk_file = None
        timestep_str = f"{timestep:05d}"
        for file in self.vtk_files:
            parts = file.split('.')
            if len(parts) >= 5 and parts[-2] == timestep_str:
                vtk_file = file
                break
                    
        if vtk_file is None:
            logger.error(f"No VTK file found for timestep {timestep}")
            return
                
        # Read VTK data
        data = self.read_vtk_data(vtk_file)
        logger.info(f"Keys in data dictionary: {list(data.keys())}")
        
        # Get output file data for this timestep
        output_data = self.output_data.get(timestep, {})
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 15))
        gs = plt.GridSpec(3, 2)
        
        # Plot 1: Velocity vectors with density background instead of pressure
        ax1 = fig.add_subplot(gs[0, :])
        
        # Reshape velocity components and density
        nx = len(data['x_coords'])
        ny = len(data['y_coords'])
        u = data['x_vel'].reshape((ny, nx))
        v = data['y_vel'].reshape((ny, nx))
        
        # Use density as background if pressure is not available
        background = data.get('pressure', data.get('density0')).reshape((ny, nx))
        background_name = 'Pressure' if 'pressure' in data else 'Density'
        
        # Plot background
        im1 = ax1.pcolormesh(data['x_coords'], data['y_coords'], 
                            background, shading='auto', cmap='viridis')
        
        # Add velocity vectors
        skip = max(nx//30, ny//30)
        x_sub = data['x_coords'][::skip]
        y_sub = data['y_coords'][::skip]
        u_sub = u[::skip, ::skip]
        v_sub = v[::skip, ::skip]
        
        ax1.quiver(x_sub, y_sub, u_sub, v_sub, 
                  scale=50, color='white', alpha=0.7)
        
        ax1.set_title('Pressure Field with Velocity Vectors')
        fig.colorbar(im1, ax=ax1, label='Pressure')
        
        # Plot 2: Energy distribution
        ax2 = fig.add_subplot(gs[1, 0])
        energy = data['energy0'].reshape((ny, nx))
        im2 = ax2.pcolormesh(data['x_coords'], data['y_coords'], 
                            energy, shading='auto', cmap='plasma')
        ax2.set_title('Internal Energy Distribution')
        fig.colorbar(im2, ax=ax2, label='Energy')
        
        # Plot 3: Density distribution
        ax3 = fig.add_subplot(gs[1, 1])
        density = data['density0'].reshape((ny, nx))
        im3 = ax3.pcolormesh(data['x_coords'], data['y_coords'], 
                            density, shading='auto', cmap='magma')
        ax3.set_title('Density Distribution')
        fig.colorbar(im3, ax=ax3, label='Density')
        
        # Plot 4: Energy evolution
        ax4 = fig.add_subplot(gs[2, :])
        timesteps = sorted(self.output_data.keys())
        times = [self.output_data[t]['time'] for t in timesteps]
        internal_energy = [self.output_data[t]['internal_energy'] for t in timesteps]
        kinetic_energy = [self.output_data[t]['kinetic_energy'] for t in timesteps]
        total_energy = [self.output_data[t]['total_energy'] for t in timesteps]
        
        ax4.plot(times, internal_energy, label='Internal Energy', marker='o')
        ax4.plot(times, kinetic_energy, label='Kinetic Energy', marker='s')
        ax4.plot(times, total_energy, label='Total Energy', marker='^')
        ax4.set_xlabel('Time')
        ax4.set_ylabel('Energy')
        ax4.set_title('Energy Evolution')
        ax4.grid(True)
        ax4.legend()
        
        # Add current timestep indicator
        if timestep in self.output_data:
            current_time = self.output_data[timestep]['time']
            ax4.axvline(x=current_time, color='r', linestyle='--', 
                       label=f'Current time: {current_time:.4f}')
            
        plt.tight_layout()
        
        # Save figure
        output_file = os.path.join(output_dir, f'combined_plot_{timestep:06d}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved combined plot for timestep {timestep} to {output_file}")

    def create_animation_frames(self):
        """Create plots for all timesteps"""
        for timestep in sorted(self.output_data.keys()):
            self.create_combined_plot(timestep)

def main():
    analyzer = CloverLeafAnalyzer()
    analyzer.create_animation_frames()

if __name__ == "__main__":
    main()