with open(r'C:\Users\Lenovo\Desktop\PMU\load_parsed_to_socle.py', 'r') as f:
    content = f.read()

idx = content.find('INSERT INTO partants')
if idx >= 0:
    idx2 = content.find('new_partants += 1', idx)
    snippet = content[idx:idx2]
    
    # Count ? in the snippet
    q_count = snippet.count('?')
    print(f'Total ? in snippet: {q_count}')
    
    # Find the VALUES clause
    val_idx = snippet.find('VALUES')
    if val_idx >= 0:
        val_part = snippet[val_idx:val_idx+200]
        print(f'VALUES part: {val_part}')
        
        # Count ? in VALUES part
        val_q = val_part.count('?')
        print(f'? in VALUES: {val_q}')