import json
from pathlib import Path
from datetime import datetime

# Load both files
with open(r"C:\Users\Lenovo\Desktop\PMU\data\processed\all_parsed.json", 'r', encoding='utf-8') as f:
    file1 = json.load(f)

with open(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\all_parsed.json", 'r', encoding='utf-8') as f:
    file2 = json.load(f)

# Index by filename
f1_by_name = {e['filename']: e for e in file1}
f2_by_name = {e['filename']: e for e in file2}

# Merge strategy: File 2 is the primary (richer, normalized)
# For overlaps, use File 2. For File 1 only, add them (but there are none)
merged = list(file2)  # Start with all File 2 entries

# Check if any File 1 entries have unique data not in File 2
# (In this case, all File 1 files are in File 2, so nothing to add)

# But let's verify the overlapping entries - File 2 has more partants for journals
# File 2 is strictly better for all overlaps

# Write merged database
output_path = r"C:\Users\Lenovo\Desktop\PMU\data\processed\all_parsed_merged.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f"Merged database written to: {output_path}")
print(f"Total entries: {len(merged)}")

# Stats
journals = [e for e in merged if e.get('doc_type') == 'JOURNAL' or e.get('type') == 'JOURNAL']
resultats = [e for e in merged if e.get('doc_type') == 'RESULTAT' or e.get('type') == 'RESULTAT']
ecds = [e for e in merged if e.get('doc_type') == 'ECD' or e.get('type') == 'ECD']

print(f"  Journals: {len(journals)}")
print(f"  Resultats: {len(resultats)}")
print(f"  ECDs: {len(ecds)}")

# Count total partants across all journals
total_partants = sum(len(e.get('partants', [])) for e in journals)
print(f"  Total partants in journals: {total_partants}")

# Date range
dates = []
for e in merged:
    d = e.get('date_publication') or e.get('data', {}).get('date_publication')
    if d:
        dates.append(d)
if dates:
    print(f"  Date range: {min(dates)} to {max(dates)}")

# Verify no duplicate filenames
filenames = [e['filename'] for e in merged]
dupes = set([f for f in filenames if filenames.count(f) > 1])
if dupes:
    print(f"WARNING: Duplicate filenames: {dupes}")
else:
    print("  No duplicate filenames ✓")