import draco

import re


# important note: input has "entity(view,root,0)." and "entity(field,root,0)." both as 0, so 
def convert_format(input_str_list):
    # Dictionary to keep track of indices for each entity type
    entity_counters = {}
    
    # Dictionary to map old indices to new (e, n) format
    # Using (entity_type, idx) as the key to prevent collisions
    index_mapping = {}
    
    # First pass: process entities and build the index mapping
    for line in input_str_list:
        if line.startswith("entity("):
            # xtract entity information using regex
            match = re.match(r"entity\(([^,]+),([^,]+),(\d+)\)\.", line)
            if match:
                entity_type, parent, idx = match.groups()
                
                # Get the first letter of entity type
                entity_prefix = entity_type[0]
                
                # Initialize counter for this entity type if not exists
                if entity_prefix not in entity_counters:
                    entity_counters[entity_prefix] = 0
                
                # Create new index format (e, n)
                new_idx = f"({entity_prefix}, {entity_counters[entity_prefix]})"
                
                # Map (entity_type, idx) to new index format
                index_mapping[(entity_type, idx)] = new_idx
                
                # Increment counter for this entity type
                entity_counters[entity_prefix] += 1
    
    # Second pass: convert all lines using the mapping
    result = []
    for line in input_str_list:
        if line.startswith("entity("):
            # xtract entity information using regex
            match = re.match(r"entity\(([^,]+),([^,]+),(\d+)\)\.", line)
            if match:
                entity_type, parent, idx = match.groups()
                
                # If parent is not "root", convert parent index too
                if parent != "root":
                    # We need to determine the parent's entity type
                    parent_type = None
                    for prev_line in input_str_list:
                        if prev_line.startswith(f"entity(") and prev_line.endswith(f",{parent})."): 
                            parent_match = re.match(r"entity\(([^,]+),", prev_line)
                            if parent_match:
                                parent_type = parent_match.group(1)
                                break
                    
                    if parent_type:
                        parent = index_mapping.get((parent_type, parent), parent)
                
                # Get new index for this entity
                new_idx = index_mapping[(entity_type, idx)]
                
                # Create the new line
                new_line = f"entity({entity_type}, {parent}, {new_idx})."
                result.append(new_line)
            else:
                result.append(line)  # Keep original if no match
                
        elif line.startswith("attribute("):
            # xtract attribute information
            # Need to handle both formats:
            # attribute((field,name),0,date)
            # attribute(number_rows,root,10)
            
            # Try the complex format first
            complex_match = re.match(r"attribute\(\(([^,]+),([^)]+)\),(\d+),(.*)\)\.", line)
            if complex_match:
                attr_entity, attr_name, parent_idx, value = complex_match.groups()
                
                # For attributes, we need to determine the parent entity type
                parent_type = None
                for prev_line in input_str_list:
                    if prev_line.startswith(f"entity(") and prev_line.endswith(f",{parent_idx})."): 
                        parent_match = re.match(r"entity\(([^,]+),", prev_line)
                        if parent_match:
                            parent_type = parent_match.group(1)
                            break
                
                # Convert parent index if we found the type
                if parent_type:
                    new_parent_idx = index_mapping.get((parent_type, parent_idx), parent_idx)
                else:
                    new_parent_idx = parent_idx
                
                # Create the new line
                new_line = f"attribute(({attr_entity}, {attr_name}), {new_parent_idx}, {value})."
                result.append(new_line)
            else:
                # Try the simple format
                simple_match = re.match(r"attribute\(([^,]+),([^,]+),([^)]+)\)\.", line)
                if simple_match:
                    attr_name, parent, value = simple_match.groups()
                    
                    # If parent is a digit, it's an index that needs conversion
                    if parent.isdigit():
                        # We need to find the parent entity type for this attribute
                        parent_type = None
                        for prev_line in input_str_list:
                            if prev_line.startswith(f"entity(") and prev_line.endswith(f",{parent})."): 
                                parent_match = re.match(r"entity\(([^,]+),", prev_line)
                                if parent_match:
                                    parent_type = parent_match.group(1)
                                    break
                        
                        if parent_type:
                            parent = index_mapping.get((parent_type, parent), parent)
                    
                    # Create the new line
                    new_line = f"attribute({attr_name}, {parent}, {value})."
                    result.append(new_line)
                else:
                    result.append(line)  # Keep original if no match
        else:
            result.append(line)  # Keep non-entity, non-attribute lines unchanged
    
    return result


    # # Loop over all generated models (with a limit of 5 models)
    # for i, model in enumerate(d.complete_spec(facts)):
    #     chart_num = i + 1
    #     spec = answer_set_to_dict(model.answer_set)
    #     chart_name = f"Rec {chart_num}"

    #     # Store the facts for each recommendation
    #     specs[chart_name] = dict_to_facts(spec)
    # Now run the complete_spec method as usual, without soft constraints
# models = my_complete_spec(input, models=20, d=d)

from pathlib import Path
Program = draco.programs.Program
def to_string(prog: Program | str):
    if isinstance(prog, Program):
        return prog.program
    else:
        return prog

asp_path = Path("./asp")
define = draco.programs.read_program(asp_path / "define.lp")
constraints = draco.programs.read_program(asp_path / "constraints.lp")
generate = draco.programs.read_program(asp_path / "generate.lp")
hard = draco.programs.read_program(asp_path / "hard.lp")
helpers = draco.programs.read_program(asp_path / "helpers.lp")
soft = draco.programs.read_program(asp_path / "soft.lp")
optimize = draco.programs.read_program(asp_path / "optimize.lp")

define = to_string(define)
constraints = to_string(constraints)
generate = to_string(generate)
hard = to_string(hard)
helpers = to_string(helpers)
soft = to_string(soft)
optimize = to_string(optimize)

def my_complete_spec(input_spec, models=1, d=None):
    if not isinstance(input_spec, str):
        input_spec = "\n".join(input_spec)

    program = [
        define,
        generate,
        constraints,
        helpers,
        hard,
        # soft,
        # assign_weights,
        # optimize,
        input_spec,
    ]
    # pass the weights as constraint to Clingo
    # args = [f"-c {w}={v}" for w, v in self.weights.items()]
    return draco.run_clingo(program, models, False)

def solve_chart(input_facts):
    # print(input_facts)

    # new draco instance
    d = draco.Draco()
    models = my_complete_spec(input_facts, models=10, d=d)
    # models = d.complete_spec(input_facts)
    result = {}
    len_model = 0
    existing_spec = []
    for i, model in enumerate(models):
        spec = draco.answer_set_to_dict(model.answer_set)
        spec_view = {'view': spec['view']}
        facts = draco.dict_to_facts(spec)
        facts = convert_format(facts)
        # print(spec)
        # print(model.cost)

        # spec_str = str(spec)
        # if spec_str not in existing_spec:
        #     existing_spec.append(spec_str)
        # else:
        #     print("input: ", input_facts)
        #     print("existing_spec: ", existing_spec)
        #     print("current repeat: ", spec_str)
        #     exit()

        # print("save facts: ", facts)
        result["model_" + str(i)] = {
            'spec': spec_view,
            "facts": facts,
            'cost': model.cost
            }
        len_model = i + 1
    return result

def solve_chart_from_file(asp_file, data_schema_file):
    # solve chart from file
    pass

def process_ambiguous_pairs(input_lines, ambiguous_pairs):
    """
    Process input lines containing ambiguous attributes and replace them with expanded rules.
    
    Args:
        input_lines (list): List of strings containing ASP rules
        ambiguous_pairs (dict): Dictionary mapping ambiguous terms to their possible values
        
    Returns:
        list: Modified list of strings with expanded rules
    """
    output_lines = []
    
    for line in input_lines:
        # Check if line contains [AMBI] with encoding
        if "attribute((encoding, field)," not in line:
            output_lines.append(line)
            continue

        if "[AMBI]" not in line:
            output_lines.append(line)
            continue
                # Extract the ambiguous term
        ambi_key = line.split("[AMBI]")[1]
        ambi_key = ambi_key.split(")")[0]
        # print(ambi_key)
        field_list = ambiguous_pairs[ambi_key]
        attr_list = [ line.replace("[AMBI]" + ambi_key, field) for field in field_list]
        attr_list = [ line[:-1] for line in attr_list]
        # print(attr_list)
        new_line_1 = "1 { " + attr_list[0] + "; " + attr_list[1] + " } 1."
        new_line_2 = ":- " + attr_list[0] + ", " + attr_list[1] + "."
        output_lines.append(new_line_1)
        output_lines.append(new_line_2)
    
    return output_lines

def convert_format(input_str_list):
    # Dictionary to keep track of indices for each entity type
    entity_counters = {}
    
    # Dictionary to map old indices to new (e, n) format
    # Using (entity_type, idx) as the key to prevent collisions
    index_mapping = {}
    
    # First pass: process entities and build the index mapping
    for line in input_str_list:
        if line.startswith("entity("):
            # Extract entity information using regex
            match = re.match(r"entity\(([^,]+),([^,]+),(\d+)\)\.", line)
            if match:
                entity_type, parent, idx = match.groups()
                
                # Get the first letter of entity type
                entity_prefix = entity_type[0]
                
                # Initialize counter for this entity type if not exists
                if entity_prefix not in entity_counters:
                    entity_counters[entity_prefix] = 0
                
                # Create new index format (e, n)
                new_idx = f"({entity_prefix}, {entity_counters[entity_prefix]})"
                
                # Map (entity_type, idx) to new index format
                index_mapping[(entity_type, idx)] = new_idx
                
                # Increment counter for this entity type
                entity_counters[entity_prefix] += 1
    
    # Second pass: convert all lines using the mapping
    result = []
    for line in input_str_list:
        if line.startswith("entity("):
            # Extract entity information using regex
            match = re.match(r"entity\(([^,]+),([^,]+),(\d+)\)\.", line)
            if match:
                entity_type, parent, idx = match.groups()
                
                # If parent is not "root", convert parent index too
                if parent != "root":
                    # We need to determine the parent's entity type
                    parent_type = None
                    for prev_line in input_str_list:
                        if prev_line.startswith(f"entity(") and prev_line.endswith(f",{parent})."): 
                            parent_match = re.match(r"entity\(([^,]+),", prev_line)
                            if parent_match:
                                parent_type = parent_match.group(1)
                                break
                    
                    if parent_type:
                        parent = index_mapping.get((parent_type, parent), parent)
                
                # Get new index for this entity
                new_idx = index_mapping[(entity_type, idx)]
                
                # Create the new line
                new_line = f"entity({entity_type}, {parent}, {new_idx})."
                result.append(new_line)
            else:
                result.append(line)  # Keep original if no match
                
        elif line.startswith("attribute("):
            # Extract attribute information
            # Need to handle both formats:
            # attribute((field,name),0,date)
            # attribute(number_rows,root,10)
            
            # Try the complex format first
            complex_match = re.match(r"attribute\(\(([^,]+),([^)]+)\),(\d+),(.*)\)\.", line)
            if complex_match:
                attr_entity, attr_name, parent_idx, value = complex_match.groups()
                
                # For attributes, we need to determine the parent entity type
                parent_type = None
                for prev_line in input_str_list:
                    if prev_line.startswith(f"entity(") and prev_line.endswith(f",{parent_idx})."): 
                        parent_match = re.match(r"entity\(([^,]+),", prev_line)
                        if parent_match:
                            parent_type = parent_match.group(1)
                            break
                
                # Convert parent index if we found the type
                if parent_type:
                    new_parent_idx = index_mapping.get((parent_type, parent_idx), parent_idx)
                else:
                    new_parent_idx = parent_idx
                
                # Create the new line
                new_line = f"attribute(({attr_entity}, {attr_name}), {new_parent_idx}, {value})."
                result.append(new_line)
            else:
                # Try the simple format
                simple_match = re.match(r"attribute\(([^,]+),([^,]+),([^)]+)\)\.", line)
                if simple_match:
                    attr_name, parent, value = simple_match.groups()
                    
                    # If parent is a digit, it's an index that needs conversion
                    if parent.isdigit():
                        # We need to find the parent entity type for this attribute
                        parent_type = None
                        for prev_line in input_str_list:
                            if prev_line.startswith(f"entity(") and prev_line.endswith(f",{parent})."): 
                                parent_match = re.match(r"entity\(([^,]+),", prev_line)
                                if parent_match:
                                    parent_type = parent_match.group(1)
                                    break
                        
                        if parent_type:
                            parent = index_mapping.get((parent_type, parent), parent)
                    
                    # Create the new line
                    new_line = f"attribute({attr_name}, {parent}, {value})."
                    result.append(new_line)
                else:
                    result.append(line)  # Keep original if no match
        else:
            result.append(line)  # Keep non-entity, non-attribute lines unchanged
    
    return result


# main
if __name__ == "__main__":
    # xample input specification
    input_spec = [
        # data schema
        "attribute(number_rows, root, 100).",        
        "entity(field, root, (f, 0)).",
        "attribute((field, name), (f, 0), area).",
        "attribute((field, type), (f, 0), string).",
        "attribute((field, unique), (f, 0), 100).",
        "entity(field, root, (f, 1)).",
        "attribute((field, name), (f, 1), date).",
        "attribute((field, type), (f, 1), datetime).",
        "attribute((field, unique), (f, 1), 100).",
        "entity(field, root, (f, 2)).",
        "attribute((field, name), (f, 2), temp_max).",
        "attribute((field, type), (f, 2), number).",
        "attribute((field, unique), (f, 2), 100).",
        # "entity(field, root, (f, 3)).",
        # "attribute((field, name), (f, 3), temp_min).",
        # "attribute((field, type), (f, 3), number).",
        # "attribute((field, unique), (f, 3), 100).",
        # view
        "entity(view, root, (v, 0)).",
        "entity(mark, (v, 0), (m, 0)).",
        # "attribute((mark, type), (m, 0), bar).",
        # "attribute((mark, type), (m, 0), line).",
        # "attribute((mark, type), (m, 0), pie).",
        # "attribute((mark, type), (m, 0), point).",
        "attribute((mark, type), (m, 0), rect).",
        # "attribute((mark, type), (m, 0), boxplot).",
        # encoding
        "entity(encoding, (m, 0), (e, 0)).",
        # "attribute((encoding, field), (e, 0), area).",
        "attribute((encoding, field), (e, 0), date).",
        # "attribute((encoding, channel), (e, 0), y).",
        # "attribute((encoding, field), (e, 0), temp_max).",
        # "attribute((encoding, field), (e, 0), [AMBI]temp).",
        # "1 { attribute((encoding, field), (e, 0), temp_max); attribute((encoding, field), (e, 0), temp_min) } 1.",
        # ":- attribute((encoding, field), E1, temp_max), attribute((encoding, field), E2, temp_min).",
    ]

    print(input_spec)

    # Number of models to generate
    models = 10

    # Create a new instance of Draco
    d = draco.Draco()

    # Generate the complete specification
    # result = d.complete_spec(input_spec, models=models)
    result = my_complete_spec(input_spec, models=models)

    # Print the results
    for i, model in enumerate(result):
        spec = draco.answer_set_to_dict(model.answer_set)
        spec = spec['view']
        print(f"Model {i}:")
        print("Spec:", spec)
        print("Cost:", model.cost)
