import json

# Open the input file
with open('Yosemite-Express.json', 'r') as f:
    data = json.load(f)

# Open a new file for writing the output
with open('Yosemite-Express.txt', 'w') as output_file:
    # Iterate through the elements and write 'Text' to the output file
    for i in data['elements']:
        if 'Text' in i:
            text_to_write = i['Text'] + '\n'
            print(text_to_write)
            output_file.write(text_to_write)
