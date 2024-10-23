from json_repair import repair_json

# Read the contents of the file
with open("messages.txt", "r") as file:
    data = file.read()

# Repair the malformed JSON content
response = repair_json(data)

# Print the repaired JSON
print(response)
