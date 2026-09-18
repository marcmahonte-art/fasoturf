import fitz
import os

folder = r'C:\Users\Lenovo\Desktop\PMU\echantillon'

# Deep analyze page 2 of 01-07-2025
f = 'JH_PMUB_DU_01-07-2025.pdf'
path = os.path.join(folder, f)
doc = fitz.open(path)

page = doc[1]  # Page 2
blocks = page.get_text("blocks")

# Print all blocks with y coordinate sorted
print("All blocks sorted by Y:")
for b in sorted(blocks, key=lambda x: x[1]):
    bbox = b[:4]
    txt = b[4].strip()
    if txt and len(txt) < 200:
        print(f"  [{bbox[0]:.0f},{bbox[1]:.0f} {bbox[2]:.0f},{bbox[3]:.0f}] {txt[:100]}")

doc.close()