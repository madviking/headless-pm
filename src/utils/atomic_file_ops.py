"""
Atomic file operations utility for safe concurrent file updates.
Uses standard library only - no external dependencies.
"""
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar
import fasteners

T = TypeVar('T')


class AtomicFileOperations:
    """Provides atomic file operations using tempfile + rename pattern."""
    
    @staticmethod
    def atomic_json_update(file_path: Path, update_func: Callable[[Dict], Dict], 
                          default_data: Optional[Dict] = None) -> Dict:
        """
        Atomically update a JSON file using a file lock and a tempfile + rename pattern.
        This ensures both the read-modify-write cycle and the write operation itself are safe.
        """
        # Use fasteners for robust inter-process locking with automatic crash recovery
        lock_path = file_path.parent / f"{file_path.name}.lock"
        lock = fasteners.InterProcessLock(lock_path)
        
        with lock:
            # Read current data safely
            current_data = AtomicFileOperations._read_json_safe(file_path, default_data or {})
            
            # Apply update function
            updated_data = update_func(current_data.copy())
            
            # Write atomically using tempfile + rename
            return AtomicFileOperations._write_json_atomic(file_path, updated_data)
    
    @staticmethod
    def _read_json_safe(file_path: Path, default: Dict) -> Dict:
        """Safely read JSON file with fallback to default."""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return default
    
    @staticmethod
    def _write_json_atomic(file_path: Path, data: Dict) -> Dict:
        """Atomically write JSON data using tempfile + rename."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file in same directory for atomic rename
        with tempfile.NamedTemporaryFile(
            mode='w', 
            delete=False,
            dir=file_path.parent,
            suffix='.tmp',
            prefix=f"{file_path.name}."
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())  # Ensure data is written to disk
            tmp_path = tmp.name
        
        # Atomic rename - this is the key operation that prevents races
        try:
            os.rename(tmp_path, file_path)
            return data
        except OSError:
            # Clean up temp file if rename failed
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


# Custom ProcessCoordinationLock replaced with fasteners.InterProcessLock
# for battle-tested, OS-native inter-process locking with automatic crash recovery


# Convenience function using fasteners.InterProcessLock
def with_coordination_lock(lock_name: str, operation: Callable[[], T], 
                          timeout: int = 10, client_id: str = None) -> Optional[T]:
    """
    Execute operation with coordination lock protection using fasteners.
    
    Args:
        lock_name: Unique lock identifier
        operation: Function to execute while holding lock
        timeout: Lock acquisition timeout (used with fasteners)
        client_id: Client identifier for debugging
        
    Returns:
        Result of operation, or None if lock acquisition failed
    """
    lock_path = Path("/tmp") / f"{lock_name}.lock"
    lock = fasteners.InterProcessLock(lock_path)
    
    try:
        with lock:
            return operation()
    except Exception:
        return None  # Lock acquisition failed or operation failed