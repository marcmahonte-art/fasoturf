import fitz
import os
import json

folder = r'C:\Users\Lenovo\Desktop\PMU\echantillon'
results = []

for f in sorted(os.listdir(folder)):
    if f.startswith('ECD') and f.endswith('.pdf'):
        path = os.path.join(folder, f)
        doc = fitz.open(path)
        size = os.path.getsize(path)
        
        info = {
            'filename': f,
            'size_bytes': size,
            'pages': len(doc),
            'pages_content': []
        }
        
        for i, page in enumerate(doc):
            text = page.get_text()
            blocks = page.get_text("blocks")
            info['pages_content'].append({
                'page_num': i + 1,
                'text_length': len(text),
                'text_preview': text[:2000],
                'block_count': len(blocks),
                'blocks': [{'bbox': b[:4], 'text': b[4][:500]} for b in blocks[:30]]
            })
        
        results.append(info)
        doc.close()

# Save to JSON for analysis
with open(r'C:\Users\Lenovo\Desktop\PMU\ecd_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Analyse terminee. Resultats sauves dans ecd_analysis.json")

# Print summary to file
with open(r'C:\Users\Lenovo\Desktop\PMU\ecd_summary.txt', 'w', encoding='utf-8') as out:
    for r in results:
        out.write(f"\n{r['filename']} - {r['size_bytes']} bytes - {r['pages']} pages\n")
        for p in r['pages_content']:
            out.write(f"  Page {p['page_num']}: {p['block_count']} blocs, {p['text_length']} chars\n")
            out.write(f"    Preview: {p['text_preview'][:500]}\n")
            out.write("\n")
        
        # Also write full text for detailed analysis
        for p in r['pages_content']:
            out.write(f"\n=== FULL TEXT PAGE {p['page_num']} ===\n")
            out.write(p['text_preview'])
            out.write("\n")