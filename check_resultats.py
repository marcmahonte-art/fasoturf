with open(r'C:\Users\Lenovo\Desktop\PMU\load_parsed_to_socle.py', 'r') as f:
    content = f.read()

idx = content.find('INSERT INTO resultats')
if idx >= 0:
    idx2 = content.find('new_resultats += 1', idx)
    snippet = content[idx:idx2]
    val_idx = snippet.find('VALUES')
    if val_idx >= 0:
        val_part = snippet[val_idx:val_idx+200]
        print(f'VALUES part: {val_part}')
        print(f'? count: {val_part.count("?")}')