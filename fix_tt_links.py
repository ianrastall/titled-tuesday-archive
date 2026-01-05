# fix_tt_links.py
import os
import shutil
from pathlib import Path

def fix_tt_links(github_repo_dir, output_file):
    """Generate tt_links.txt with correct GitHub raw URLs."""
    repo_path = Path(github_repo_dir)
    base_url = "https://github.com/ianrastall/titled-tuesday-archive/raw/main"
    
    links = []
    
    # Walk through all ZIP files in the repo
    for zip_file in sorted(repo_path.glob('**/*.zip')):
        # Get relative path from repo root, using forward slashes
        rel_path = zip_file.relative_to(repo_path)
        rel_path_str = str(rel_path).replace('\\', '/')  # Convert Windows path to URL path
        url = f"{base_url}/{rel_path_str}"
        links.append(url)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(link + '\n')
    
    print(f"Generated {output_file} with {len(links)} links")
    return len(links)

def main():
    tt_archive_dir = r"D:\GitHub\titled-tuesday-archive"
    chessnerd_dir = r"D:\GitHub\chessnerd"
    
    print("Fixing tt_links.txt format...")
    
    # Fix the links file
    tt_links_file = os.path.join(tt_archive_dir, "tt_links.txt")
    links_count = fix_tt_links(tt_archive_dir, tt_links_file)
    
    # Copy to chessnerd directory
    chessnerd_links = os.path.join(chessnerd_dir, "tt_links.txt")
    shutil.copy2(tt_links_file, chessnerd_links)
    
    print(f"Fixed tt_links.txt with {links_count} links")
    print(f"Copied to chessnerd repo")

if __name__ == "__main__":
    main()