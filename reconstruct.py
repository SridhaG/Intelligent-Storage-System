import os
import json
import sys

# Configuration
STORAGE_DIR = "storage"
METADATA_FILE = "metadata.json"

def load_metadata():
    """Load metadata from JSON file."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def reconstruct_file(target_filename):
    """Reconstruct the original file from stored chunks."""
    metadata = load_metadata()
    
    if target_filename not in metadata:
        print(f"Error: No metadata found for '{target_filename}'.")
        return

    chunk_hashes = metadata[target_filename]
    output_path = os.path.join("reconstructed_" + target_filename)
    
    print(f"Reconstructing '{target_filename}'...")
    
    try:
        with open(output_path, 'wb') as out_file:
            for chunk_hash in chunk_hashes:
                chunk_path = os.path.join(STORAGE_DIR, chunk_hash)
                
                if not os.path.exists(chunk_path):
                    print(f"Critical Error: Chunk {chunk_hash} missing! Reconstruction failed.")
                    out_file.close()
                    os.remove(output_path)
                    return
                
                with open(chunk_path, 'rb') as chunk_file:
                    out_file.write(chunk_file.read())
                    
        print(f"Success! File reconstructed as '{output_path}'.")
        
    except IOError as e:
        print(f"Error writing reconstructed file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reconstruct.py <filename>")
    else:
        reconstruct_file(sys.argv[1])
