from typing import List, Dict
import csv
import json

def generate_enums_file(message_dict):
    # Existing code for categories
    category_code = "# This file is auto generated, refer to definitions.py\n\nclass MessageCategory(Enum):\n"
    categories = list(message_dict.keys())
    for i, category in enumerate(categories, start=1):
        category_code += f"    {category} = {i}\n"

    # New code to assign subcategory values
    values_code = "\n\n"
    for category in categories:
        subcategories = list(message_dict[category].keys())
        for i, subcategory in enumerate(subcategories, start=1):
            values_code += f"Messages.{category}.{subcategory}.value = {i}\n"
            values_code += f'Messages.{category}.{subcategory}.str = {subcategory!r}\n'

    for i, category in enumerate(categories, start=1):
        values_code += f"Messages.{category}.value = {i}\n"
        values_code += f'Messages.{category}.str = {category!r}\n'


    # Existing code for messages
    messages_code = "class Messages:\n"
    for category in categories:
        messages_code += f"    class {category}:\n"
        for subcategory in message_dict[category]:
            messages_code += f"        class {subcategory}(Enum):\n"
            for i, message in enumerate(message_dict[category][subcategory], start=1):
                messages_code += f"            {message} = auto()\n"

    # Existing code for payloads (simplified)
    payload_code = ""
    for category in categories:
        for subcategory in message_dict[category]:
            for message in message_dict[category][subcategory]:
                payload = message_dict[category][subcategory][message]
                payload_code += f"Messages.{category}.{subcategory}.{message}.payload = {repr(payload)}\n"

    # Combine all parts
    code = "from enum import Enum, auto\n\n"
    code += category_code + "\n"
    code += messages_code
    code += values_code
    code += payload_code

    # Write to file (existing logic)
    with open("message_structure.py", "w") as f:
        f.write(code)
    
class MessageDefinitions():
    def __init__(self):
        self.messages = {}
        self.messages = {}
        with open("message_definitions.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            current_message = None  # will hold a tuple: (Category, Type, Subtype)
            cats = {}
            for row in reader:
                # Clean each field (strip whitespace; convert missing values to empty strings)
                row = {k: (v.strip() if v is not None else "") for k, v in row.items()}
                # If the Category field is non‐empty, then this row starts a new message definition.
                if row["Category"]:
                    current_category = row["Category"]
                    current_type = row["Type"] if row["Type"] else None
                    current_subtype = row["Subtype"] if row["Subtype"] else None
                    if current_category not in cats:
                        cats[current_category] = {}
                    else:
                        cats[current_category][current_type] = [] if not current_subtype else current_subtype
                    #print(current_category, cats) 

                    # Build the self.messages dictionary.
                    if current_category not in self.messages:
                        self.messages[current_category] = {}
                    if current_type:
                        if current_type not in self.messages[current_category]:
                            self.messages[current_category][current_type] = {}
                    if current_subtype:
                        self.messages[current_category][current_type][current_subtype] = []

                    # Remember the current message for subsequent payload rows.
                    current_message = (current_category, current_type, current_subtype)
                else:
                    # If Category is empty, this row defines a payload field for the current message.
                    if current_message is None:
                        continue  # or raise an error if a payload row is found before any message definition
                    payload_field = row["FieldName"]
                    if payload_field:
                        payload_field_type = row["FieldType"]
                        payload_field_bitmask = row["FieldBitmask"]
                        # Interpret bitmask flag (assumes the CSV uses "TRUE" or "FALSE")
                        payload_field_bitmask_bool = payload_field_bitmask.upper() == "TRUE"
                        payload_def = {
                            "name": payload_field,
                            "datatype": payload_field_type,
                            "bitmask": payload_field_bitmask_bool
                        }
                        cat, typ, sub = current_message
                        self.messages[cat][typ][sub].append(payload_def)
            
            # replace the csv file with json entirely soon
            #with open("message_definitions.json","w+") as file:
            #    file.write(json.dumps(self.messages,indent=4))
            generate_enums_file(self.messages)

# For debugging, you can print the generated dictionaries:
if __name__ == '__main__':
    import pprint
    protodefs = MessageDefinitions()
    print("Structure:")
    pprint.pprint(protodefs.messages)

