import os
import hashlib
import json
import sys

# Configuration
CHUNK_SIZE = 4096  # 4KB
STORAGE_DIR = "storage"
METADATA_FILE = "metadata.json"

def ensure_directories():
    """Ensure required directories exist."""
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def get_file_hash(data):
    """Calculate SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()

def load_metadata():
    """Load metadata from JSON file."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_metadata(metadata):
    """Save metadata to JSON file."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)

def deduplicate_file(file_path):
    """Chunk file, hash chunks, and store unique chunks."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    filename = os.path.basename(file_path)
    metadata = load_metadata()

    if filename in metadata:
        print(f"File '{filename}' has already been processed. Skipping.")
        return

    ensure_directories()
    
    chunk_hashes = []
    logical_size = 0
    
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                logical_size += len(chunk)
                chunk_hash = get_file_hash(chunk)
                chunk_hashes.append(chunk_hash)
                
                chunk_path = os.path.join(STORAGE_DIR, chunk_hash)
                if not os.path.exists(chunk_path):
                    with open(chunk_path, 'wb') as chunk_file:
                        chunk_file.write(chunk)
        
        metadata[filename] = chunk_hashes
        save_metadata(metadata)
        
        print(f"Successfully processed '{filename}'.")
        display_stats(metadata)
        
    except IOError as e:
        print(f"Error reading file: {e}")

def display_stats(metadata):
    """Calculate and display deduplication statistics."""
    total_logical_size = 0
    for filename, hashes in metadata.items():
        # Note: This is an approximation as we don't store individual chunk sizes in metadata
        # for this simple version, but we know most are CHUNK_SIZE.
        # A more accurate way would be to track the size of each file during dedup.
        total_logical_size += len(hashes) * CHUNK_SIZE 

    # Calculate actual storage size
    actual_storage_size = 0
    if os.path.exists(STORAGE_DIR):
        for chunk_name in os.listdir(STORAGE_DIR):
            actual_storage_size += os.path.getsize(os.path.join(STORAGE_DIR, chunk_name))

    saved_space = total_logical_size - actual_storage_size
    
    print("\n--- Storage Optimization Report ---")
    print(f"Total Logical Data Size: {total_logical_size / 1024:.2f} KB")
    print(f"Actual Stored Size:     {actual_storage_size / 1024:.2f} KB")
    print(f"Space Saved:            {saved_space / 1024:.2f} KB")
    if total_logical_size > 0:
        print(f"Efficiency:             {(saved_space / total_logical_size) * 100:.2f}%")
    print("-----------------------------------\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dedup.py <file_path>")
    else:
        deduplicate_file(sys.argv[1])
