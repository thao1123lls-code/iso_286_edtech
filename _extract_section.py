import sys

with open("d:/iso-286-edtech/index.html", encoding="utf-8") as f:
    lines = f.readlines()

start = int(sys.argv[1]) - 1
end = int(sys.argv[2])

for i in range(start, min(end, len(lines))):
    print(f"{i+1:5d}| {lines[i]}", end="")

