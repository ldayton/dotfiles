# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "bashlex",
# ]
# ///
import bashlex

cmd = "time git status"
parts = bashlex.parse(cmd)
print(f"Parsing: {cmd}")
for p in parts:
    print(p.dump())
