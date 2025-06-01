# utils.py - Cleaned version

import json
import time

def safe_value(val):
    """Convert various data types to string format suitable for spreadsheets."""
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    elif val is None:
        return ""
    else:
        return str(val)

class Timer:
    """Simple timer for performance measurement."""
    def __init__(self, name="Operation"):
        self.name = name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        print(f"✅ {self.name} completed in {elapsed:.2f} seconds")