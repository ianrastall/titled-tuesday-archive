import os
import shutil
from pathlib import Path

def generate_tt_links(github_repo_dir, output_file):
    """Generate tt_links.txt with GitHub raw URLs for ZIP files."""
    repo_path = Path(github_repo_dir)
    base_url = "https://github.com/ianrastall/titled-tuesday-archive/raw/main"
    
    links = []
    
    # Walk through all ZIP files in the repo
    for zip_file in sorted(repo_path.glob('**/*.zip')):
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
    
    # Debug: print the directory we are looking in
    print(f"Looking for PGN files in: {pgn_path.absolute()}")
    
    # Get list of PGN files
    pgn_files = list(pgn_path.glob('**/*.pgn'))
    print(f"Found {len(pgn_files)} PGN files")
    
    events = []
    
    # Process all PGN files recursively
    for pgn_file in sorted(pgn_files):
        filename = pgn_file.name
        print(f"Processing: {filename}")
        try:
            # Read the file to find Event tag
            with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
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
                        break
                else:
                    events.append(f"{filename}: No Event tag found")
                    
        except Exception as e:
            print(f"Error reading {filename}: {e}")
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
    
    counts = []
    
    # Process all PGN files recursively
    for pgn_file in sorted(pgn_path.glob('**/*.pgn')):
        filename = pgn_file.name
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
            print(f"Error reading {filename}: {e}")
            counts.append(f"{filename}: 0")
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for count in counts:
            f.write(count + '\n')
    
    print(f"Generated {output_file} with {len(counts)} game counts")
    return len(counts)

def main():
    # Configuration
    tt_archive_dir = r"D:\GitHub\titled-tuesday-archive"  # Your local clone of the repo
    chessnerd_dir = r"D:\GitHub\chessnerd"  # Your chessnerd website repo
    pgn_source_dir = r"D:\chessnerd\tt"  # Your original PGN files
    
    print("Generating Titled Tuesday metadata files...\n")
    
    # Generate files
    print("Creating metadata files...")
    tt_links_file = os.path.join(tt_archive_dir, "tt_links.txt")
    tt_events_file = os.path.join(tt_archive_dir, "tt_events.txt")
    tt_counts_file = os.path.join(tt_archive_dir, "tt_game_counts.txt")
    
    # Regenerate links to ensure they're up to date
    links_count = generate_tt_links(tt_archive_dir, tt_links_file)
    
    # Generate events and counts from original PGNs
    events_count = generate_tt_events_txt(pgn_source_dir, tt_events_file)
    counts_count = generate_tt_game_counts_txt(pgn_source_dir, tt_counts_file)
    
    # Copy all files to chessnerd directory
    print(f"\nCopying files to chessnerd repo...")
    chessnerd_links = os.path.join(chessnerd_dir, "tt_links.txt")
    chessnerd_events = os.path.join(chessnerd_dir, "tt_events.txt")
    chessnerd_counts = os.path.join(chessnerd_dir, "tt_game_counts.txt")
    
    shutil.copy2(tt_links_file, chessnerd_links)
    shutil.copy2(tt_events_file, chessnerd_events)
    shutil.copy2(tt_counts_file, chessnerd_counts)
    
    print(f"  ✓ Copied tt_links.txt")
    print(f"  ✓ Copied tt_events.txt")
    print(f"  ✓ Copied tt_game_counts.txt")
    
    print(f"\n{'='*60}")
    print("Titled Tuesday metadata generation complete!")
    print(f"Links: {links_count}")
    print(f"Events: {events_count}")
    print(f"Game counts: {counts_count}")
    print(f"{'='*60}")
    print(f"\nFiles created in:")
    print(f"  - {tt_archive_dir}")
    print(f"  - {chessnerd_dir}")
    print("\nNext steps:")
    print("1. Commit and push titled-tuesday-archive repo:")
    print("   cd D:\GitHub\titled-tuesday-archive")
    print("   git add tt_links.txt tt_events.txt tt_game_counts.txt")
    print("   git commit -m 'Add metadata files'")
    print("   git push")
    print("2. Commit and push chessnerd repo:")
    print("   cd D:\GitHub\chessnerd")
    print("   git add tt_links.txt tt_events.txt tt_game_counts.txt")
    print("   git commit -m 'Update Titled Tuesday metadata'")
    print("   git push")

if __name__ == "__main__":
    main()