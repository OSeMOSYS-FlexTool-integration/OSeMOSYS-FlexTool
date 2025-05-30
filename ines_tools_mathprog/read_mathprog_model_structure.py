from spinedb_api import DatabaseMapping
from spinedb_api.exception import NothingToCommit
import sys
import yaml
from pathlib import Path

def read_mathprog_structure(settings, url_db, file_path, param_dimens_file, write_to_db=True):

    file = open(file_path, 'r')
    dimens_to_param = settings["dimens_to_param"]
    class_for_scalars = settings["class_for_scalars"]
    set_names = []
    set_dimen_list = []
    set_1d_all = []
    set_1d_class = []
    param_names = []
    class_param_dimen_list = []
    all_param_dimen_list = []
    inside_param_dimen_list = []
    orig_dimen_order_list = []

    while True:
        next_line = file.readline()
        if not next_line:
            break
        if not next_line.find(';'):
            next_line = next_line + file.readline()
            if not next_line:
                break

        elements = next_line.replace(';', ' ').replace(',', ' , ').replace('{', ' { ').replace('}', ' } ').split()
        dimen_found = False
        make_set = False
        first_word = ""
        second_word = ""

        if len(elements) > 0:
            first_word = elements.pop(0)
            if len(elements) > 0:
                second_word = elements.pop(0)
            if first_word == "set":
                for i, element in enumerate(elements):
                    if element == "dimen":
                        dimen_found = True
                        if elements[i+1].isdigit():      # Check that the word after 'dimen' is a positive integer
                            if int(elements[i+1]) > 1:  # If dimen is more than 1, stop (just picking fundamental sets here, n-d sets are based on parameters
                                break
                        else:
                            make_set = True
                if not dimen_found:
                    set_1d_all.append(second_word)
                    make_set = True
                    for dimen_to_param in dimens_to_param:
                        if dimen_to_param == second_word:
                            make_set = False  # If the dimension is not on the list dimensions that will be put to parameters, make one
                            break
                if make_set:
                    set_names.append(second_word)
                    set_dimen_list.append([second_word])
                if not make_set and not dimen_found:
                    set_names.append(second_word)
                    set_dimen_list.append([second_word])
                if not dimen_found and make_set:
                    set_1d_class.append(second_word)


            if first_word == "param":
                param_dimen_start = False
                param_dimen_end = False
                param_attributes_start = False
                param_expression = False
                param_name_alias = []
                param_dimens = []
                all_param_dimens = []
                class_param_dimens = []
                inside_param_dimens = []
                class_dimen_order = []
                inside_dimen_order = []
                dim_counter = 0
                for i, next_word in enumerate(elements):
                    if next_word == '{':
                        param_dimen_start = True
                        continue
                    if next_word == '}':
                        param_dimen_end = True
                        continue
                    if next_word == ':=':
                        param_expression = True
                        break
                    if next_word == ',':
                        if (param_dimen_start and param_dimen_end) or (not param_dimen_start and not param_dimen_end):
                            param_attributes_start = True
                            break  # Attributes are not handled yet
                        continue
                    if not param_dimen_start and not param_attributes_start:
                        param_name_alias.append(next_word)
                    elif not param_dimen_end and not param_attributes_start:
                        if len(elements) > i + 2 and elements[i + 1] == "in":
                            param_dimen_candidate = elements[i + 2]
                            elements.pop(i)
                            elements.pop(i)
                        elif next_word != ',':
                            param_dimen_candidate = next_word
                        else:
                            continue
                        for set_name in set_1d_class:
                            if param_dimen_candidate == set_name:
                                class_param_dimens.append(param_dimen_candidate)
                                class_dimen_order.append(dim_counter)
                                dim_counter += 1
                                break
                        for set_name in dimens_to_param:
                            if param_dimen_candidate == set_name:
                                inside_param_dimens.append(param_dimen_candidate)
                                inside_dimen_order.append(dim_counter)
                                dim_counter += 1
                                break
                all_param_dimens = class_param_dimens + inside_param_dimens
                if not param_expression and param_dimen_start and param_dimen_end and class_param_dimens:
                    param_names.append(second_word)
                    class_param_dimen_list.append(class_param_dimens)
                    all_param_dimen_list.append(all_param_dimens)
                if not param_expression and param_dimen_start and param_dimen_end and not class_param_dimens:
                    param_names.append(second_word)
                    class_param_dimen_list.append([class_for_scalars])
                    all_param_dimen_list.append(all_param_dimens)
                    for f in range(len(inside_dimen_order)):
                        inside_dimen_order[f] += 1   # Move all dimensions one right to make room for the scalar class dimension
                if not param_expression and not param_dimen_start and not param_dimen_end:
                    param_names.append(second_word)
                    class_param_dimen_list.append([class_for_scalars])
                    all_param_dimen_list.append([class_for_scalars])
                    orig_dimen_order_list.append([])
                    inside_param_dimen_list.append(inside_param_dimens)
                if not param_expression and param_dimen_start and param_dimen_end:
                    orig_dimen_order_list.append(class_dimen_order + inside_dimen_order)
                    inside_param_dimen_list.append(inside_param_dimens)
    file.close()

    if write_to_db:
        for class_param_dimens in class_param_dimen_list:
            new_param_dimens = True  # Start by assuming that the dimens are not in any set yet
            for set_dimens in set_dimen_list:
                if len(class_param_dimens) == len(set_dimens):
                    param_dimens_in_set = True  # Start by assuming that the dimens are the same
                    for i, param_dimen in enumerate(class_param_dimens):
                        if param_dimen != set_dimens[i]:
                            param_dimens_in_set = False  # The dimens weren't the same, so it could be new
                            break
                    if param_dimens_in_set:       # Went through the dimens and it was the same!
                        new_param_dimens = False  # So, it's not a new set
                        break                     # No point to check the rest
            if new_param_dimens:  # It turned out to be a new set
                set_dimen_list.append(class_param_dimens)  # So, let's add it to the set_dimens_list
                set_names.append('__'.join(class_param_dimens))  # And give the set a name
        with DatabaseMapping(url_db) as target_db:
            for i, set_name in enumerate(set_names):
                if len(set_dimen_list[i]) > 1:
                    added, updated, error = target_db.add_update_entity_class_item(name=set_name, dimension_name_list=set_dimen_list[i])
                else:
                    added, updated, error = target_db.add_update_entity_class_item(name=set_name)
                if error:
                    exit("Exiting, db not changed: " + error)
            for i, param_name in enumerate(param_names):
                added, updated, error = target_db.add_update_parameter_definition_item(name=param_name,
                                                                    entity_class_name='__'.join(class_param_dimen_list[i]),
                                                                    description=' '.join(inside_param_dimen_list[i]))
                if error:
                    exit("Exiting, db not changed: " + error)

            try:
                target_db.commit_session("Model structure added from a Mathprog file")
            except NothingToCommit:
                print("Warning! There was no new classes or parameters to be added (maybe existing DB)")


    param_listing = {}
    for i in range(len(class_param_dimen_list)):
        param_listing[param_names[i]] = [class_param_dimen_list[i], inside_param_dimen_list[i]] + [orig_dimen_order_list[i]]

    with open(param_dimens_file, 'w+') as yaml_file:
        yaml.safe_dump(param_listing, yaml_file)

    file.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit("You need to provide the name (including path if in different folder) of the settings file as an argument")

    with open(sys.argv[1], 'r') as yaml_file:
        settings = yaml.safe_load(yaml_file)
    url_db = settings["target_db"]
    file_name = settings["model_code"]
    param_dimens_file='param_dimens.yaml'
    if len(sys.argv) > 2:
        url_db = sys.argv[2]
    read_mathprog_structure(settings, url_db, file_name, param_dimens_file)
