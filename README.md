# Intelligent File Deduplication & Storage Optimization System

## Project Overview
This project simulates enterprise-grade block-level deduplication. It optimizes storage by splitting files into smaller chunks, hashing them, and storing only unique chunks. This technology is foundational in modern cloud storage, backup systems, and high-performance storage arrays.

![System Dashboard](screenshot.png)

## Problem Statement
Traditional storage systems often store redundant data (e.g., multiple copies of the same OS image or similar document versions). This leads to wasted disk space and increased costs. Block-level deduplication identifies duplicate content even within different files, significantly reducing the physical storage footprint.

## Architecture & How it Works
1.  **Chunking**: Files are divided into fixed-size 4KB blocks.
2.  **Hashing**: Each block is processed through the **SHA-256** algorithm to generate a unique digital fingerprint.
3.  **Deduplication**: The system checks if a chunk with the same hash already exists in the `storage/` directory.
    - If it exists, only a reference is added to the metadata.
    - If it's new, the chunk is saved to disk.
4.  **Metadata Management**: A `metadata.json` file maps filenames to their constituent chunk hashes in the correct order.
5.  **Reconstruction**: To retrieve a file, the system reads the hashes from metadata and concatenates the corresponding chunks from `storage/`.

## Technologies Used
- **Python 3.x**
- **hashlib**: For SHA-256 fingerprinting.
- **json**: For metadata persistence.
- **os**: For filesystem interactions.

## How to Run

### 1. Deduplication
Place a file in the `uploads/` directory (or use any local path) and run:
```bash
python dedup.py uploads/example_file.txt
```

### 2. Reconstruction
To rebuild a previously deduplicated file:
```bash
python reconstruct.py example_file.txt
```

## Sample Test Case
1.  Create a file `file1.txt` with "Hello World" repeated many times.
2.  Run `python dedup.py file1.txt`.
3.  Duplicate `file1.txt` as `file2.txt`.
4.  Run `python dedup.py file2.txt`.
5.  **Observation**: The system will report 100% efficiency for the second file as all its chunks are already stored.

## Relevance to Enterprise Storage
In environments like Virtual Desktop Infrastructure (VDI) or massive database backups, deduplication ratios can reach 5:1 or even 20:1, saving petabytes of space and millions of dollars in infrastructure costs.

## Future Improvements
- Variable-size chunking (Content-Defined Chunking) to handle insertions/deletions better.
- Compression of stored chunks.
- Encryption for chunks at rest.
- Database-backed metadata for better performance with millions of files.
