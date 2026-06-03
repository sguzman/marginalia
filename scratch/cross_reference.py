import os
import re

def main():
    md_dir = "/win/linux/Code/Text/marginalia/tmp/ai-research-reports/data/md"
    ledger_path = "/win/linux/Code/Text/marginalia/data/ai/article_migration.toml"

    # 1. Get all project folders from the AI research repo
    md_projects = set()
    for item in os.listdir(md_dir):
        if os.path.isdir(os.path.join(md_dir, item)):
            md_projects.add(item)

    # 2. Get all tracked/migrated slugs from the official ledger
    migrated_slugs = set()
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger_content = f.read()
    
    # Extract all source_slug values from the TOML ledger
    # format: source_slug = "..."
    matches = re.findall(r'source_slug\s*=\s*"([^"]+)"', ledger_content)
    for match in matches:
        migrated_slugs.add(match)

    # 3. Objective comparison
    missing_projects = sorted(list(md_projects - migrated_slugs))

    # Output results
    print(f"Total projects in ai-research-reports: {len(md_projects)}")
    print(f"Total projects migrated in ledger: {len(migrated_slugs)}")
    print(f"Total missing (unmigrated) projects: {len(missing_projects)}")
    print("-" * 50)
    for missing in missing_projects:
        print(missing)

if __name__ == "__main__":
    main()
