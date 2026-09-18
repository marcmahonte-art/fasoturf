import fitz
import os

folder = r'C:\Users\Lenovo\Desktop\PMU\echantillon'
f = 'JH_PMUB_DU_01-07-2025.pdf'
path = os.path.join(folder, f)
doc = fitz.open(path)
page = doc[1]
blocks = page.get_text("blocks")

# Test the grouping logic
rows = {}
for b in blocks:
    bbox = b[:4]
    txt = b[4].strip()
    if not txt or len(txt) > 200:
        continue
    x_center = (bbox[0] + bbox[2]) / 2
    y_center = (bbox[1] + bbox[3]) / 2
    y_key = round(y_center / 15) * 15
    x_key = round(x_center / 10) * 10
    if y_key not in rows:
        rows[y_key] = {}
    if x_key not in rows[y_key]:
        rows[y_key][x_key] = txt
    else:
        rows[y_key][x_key] += " | " + txt

# Print rows with potential numero
print("Rows with numero candidates:")
for y in sorted(rows.keys()):
    cols = rows[y]
    # Check for numero in columns ~20-35
    for cx in [20, 25, 30, 35]:
        if cx in cols:
            val = cols[cx].strip()
            if val.isdigit():
                print(f"  y={y}, x={cx}: '{val}' -> ROW CANDIDATE")
                # Show all cols for this row
                for k in sorted(cols.keys()):
                    print(f"    x={k}: {cols[k][:50]}")
                break

doc.close()