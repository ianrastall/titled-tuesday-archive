# generate_tt_metadata.py
import os
import shutil
from pathlib import Path

def generate_tt_links(github_repo_dir, output_file):
    """Generate tt_links.txt with GitHub raw URLs for ZIP files."""
    repo_path = Path(github_repo_dir)
    base_url = "https://github.com/ianrastall/titled-tuesday-archive/raw/main"
    
    links = []
    
    # Walk through all ZIP files in the repo
    zip_files = list(repo_path.glob('**/*.zip'))
    print(f"Found {len(zip_files)} ZIP files in {repo_path}")
    
    for zip_file in sorted(zip_files):
        # Get relative path from repo root
        rel_path = zip_file.relative_to(repo_path)
        url = f"{base_url}/{rel_path}"
        links.append(url)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(link + '\n')
    
    print(f"Generated {output_file} with {len(links)} links")
    return len(links)

def generate_tt_events_txt(pgn_dir, output_file):
    """Generate tt_events.txt by reading Event tags from PGNs."""
    pgn_path = Path(pgn_dir)
    
    # Check if directory exists
    if not pgn_path.exists():
        print(f"ERROR: Directory does not exist: {pgn_path}")
        return 0
    
    events = []
    
    # Process all PGN files recursively
    pgn_files = list(pgn_path.glob('**/*.pgn'))
    print(f"Found {len(pgn_files)} PGN files in {pgn_path}")
    
    for pgn_file in sorted(pgn_files):
        filename = pgn_file.name
        print(f"  Processing: {filename}")
        try:
            # Read the file to find Event tag
            with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
                event_found = False
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith('[Event "') and not stripped_line.startswith('[EventDate'):
                        # Extract event name
                        start = stripped_line.find('"') + 1
                        end = stripped_line.rfind('"')
                        if start > 0 and end > start:
                            event_name = stripped_line[start:end]
                            events.append(f"{filename}: {event_name}")
                        else:
                            events.append(f"{filename}: {stripped_line}")
                        event_found = True
                        break
                
                if not event_found:
                    events.append(f"{filename}: No Event tag found")
                    
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            events.append(f"{filename}: Error reading file")
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for event in events:
            f.write(event + '\n')
    
    print(f"Generated {output_file} with {len(events)} events")
    return len(events)

def generate_tt_game_counts_txt(pgn_dir, output_file):
    """Generate tt_game_counts.txt by counting games in PGNs."""
    pgn_path = Path(pgn_dir)
    
    # Check if directory exists
    if not pgn_path.exists():
        print(f"ERROR: Directory does not exist: {pgn_path}")
        return 0
    
    counts = []
    
    # Process all PGN files recursively
    pgn_files = list(pgn_path.glob('**/*.pgn'))
    print(f"Found {len(pgn_files)} PGN files in {pgn_path}")
    
    for pgn_file in sorted(pgn_files):
        filename = pgn_file.name
        print(f"  Processing: {filename}")
        try:
            # Count Event tags (games)
            with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                game_count = 0
                for line in content.split('\n'):
                    stripped_line = line.strip()
                    if stripped_line.startswith('[Event "') and not stripped_line.startswith('[EventDate'):
                        game_count += 1
                
                counts.append(f"{filename}: {game_count}")
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            counts.append(f"{filename}: 0")
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for count in counts:
            f.write(count + '\n')
    
    print(f"Generated {output_file} with {len(counts)} game counts")
    return len(counts)

def main():
    # Configuration - UPDATED PATHS
    tt_archive_dir = r"D:\GitHub\titled-tuesday-archive"  # Your GitHub repo with ZIP files
    chessnerd_dir = r"D:\GitHub\chessnerd"  # Your chessnerd website repo
    pgn_source_dir = r"D:\chessnerd\tt"  # Your original PGN files (NOT in GitHub repo!)
    
    print("=" * 60)
    print("Titled Tuesday Metadata Generator")
    print("=" * 60)
    print(f"GitHub Repo (ZIPs): {tt_archive_dir}")
    print(f"PGN Source Dir: {pgn_source_dir}")
    print(f"ChessNerd Dir: {chessnerd_dir}")
    print()
    
    # Check if directories exist
    if not Path(pgn_source_dir).exists():
        print(f"ERROR: PGN source directory not found: {pgn_source_dir}")
        print("Please check the path and try again.")
        return
    
    if not Path(tt_archive_dir).exists():
        print(f"WARNING: GitHub repo directory not found: {tt_archive_dir}")
        print("Creating directory...")
        Path(tt_archive_dir).mkdir(parents=True, exist_ok=True)
    
    if not Path(chessnerd_dir).exists():
        print(f"WARNING: ChessNerd directory not found: {chessnerd_dir}")
        print("Creating directory...")
        Path(chessnerd_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate files
    print("\n" + "=" * 60)
    print("Generating metadata files...")
    print("=" * 60)
    
    tt_links_file = os.path.join(tt_archive_dir, "tt_links.txt")
    tt_events_file = os.path.join(tt_archive_dir, "tt_events.txt")
    tt_counts_file = os.path.join(tt_archive_dir, "tt_game_counts.txt")
    
    # Generate links from ZIP files in GitHub repo
    print("\n1. Generating tt_links.txt from ZIP files...")
    links_count = generate_tt_links(tt_archive_dir, tt_links_file)
    
    # Generate events and counts from original PGNs
    print("\n2. Generating tt_events.txt from PGN files...")
    events_count = generate_tt_events_txt(pgn_source_dir, tt_events_file)
    
    print("\n3. Generating tt_game_counts.txt from PGN files...")
    counts_count = generate_tt_game_counts_txt(pgn_source_dir, tt_counts_file)
    
    # Copy all files to chessnerd directory
    print("\n" + "=" * 60)
    print("Copying files to chessnerd repo...")
    print("=" * 60)
    
    chessnerd_links = os.path.join(chessnerd_dir, "tt_links.txt")
    chessnerd_events = os.path.join(chessnerd_dir, "tt_events.txt")
    chessnerd_counts = os.path.join(chessnerd_dir, "tt_game_counts.txt")
    
    shutil.copy2(tt_links_file, chessnerd_links)
    shutil.copy2(tt_events_file, chessnerd_events)
    shutil.copy2(tt_counts_file, chessnerd_counts)
    
    print(f"  ✓ Copied tt_links.txt")
    print(f"  ✓ Copied tt_events.txt")
    print(f"  ✓ Copied tt_game_counts.txt")
    
    print("\n" + "=" * 60)
    print("METADATA GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Links (from ZIPs): {links_count}")
    print(f"Events (from PGNs): {events_count}")
    print(f"Game counts (from PGNs): {counts_count}")
    print()
    
    # Summary of files created
    print("Files created:")
    print(f"  {tt_links_file} (exists: {os.path.exists(tt_links_file)})")
    print(f"  {tt_events_file} (exists: {os.path.exists(tt_events_file)})")
    print(f"  {tt_counts_file} (exists: {os.path.exists(tt_counts_file)})")
    print()
    
    # Check if any PGN files were found
    pgn_files = list(Path(pgn_source_dir).glob('**/*.pgn'))
    if len(pgn_files) == 0:
        print("WARNING: No PGN files found!")
        print(f"Please check that PGN files exist in: {pgn_source_dir}")
        print("Common issues:")
        print("  1. Wrong directory path")
        print("  2. No .pgn files in the directory")
        print("  3. Files have different extension (.PGN instead of .pgn)")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Push ZIP files and metadata to GitHub:")
    print(f"   cd {tt_archive_dir}")
    print("   git add .")
    print("   git commit -m 'Add Titled Tuesday ZIP files and metadata'")
    print("   git push")
    print()
    print("2. Push metadata to ChessNerd:")
    print(f"   cd {chessnerd_dir}")
    print("   git add tt_links.txt tt_events.txt tt_game_counts.txt")
    print("   git commit -m 'Update Titled Tuesday metadata'")
    print("   git push")
    print()
    print("3. Verify the Titled Tuesday Archive page works:")
    print("   https://chessnerd.net/titled-tuesday-archive.html")

if __name__ == "__main__":
    main()