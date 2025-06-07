"""
Environment setup, logging, and checkpoint management utilities.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, Optional

from business_validator.config import DATA_DIR, LOG_DIR

def setup_environment(business_idea: str) -> Dict[str, str]:
    """Setup logging and data directories for the current run.
    
    Args:
        business_idea: The business idea being validated
        
    Returns:
        Dictionary with run_id, data_dir, and log_file paths
    """
    # Create a timestamp for this run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a safe version of the business idea for filenames
    safe_idea = "".join(c if c.isalnum() else "_" for c in business_idea[:30]).strip("_")
    
    # Create run ID
    run_id = f"{safe_idea}_{timestamp}"
    
    # Create directories
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Create run-specific directories
    run_data_dir = os.path.join(DATA_DIR, run_id)
    os.makedirs(run_data_dir, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join(LOG_DIR, f"{run_id}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Starting validation for business idea: {business_idea}")
    logging.info(f"Run ID: {run_id}")
    
    return {
        "run_id": run_id,
        "data_dir": run_data_dir,
        "log_file": log_file
    }

def save_checkpoint(data: Any, filename: str, data_dir: str) -> str:
    """Save data to a checkpoint file.
    
    Args:
        data: The data to save (can be a dict or Pydantic model)
        filename: The name of the checkpoint file
        data_dir: The directory to save the file in
        
    Returns:
        The full path to the saved file, or empty string on error
    """
    filepath = os.path.join(data_dir, filename)
    
    # Convert Pydantic models to dict if needed
    if hasattr(data, "dict"):
        data = data.dict()
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Checkpoint saved: {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error saving checkpoint {filepath}: {e}")
        return ""

def load_checkpoint(filename: str, data_dir: str) -> Optional[Dict]:
    """Load data from a checkpoint file.
    
    Args:
        filename: The name of the checkpoint file
        data_dir: The directory to load the file from
        
    Returns:
        The loaded data as a dictionary, or None on error
    """
    filepath = os.path.join(data_dir, filename)
    
    if not os.path.exists(filepath):
        logging.warning(f"Checkpoint file not found: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.info(f"Checkpoint loaded: {filepath}")
        return data
    except Exception as e:
        logging.error(f"Error loading checkpoint {filepath}: {e}")
        return None
