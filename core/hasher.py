import hashlib
import os

def generate_file_hash(filepath: str, algorithm="sha256") -> str:
    """Generates a cryptographic hash for a given file to ensure forensic integrity."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    hash_obj = hashlib.new(algorithm)
    
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
            
    return hash_obj.hexdigest()

def create_custody_log(filepath: str, output_log: str):
    """Creates a basic chain of custody text file containing the original file hash."""
    file_hash = generate_file_hash(filepath)
    filename = os.path.basename(filepath)
    import datetime
    
    log_content = (
        f"Forensic Chain of Custody Log\n"
        f"=============================\n"
        f"File Name: {filename}\n"
        f"Original Path: {filepath}\n"
        f"SHA-256 Hash: {file_hash}\n"
        f"Acquired On: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
    )
    
    with open(output_log, "w") as f:
        f.write(log_content)
        
    return file_hash
