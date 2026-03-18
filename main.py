"""Main entry point and example usage."""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run basic example simulation."""
    from src.simulation import SimulationEngine
    from src.config import SimulationConfig
    
    logger.info("=== AI Labor Market Simulation ===")
    
    # Create default configuration
    config = SimulationConfig()
    logger.info(f"Configuration: {config.num_firms} firms, "
                f"{config.initial_human_workers} workers, "
                f"{config.simulation_periods} periods")
    
    # Initialize engine
    logger.info("Initializing simulation engine...")
    engine = SimulationEngine(config)
    
    # Run simulation
    logger.info("Running simulation...")
    results_df = engine.run()
    
    # Display results
    logger.info(f"\nSimulation Results ({len(results_df)} periods):")
    print(results_df.head(10))
    
    # Export
    output_path = Path(__file__).parent / "outputs" / "results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"\nResults saved to {output_path}")
    
    return results_df


if __name__ == "__main__":
    try:
        results = main()
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        sys.exit(1)
