from parser import SimpleParser

parser = SimpleParser()

# Test cases
test_phrases = [
    "Goal Winston",
    "Save Tommy",
    "Shot Kip",
    "Alex scored",
    "Pass from Logan to Tom"
]

for phrase in test_phrases:
    result = parser.parse(phrase)
    print(f"'{phrase}' → {result}")