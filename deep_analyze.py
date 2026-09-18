import fitz
import os

folder = r'C:\Users\Lenovo\Desktop\PMU\echantillon'

# Deep analyze one journal page 2 (partants table)
for f in sorted(os.listdir(folder)):
    if f.endswith('.pdf') and 'JH' in f:
        path = os.path.join(folder, f)
        doc = fitz.open(path)
        
        print(f"\n{'='*80}")
        print(f"FICHIER: {f}")
        print(f"{'='*80}")
        
        for i, page in enumerate(doc):
            print(f"\n--- PAGE {i+1} ---")
            text = page.get_text()
            print(f"Full text ({len(text)} chars):")
            print(text[:3000])
            
            # Get blocks with coordinates
            blocks = page.get_text("blocks")
            print(f"\nBlocs ({len(blocks)}):")
            for b in blocks:
                bbox = b[:4]
                txt = b[4].strip()
                if txt:
                    print(f"  [{bbox[0]:.0f},{bbox[1]:.0f} {bbox[2]:.0f},{bbox[3]:.0f}] {txt[:150]}")
        
        doc.close()
        break  # Just first journal for now