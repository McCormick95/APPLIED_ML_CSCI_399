import argparse
import subprocess
import sys
import time
from pathlib import Path
import logging
import shutil
import tarfile
from datetime import datetime
from typing import Dict, Any, Optional
from clover_vis import CloverVisualizer
from datetime import datetime
import os

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class CloverLeafRunner:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Find repository root by looking for CloverLeaf_Serial directory
            current = Path.cwd()
            while current != current.parent:
                if (current / "CloverLeaf_Serial").exists():
                    self.base_dir = current
                    break
                current = current.parent
            else:
                raise FileNotFoundError("Could not find CloverLeaf repository root")

        self.clover_dir = self.base_dir / "CloverLeaf_Serial"
        self.output_dir = self.base_dir / "data_processing/new_data"
        self.vis_dir = self.base_dir / "data_processing/visualizations"
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vis_dir.mkdir(parents=True, exist_ok=True)
        
        self.timing_data = {'simulation': 0, 'total': 0}
        
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"CloverLeaf directory: {self.clover_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        
    def generate_input(self, cells: int = 64, steps: int = 500, visit_freq: int = 2) -> None:
        input_content = f"""*clover
 state 1 density=0.2 energy=1.0
 state 2 density=1.0 energy=2.5 geometry=rectangle xmin=0.0 xmax=1.0 ymin=0.0 ymax=1.0

 x_cells={cells}
 y_cells={cells}

 xmin=0.0
 ymin=0.0
 xmax=5.0
 ymax=5.0

 initial_timestep=0.04
 timestep_rise=1.5
 max_timestep=0.04
 end_step={steps}
 test_problem 2
 
 visit_frequency={visit_freq}

*endclover
"""
        input_file = self.clover_dir / "clover.in"
        input_file.write_text(input_content)

    def build_cloverleaf(self) -> None:
        logger.info("Building CloverLeaf...")
        subprocess.run(["make", "clean"], cwd=self.clover_dir, check=True)
        subprocess.run(["make", "COMPILER=GNU"], cwd=self.clover_dir, check=True)

    def run_simulation(self) -> float:
        start_time = time.time()
        
        if not (self.clover_dir / "clover_leaf").exists():
            self.build_cloverleaf()
        
        # Redirect stdout/stderr to DEVNULL
        with open('/dev/null', 'w') as devnull:
            result = subprocess.run(["./clover_leaf"], 
                                cwd=self.clover_dir,
                                stdout=devnull,
                                stderr=devnull)

        # Only check return code
        if result.returncode != 0:
            logger.error("Simulation failed")
            sys.exit(1)
                
        return time.time() - start_time

    def process_files(self, iteration: int) -> float:
        start_time = time.time()
        
        # Setup iteration directory
        iter_dir = self.output_dir / f"iteration_{iteration}"
        iter_dir.mkdir(parents=True, exist_ok=True)
        
        # Move output files 
        for vtk_file in self.clover_dir.glob("*.vtk"):
            shutil.move(str(vtk_file), str(iter_dir / vtk_file.name))
        for output_file in ["clover.out", "clover.visit"]:
            if (self.clover_dir / output_file).exists():
                shutil.move(str(self.clover_dir / output_file), str(iter_dir / output_file))
                
        return time.time() - start_time

    def create_archive(self, iteration: int) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"clover_data_{timestamp}_{iteration:02d}.tar.gz"
        
        with tarfile.open(self.output_dir / archive_name, "w:gz") as tar:
            tar.add(self.output_dir / f"iteration_{iteration}", 
                   arcname=f"iteration_{iteration}")
        logger.info(f"Created archive: {archive_name}")

    def run_workflow(self, cells: int = 64, steps: int = 500, visit_freq: int = 1, 
                 visualize: bool = False, iteration: int = 2):
        print(f"Starting CloverLeaf workflow (iteration {iteration})...")
        total_start = time.time()
        timing_data = {}

        # Generate input and run simulation
        self.generate_input(cells, steps, visit_freq)
        print("Generated CloverLeaf input.")
        timing_data['simulation'] = self.run_simulation()
        print(f"Simulation completed in {timing_data['simulation']:.2f} seconds.")

        # Process VTK files
        timing_data['vtk_processing'] = self.process_files(iteration)
        print(f"VTK files processed in {timing_data['vtk_processing']:.2f} seconds.")

        # Process VTK files into .npy files
        visualizer = CloverVisualizer(self.output_dir / f"iteration_{iteration}", self.vis_dir)
        npy_start = time.time()
        visualizer.process_all_files()
        timing_data['npy_generation'] = time.time() - npy_start
        print(f".npy files generated in {timing_data['npy_generation']:.2f} seconds.")

        # Create timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Zip the .npy files and then delete them
        npy_dir = visualizer.npy_dir
        npy_archive_name = self.output_dir / f"npy_files_{timestamp}_iteration_{iteration}.zip"
        shutil.make_archive(npy_archive_name.with_suffix(''), 'zip', root_dir=npy_dir)
        print(f"Archived .npy files into: {npy_archive_name}")
        for npy_file in npy_dir.glob("*.npy"):
            npy_file.unlink()
        print("Deleted all .npy files after archiving.")

        # Zip the .vtk files and clover.out and leave clover.out untouched
        vtk_dir = self.output_dir / f"iteration_{iteration}"
        vtk_archive_name = self.output_dir / f"vtk_files_{timestamp}_iteration_{iteration}.zip"
        
        # Add clover.out file to the vtk directory for zipping (without removing it)
        clover_out_file = self.output_dir / "CloverLeaf_Serial" / "clover.out"
        if clover_out_file.exists():
            shutil.copy(clover_out_file, vtk_dir)  # Copy the clover.out to the vtk directory
        
        shutil.make_archive(vtk_archive_name.with_suffix(''), 'zip', root_dir=vtk_dir)
        print(f"Archived .vtk files and clover.out into: {vtk_archive_name}")
        
        # Do not delete .vtk files until after visualization is done
        if visualize:
            timing_data['visualization'] = visualizer.create_animation(variable='velocity_magnitude')
            print(f"Visualization completed in {timing_data['visualization']:.2f} seconds.")

        # Clean up by deleting .vtk files (but keep clover.out)
        for vtk_file in vtk_dir.glob("*.vtk"):
            vtk_file.unlink()
        print("Deleted all .vtk files after archiving.")

        timing_data['total'] = time.time() - total_start
        return timing_data

def main():
    parser = argparse.ArgumentParser(description='CloverLeaf Workflow Runner')
    parser.add_argument('--cells', type=int, default=64,
                       help='Number of cells in x and y (default: 64)')
    parser.add_argument('--steps', type=int, default=500,
                       help='Number of timesteps (default: 500)')
    parser.add_argument('--visit-freq', type=int, default=1,
                       help='Frequency of VTK file generation (default: 1)')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate visualizations (optional)')
    parser.add_argument('--base-dir', type=str, default=None,
                       help='Base directory for CloverLeaf project')
    args = parser.parse_args()

    runner = CloverLeafRunner(args.base_dir)
    timing_data = runner.run_workflow(args.cells, args.steps, args.visit_freq, args.visualize)

    print("\nTiming Summary:")
    print(f"Simulation Time: {timing_data['simulation']:.2f} seconds")
    print(f"VTK Processing Time: {timing_data['vtk_processing']:.2f} seconds")
    print(f"NPY Generation Time: {timing_data['npy_generation']:.2f} seconds")
    if args.visualize:
        print(f"Visualization Time: {timing_data['visualization']:.2f} seconds")
    print(f"Total Time: {timing_data['total']:.2f} seconds")


if __name__ == "__main__":
    main()