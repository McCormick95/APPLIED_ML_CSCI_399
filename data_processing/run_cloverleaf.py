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
import json

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

    def _filter_input_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter parameters to only include those used in generate_input."""
        input_params = {
            'cells', 'steps', 'visit_freq',
            'state1_density', 'state1_energy',
            'state2_density', 'state2_energy',
            'state2_xmin', 'state2_xmax',
            'state2_ymin', 'state2_ymax',
            'xmin', 'xmax', 'ymin', 'ymax',
            'initial_timestep', 'timestep_rise', 'max_timestep'
        }
        return {k: v for k, v in params.items() if k in input_params}
        
    def generate_input(self, 
                  cells: int = 64,
                  steps: int = 500, 
                  visit_freq: int = 1,
                  # State parameters
                  state1_density: float = 0.2,
                  state1_energy: float = 1.0,
                  state2_density: float = 1.0,
                  state2_energy: float = 2.5,
                  # State 2 geometry
                  state2_xmin: float = 0.0,
                  state2_xmax: float = 1.0,
                  state2_ymin: float = 0.0,
                  state2_ymax: float = 1.0,
                  # Overall geometry
                  xmin: float = 0.0,
                  xmax: float = 5.0,
                  ymin: float = 0.0,
                  ymax: float = 5.0,
                  # Timestep parameters
                  initial_timestep: float = 0.04,
                  timestep_rise: float = 1.5,
                  max_timestep: float = 0.04
                  ) -> None:
        input_content = f"""*clover
 state 1 density={state1_density} energy={state1_energy}
 state 2 density={state2_density} energy={state2_energy} geometry=rectangle xmin={state2_xmin} xmax={state2_xmax} ymin={state2_ymin} ymax={state2_ymax}

 x_cells={cells}
 y_cells={cells}

 xmin={xmin}
 ymin={ymin}
 xmax={xmax}
 ymax={ymax}

 initial_timestep={initial_timestep}
 timestep_rise={timestep_rise}
 max_timestep={max_timestep}
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

    def create_archive(self, param_str: str, iteration: int) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"clover_data_{param_str}_{timestamp}_{iteration:02d}.tar.gz"
        
        with tarfile.open(self.output_dir / archive_name, "w:gz") as tar:
            tar.add(self.output_dir / f"iteration_{param_str}_{iteration}", 
                arcname=f"iteration_{param_str}_{iteration}")
        logger.info(f"Created archive: {archive_name}")

    def cleanup(self) -> None:
        """Clean the CloverLeaf directory after running simulations."""
        logger.info("Cleaning CloverLeaf directory...")
        try:
            subprocess.run(["make", "clean"], cwd=self.clover_dir, check=True)
            logger.info("Successfully cleaned CloverLeaf directory")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clean CloverLeaf directory: {e}")

    def run_workflow(self, cells: int = 64, steps: int = 500, visit_freq: int = 1, 
                visualize: bool = False, iteration: int = 1, **params):
        total_start = time.time()
        
        # Filter parameters for generate_input
        input_params = self._filter_input_params(params)
        
        # Create parameter string for file naming
        param_str = f"c{cells}_s{steps}_d1{params.get('state1_density', 0.2):.1f}_" \
                    f"d2{params.get('state2_density', 1.0):.1f}_e1{params.get('state1_energy', 1.0):.1f}_" \
                    f"e2{params.get('state2_energy', 2.5):.1f}"
        
        # Setup directories
        iter_dir = self.output_dir / f"iteration_{param_str}_{iteration}"
        iter_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate input and run simulation
        logger.info(f"Starting simulation with parameters: {param_str}")
        logger.info(f"Output directory: {iter_dir}")
        
        sim_start = time.time()
        self.generate_input(cells, steps, visit_freq, **input_params)
        sim_time = self.run_simulation()
        sim_end = time.time()
        self.timing_data['simulation'] = sim_end - sim_start
        
        # Process files
        process_start = time.time()
        self.process_files(iteration)
        process_end = time.time()
        self.timing_data['processing'] = process_end - process_start
        
        # Create archive with parameter string
        self.create_archive(param_str, iteration)
        
        self.timing_data['total'] = time.time() - total_start
        
        # Save run configuration and timing data
        config_data = {
            'parameters': {
                'cells': cells,
                'steps': steps,
                'visit_freq': visit_freq,
                **params
            },
            'timing': self.timing_data,
            'timestamp': datetime.now().isoformat(),
            'output_dir': str(iter_dir)
        }
        
        with open(iter_dir / 'run_config.json', 'w') as f:
            json.dump(config_data, f, indent=4)
        
        return self.timing_data

def main():
    parser = argparse.ArgumentParser(description='CloverLeaf Workflow Runner')
    # Core arguments
    parser.add_argument('--cells', type=int, default=64,
                       help='Number of cells in x and y (default: 64)')
    parser.add_argument('--steps', type=int, default=500,
                       help='Number of timesteps (default: 500)')
    parser.add_argument('--visit-freq', type=int, default=1,
                       help='Frequency of VTK file generation (default: 1)')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate visualizations')
    parser.add_argument('--base-dir', type=str, default=None,
                       help='Base directory for CloverLeaf project')
    parser.add_argument('--cleanup', action='store_true', default=False,
                       help='Clean the CloverLeaf directory after running')

    args = parser.parse_args()
    
    runner = CloverLeafRunner(args.base_dir)
    
    # Convert args to dict for additional parameters
    params = vars(args)
    
    # Store cleanup value before removing from params
    should_cleanup = params.pop('cleanup', False)
    
    # Remove non-workflow parameters
    params.pop('base_dir', None)
    
    timing_data = runner.run_workflow(**params)

    if should_cleanup:
        runner.cleanup()

if __name__ == "__main__":
    main()