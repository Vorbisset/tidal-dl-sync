import sys
import os
import subprocess
import hashlib
from tqdm import tqdm
import time

def read_urls(file_path):
    urls_with_comments = []
    current_comment = None
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#'):
                current_comment = line[1:].strip()
            elif line.startswith('https'):
                urls_with_comments.append((line, current_comment))
                current_comment = None
    return urls_with_comments

def hash_file(filepath):
    """Returns the MD5 hash of the file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_files(directory):
    """Returns a dictionary of files and their hashes in the given directory."""
    files = {}
    file_list = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            file_list.append(filepath)

    for filepath in tqdm(file_list, desc="Checking files", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}"):
        files[filepath] = hash_file(filepath)
    
    return files

def compare_files(before, after):
    """Compares two dictionaries of files and returns the differences."""
    added = {k: after[k] for k in set(after) - set(before)}
    removed = {k: before[k] for k in set(before) - set(after)}
    modified = {k: after[k] for k in set(after) & set(before) if before[k] != after[k]}
    return added, removed, modified

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 auto-dl-2.py <list_with_URL_playlists>")
        sys.exit(1)

    file_path = sys.argv[1]
    urls_with_comments = read_urls(file_path)
    directory_to_watch = '<YOUR PLAYLIST PATH (same that tidal-dl config)>'

    # Step 1: Control the initial state of the directory
    print("Checking initial state of the directory...")
    initial_files = get_files(directory_to_watch)

    for url, comment in urls_with_comments:
        if comment:
            print(f"Playlist name: {comment}")
        print(f"Processing {url}")
        command = ['tidal-dl', '--link', url]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Create a progress bar for download
        with tqdm(total=100, desc=url, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
            while process.poll() is None:
                # Update the progress bar every 0.5 seconds
                time.sleep(0.5)
                pbar.update(5)
            # Ensure the bar completes
            pbar.update(100 - pbar.n)

        # Check the exit code of the process
        process.wait()
        if process.returncode == 0:
            print(f"Successfully downloaded {comment}\n")
        else:
            print(f"Failed to download {comment}\n")

    # Step 2: Control the state of the directory after the download
    print("Checking state of the directory after download...")
    final_files = get_files(directory_to_watch)

    # Step 3: Compare the states and output the differences
    added, removed, modified = compare_files(initial_files, final_files)

    print("\nChanges detected:")
    print("Added files:")
    for filepath in added:
        print(f"  {filepath}")

    print("Removed files:")
    for filepath in removed:
        print(f"  {filepath}")

    print("Modified files:")
    for filepath in modified:
        print(f"  {filepath}")

if __name__ == "__main__":
    main()
