import fitz
import os
import json

folder = r'C:\Users\Lenovo\Desktop\PMU\echantillon'
results = []

for f in sorted(os.listdir(folder)):
    if f.endswith('.pdf'):
        path = os.path.join(folder, f)
        doc = fitz.open(path)
        size = os.path.getsize(path)
        ftype = 'JOURNAL' if 'JH' in f else 'RESULTAT'
        
        info = {
            'filename': f,
            'type': ftype,
            'size_bytes': size,
            'pages': len(doc),
            'pages_content': []
        }
        
        for i, page in enumerate(doc):
            text = page.get_text()
            blocks = page.get_text("blocks")
            info['pages_content'].append({
                'page_num': i + 1,
                'text_preview': text[:1000],
                'block_count': len(blocks),
                'blocks': [{'bbox': b[:4], 'text': b[4][:200]} for b in blocks[:20]]
            })
        
        results.append(info)
        doc.close()

# Save to JSON for analysis
with open(r'C:\Users\Lenovo\Desktop\PMU\sample_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Analyse terminee. Resultats sauves dans sample_analysis.json")

# Print summary
for r in results:
    print(f"\n{r['filename']} ({r['type']}) - {r['size_bytes']} bytes - {r['pages']} pages")
    for p in r['pages_content']:
        print(f"  Page {p['page_num']}: {p['block_count']} blocs")
        print(f"    Preview: {p['text_preview'][:300]}")