with open(r'd:/ISO 286 EdTech/iso_286_edtech/index.html', encoding='utf-8') as f:
    lines = f.read().splitlines()
for i in range(2893, min(3120, len(lines))):
    print(f"{i+1}: {lines[i]}")
