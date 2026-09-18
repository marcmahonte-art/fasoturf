import fitz
import os

folder = r'C:\Users\Lenovo\Desktop\PMU\echantillon'

# Analyze second journal (02-12-2024) page 2
for f in sorted(os.listdir(folder)):
    if f.endswith('.pdf') and 'JH' in f and '02-12' in f:
        path = os.path.join(folder, f)
        doc = fitz.open(path)
        
        print(f"\n{'='*80}")
        print(f"FICHIER: {f}")
        print(f"{'='*80}")
        
        page = doc[1]  # Page 2
        blocks = page.get_text("blocks")
        
        # Group by x coordinate to identify columns
        cols = {}
        for b in blocks:
            bbox = b[:4]
            txt = b[4].strip()
            if txt and len(txt) < 100:
                x = round(bbox[0] / 10) * 10
                if x not in cols:
                    cols[x] = []
                cols[x].append((bbox[1], txt))
        
        print("\nColonnes détectées (par x):")
        for x in sorted(cols.keys()):
            vals = [v[1] for v in sorted(cols[x])[:20]]
            print(f"  x={x}: {vals}")
        
        doc.close()
        break