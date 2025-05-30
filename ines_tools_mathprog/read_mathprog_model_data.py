import spinedb_api as api
from spinedb_api import DatabaseMapping
from spinedb_api.exception import NothingToCommit
import sys
import os
import numpy
import yaml
import copy
import csv
from datetime import datetime
from pathlib import Path


def write_param(target_db, entity_class, param, alternative_name, new_values, param_dims):
    previous_entity_name = []
    new_entity = False
    # Get the first entity_name
    entity_name = []

    if len(param_dims[2]) < len(param_dims[0]) + len(param_dims[1]):  # Take out the artificial class dimension
        class_dimen_positions = [0]
        inside_dimen_positions = param_dims[2][len(param_dims[0]) - 1:]
    else:
        class_dimen_positions = param_dims[2][:len(param_dims[0])]
        inside_dimen_positions = param_dims[2][len(param_dims[0]):]
    for class_dim in class_dimen_positions:
        entity_name.append(new_values[0][class_dim])
    insides = ([[] for _ in range(len(inside_dimen_positions) + 1)])
    for q, value_row in enumerate(new_values):
        entity_name_joined = '__'.join(entity_name)
        next_entity_name = []
        if q < len(new_values) - 1:  # If not the last value row, then get the name of the next entity
            for class_dim in class_dimen_positions:  # Get the next entity_name
                next_entity_name.append(new_values[q + 1][class_dim])
            next_entity_name_joined = '__'.join(next_entity_name)
        else:
            next_entity_name_joined = ''
        for r, inside_dim in enumerate(inside_dimen_positions):  # Get the index names for the current value row
            insides[r].append(value_row[inside_dim])
        try:
            value_row[-1] = float(value_row[-1])
        except ValueError:
            pass
        insides[-1].append(value_row[-1])  # Get the values for the current value row (from the last column of the value_row
        # If the entity name changes, then write the data for the current entity_name
        if entity_name_joined != next_entity_name_joined or q == len(new_values) - 1:
            # write param
            if len(inside_dimen_positions) == 1:
                vls = api.Map(insides[0], insides[-1], index_name=param_dims[1][0])
                values_in_map, type_ = api.to_database(vls)
            elif len(inside_dimen_positions) == 2:
                vls = []
                outer_index_list = []
                current_2nd_last_dim_index = insides[-3][0]
                outer_index_list.append(current_2nd_last_dim_index)
                start_2nd_last_dim = 0
                for x in range(len(insides[0])):
                    if current_2nd_last_dim_index != insides[-3][x]:
                        vls.append(api.Map(insides[-2][start_2nd_last_dim:x], insides[-1][start_2nd_last_dim:x], index_name=param_dims[1][len(inside_dimen_positions) - 1]))
                        current_2nd_last_dim_index = insides[-3][x]
                        start_2nd_last_dim = x
                        outer_index_list.append(current_2nd_last_dim_index)
                vls.append(api.Map(insides[-2][start_2nd_last_dim:x + 1], insides[-1][start_2nd_last_dim:x + 1], index_name=param_dims[1][len(inside_dimen_positions) - 1]))
                for r in reversed(range(len(inside_dimen_positions) - 1)):
                    vls = api.Map(outer_index_list, vls, index_name=param_dims[1][r])
                values_in_map, type_ = api.to_database(vls)
            elif len(inside_dimen_positions) > 2:
                exit("More than two inside dimensions currently not supported")
            else:
                if len(insides[-1]) == 1:
                    values_in_map, type_ = api.to_database(insides[-1][0])
                else:
                    exit("Scalar parameter value has more than one value in the input file_ " + entity_name_joined)
            entity_class_split = entity_class.split("__")
            added = []
            for c, entity_dim_name in enumerate(entity_name):
                added = target_db.add_update_entity_item(entity_class_name=entity_class_split[c],
                                                         name=entity_dim_name
                                                         )
                added_ea = target_db.add_update_entity_alternative_item(entity_class_name=entity_class,
                                                                        entity_byname=[entity_dim_name],
                                                                        alternative_name=alternative_name,
                                                                        active=True
                                                                        )
            added = target_db.add_update_entity_item(entity_class_name=entity_class,
                                                     entity_byname=tuple(entity_name)
                                                     )
            added, error = target_db.add_parameter_value_item(entity_class_name=entity_class,
                                                              parameter_definition_name=param,
                                                              entity_byname=tuple(entity_name),
                                                              value=values_in_map,
                                                              type=type_,
                                                              alternative_name=alternative_name)

            #print("added param " + param)
            insides = [[] for _ in range(len(inside_dimen_positions) + 1)]
        entity_name = next_entity_name
    try:
        target_db.commit_session("Values for parameter " + param + " added")
    except NothingToCommit:
        pass

def read_mathprog_data(settings, url_db, file_name, param_dimens_file):

    dimens_to_param = settings["dimens_to_param"]
    class_for_scalars = settings["class_for_scalars"]
    alternative_name = settings["alternative_name"]
    entities_from_entities = settings["entities_from_entities"]
    purge = settings["purge"]
    #read_separate_csv = settings["read_separate_csv"]
    file = open(file_name, 'r')
    with open(param_dimens_file, 'r') as yaml_file:
        param_listing = yaml.safe_load(yaml_file)

    with DatabaseMapping(url_db) as target_db:

        if purge:
            target_db.purge_items('entity')
            target_db.commit_session("Purged entities")
            target_db.purge_items('alternative')
            target_db.commit_session("Purged alternatives")
        target_db.add_alternative_item(name=alternative_name)
        target_db.add_scenario_item(name=alternative_name)
        target_db.add_scenario_alternative_item(alternative_name=alternative_name, scenario_name=alternative_name, rank=0)
        target_db.commit_session("Added alternative and scenario " + alternative_name)
        class__param = {}
        class__param__all_dimens = {}
        class__dimen = {}
        entity_classes = target_db.get_entity_class_items()
        for entity_class in entity_classes:
            params = target_db.get_parameter_definition_items(entity_class_name=entity_class["name"])
            params_name_list = []
            all_params_dimen_dict_list = {}
            for param in params:
                params_name_list.append(param["name"])
                if param["name"] in param_listing.keys():
                    all_params_dimen_dict_list[param["name"]] = param_listing[param["name"]][0] + param_listing[param["name"]][1]
            class__param[entity_class["name"]] = params_name_list
            class__param__all_dimens[entity_class["name"]] = all_params_dimen_dict_list
            dimens_name_list = []
            for dimen in entity_class["dimension_name_list"]:
                dimens_name_list.append(dimen)
            class__dimen[entity_class["name"]] = dimens_name_list

        while True:
            next_line = file.readline()  # This block of code will read the next line, but also the lines after in case there is no ';' sign to mark the end of the MathProg command
            if not next_line:
                break
            elements = next_line.replace(':', ' :').replace(';', ' ;').replace(',', ' , ').replace('[', ' [ ').replace(']', ' ] ').split()
            if len(elements) > 0:
                if elements[0] == "set" or elements[0] == "param":
                    while next_line.find(';') == -1:  # Check if the data is all in one line. find() returns -1 if not found --> adds lines until ;
                        next_line = file.readline()
                        if not next_line:
                            break
                        elements = elements + ['\n'] + next_line.replace(':', ' :').replace(';', ' ;').replace(',', ' , ').replace('[', ' [ ').replace(']', ' ] ').split()
                else:
                    continue
            else:
                continue

            make_set = False
            first_word = ""
            second_word = ""
            add_all_entity_combinations_to_class = []

            if len(elements) > 0:
                first_word = elements.pop(0)
                if len(elements) > 0:
                    second_word = elements.pop(0)

                if first_word == "set":
                    class_name_found = False
                    class_name_to_parameters = False
                    for class_name in class__param.keys():
                        if second_word == class_name:
                            print("Class " + class_name + " found")
                            class_name_found = True
                            break
                    for class_name_2 in dimens_to_param:
                        if second_word == class_name_2:
                            print("Class " + class_name_2 + " going into parameters")
                            class_name_to_parameters = True
                            break
                    if not class_name_found and not class_name_to_parameters:
                        exit("No class found for set " + second_word)
                    if class_name_found:
                        added = None
                        read_set_elements = False
                        set_member_names = []
                        for i, element in enumerate(elements):
                            if element == "\n":
                                continue
                            if element == ":=":
                                read_set_elements = True
                                continue
                            if element == ";":
                                break
                            if read_set_elements:
                                set_member_names.append(element)
                                added, error = target_db.add_entity_item(entity_class_name=class_name, name=element)
                                added_ea = target_db.add_update_entity_alternative_item(entity_class_name=class_name,
                                                                                        entity_byname=[element],
                                                                                        alternative_name=alternative_name,
                                                                                        active=True
                                                                                        )
                        if added:
                            try:
                                target_db.commit_session("Added entities from class " + class_name)
                            except NothingToCommit:
                                pass
                        continue


                if first_word == "param":
                    param_dimen_start = False
                    param_dimen_end = False
                    param_attributes_start = False
                    colon_sign = False
                    value_given = False
                    tabbed_column_headers = []
                    param_name_alias = []
                    param_dimens = []
                    is_default_value = False
                    current_entity_class_dimens = []
                    entity_class_dimens = []
                    inside_dimen_positions = []
                    class_dimen_positions = []
                    is_class_dimen = []
                    current_inside_dimens = []
                    current_untabbed_headers = []
                    tabbed_col_orig_pos = 0
                    tabbed_row_orig_pos = 0
                    current_untabbed_locations = []
                    found_param = False
                    tabbed_flag = False
                    for entity_class in class__param:  # Try to find the param from the DB structure, check all entity_classes
                        for param in class__param[entity_class]:  # Go through every parameter in the class
                            if second_word == param:              # If the parameter name matches DB parameter name
                                if class__dimen[entity_class]:
                                    current_entity_class_dimens = class__dimen[entity_class]  # Take the dimensions the parameter class has
                                else:
                                    current_entity_class_dimens = [entity_class]
                                if class__param__all_dimens[entity_class][param]:
                                    current_parameter_dimens = class__param__all_dimens[entity_class][param]
                                current_list = []
                                param_data = current_list
                                new_values = []

                                for i, dimen in enumerate(current_parameter_dimens):
                                    if i > 1:
                                        nested = []
                                        current_list.append(nested)
                                        current_list = nested
                                    found_dimen = False
                                    for class_dimen in current_entity_class_dimens:
                                        if dimen == class_dimen:
                                            found_dimen = True
                                            class_dimen_positions.append(i)
                                            is_class_dimen.append(True)
                                            break
                                    if not found_dimen:
                                        inside_dimen_positions.append(i)
                                        is_class_dimen.append(False)
                                        current_inside_dimens.append(dimen)
                                found_param = True
                                break
                        if found_param:  # No need to check further entity classes if the parameter has been found (no duplicate parameter names in MathProg)
                            data_headers = [[] for _ in range(len(current_parameter_dimens))]  # List of lists where each dimension has it's own list of header names.
                            data_counter = [-1 for _ in range(len(current_parameter_dimens))]
                            print(param)
                            break

                    for i, next_word in enumerate(elements):
                        if next_word == '\n':  # Skip end of lines
                            continue
                        if next_word == '#':
                            while elements[i + 1] != '\n':
                                elements.pop(i + 1)
                            continue
                        if next_word == ';':
                            if new_values:
                                write_param(target_db, entity_class, param, alternative_name, new_values, param_listing[param])
                            if not value_given and is_default_value:
                                add_all_entity_combinations_to_class.append(entity_class)
                            break
                        if next_word == '[':
                            dim_number = 0
                            non_tabbed_dim_number = 0
                            current_untabbed_headers = []
                            current_untabbed_locations = []
                            read_tabbed = elements.pop(i + 1)
                            first_star_given = False
                            data_header_branches = False
                            if len(current_parameter_dimens) > len(param_listing[param][2]):  # If there is no class dimension (all dimensions inside_class)
                                dim_number = 1
                                current_untabbed_locations.append(0)
                                data_headers[0].append(settings["class_for_scalars"])
                            while read_tabbed != ']':
                                if read_tabbed != ',':
                                    if read_tabbed == '*':
                                        if not first_star_given:
                                            tabbed_row_orig_pos = dim_number
                                            tabbed_dim_loc = len(current_parameter_dimens) - 2
                                            first_star_given = True
                                        else:
                                            tabbed_col_orig_pos = dim_number
                                            tabbed_dim_loc = len(current_parameter_dimens) - 1
                                    else:
                                        data_header_found = False
                                        current_untabbed_headers.append(read_tabbed)
                                        current_untabbed_locations.append(dim_number)
                                        for k, data_header in enumerate(data_headers[non_tabbed_dim_number]):
                                            if data_header == read_tabbed:
                                                data_header_found = True
                                                data_counter[non_tabbed_dim_number] = k
                                                break
                                        if not data_header_found:
                                            data_headers[non_tabbed_dim_number].append(read_tabbed)
                                            data_counter[non_tabbed_dim_number] = len(data_headers[non_tabbed_dim_number]) - 1
                                            data_header_branches = True
                                        non_tabbed_dim_number += 1

                                    dim_number += 1
                                read_tabbed = elements.pop(i+1)
                            continue
                        if next_word == ':=':  # Skip := signs (unsignificant in MathProg)
                            continue
                        if next_word == ':':
                            colon_sign = True
                            if not tabbed_col_orig_pos and not tabbed_row_orig_pos and not tabbed_flag:  # Check whether asterix has been used
                                tabbed_flag = True
                                tabbed_col_orig_pos = 1
                                tabbed_row_orig_pos = 0
                                non_tabbed_dim_number = 0
                                if len(current_parameter_dimens) > len(param_listing[param][2]):  # If there is no class dimension (all dimensions inside_class)
                                    tabbed_col_orig_pos = 2
                                    tabbed_row_orig_pos = 1
                                    non_tabbed_dim_number = 1
                                    current_untabbed_locations.append(0)
                                    data_headers[0].append(settings["class_for_scalars"])
                                    data_counter[0] = 0
                            next_column_header_element = elements.pop(i+1)
                            while next_column_header_element == '\n':
                                next_column_header_element = elements.pop(i+1)
                            while next_column_header_element != ':=' and next_column_header_element != '\n':
                                data_header_found = False
                                tabbed_dim_loc = len(current_parameter_dimens) - 1
                                for k, data_header in enumerate(data_headers[tabbed_dim_loc]):
                                    if data_header == next_column_header_element:
                                        data_header_found = True
                                        data_counter[non_tabbed_dim_number] = k
                                        break
                                if not data_header_found:
                                    data_headers[tabbed_dim_loc].append(next_column_header_element)
                                    data_counter[tabbed_dim_loc] = len(data_headers[tabbed_dim_loc]) - 1
                                next_column_header_element = elements.pop(i + 1)
                            if next_column_header_element == ':=':
                                elements.pop(i+1)
                            value_row_pos = 0
                            tabbed_row_count = -1
                            continue
                        if colon_sign and value_row_pos == 0:
                            tabbed_dim_loc = len(current_parameter_dimens) - 2
                            data_header_found = False
                            for k, data_header in enumerate(data_headers[tabbed_dim_loc]):
                                if data_header == next_word:
                                    data_header_found = True
                                    data_counter[non_tabbed_dim_number] = k
                                    break
                            if not data_header_found:
                                data_headers[tabbed_dim_loc].append(next_word)
                                data_counter[tabbed_dim_loc] = len(data_headers[tabbed_dim_loc]) - 1
                            current_row_header = next_word
                            tabbed_row_count += 1
                            value_row_pos = 1
                        if colon_sign and value_row_pos > 0:
                            param_values_in_row = []
                            param_types_in_row = []
                            temp = [-1 for _ in range(len(current_parameter_dimens) + 1)]
                            for j, tabbed_column_header_name in enumerate(data_headers[len(current_parameter_dimens) - 1]):
                                value = elements.pop(i+1)
                                for d, u in enumerate(current_untabbed_locations):
                                    temp[u] = data_headers[d][data_counter[d]]
                                temp[tabbed_row_orig_pos] = current_row_header
                                temp[tabbed_col_orig_pos] = copy.copy(tabbed_column_header_name)
                                temp[-1] = value
                                new_values.append(copy.copy(temp))
                            value_row_pos = 0
                            value_given = True
                            continue
                        if next_word == 'default' and i == 0:
                            is_default_value = True
                            default_value = elements[i+1]
                            default_value_db, default_value_type = api.to_database(float(elements[i+1]))
                            added = target_db.add_update_parameter_definition_item(entity_class_name=entity_class,
                                                                        name=second_word,
                                                                        default_value=default_value_db,
                                                                        default_type=default_value_type)
                            if added[1]:
                                try:
                                    target_db.commit_session("added default")
                                except:
                                    print("Default value add_update commit failed")
                            elements.pop(i)
                            continue
                        if not colon_sign and i > 1:
                            while len(elements) > i + 1:
                                temp = []
                                for dimen in range(len(param_listing[param][2])):
                                    element = elements.pop(i)
                                    temp.append(element)
                                    element = elements.pop(i)
                                temp.append(element)
                                new_values.append(copy.copy(temp))
                                element = elements.pop(i)
                                value_given = True
                            if new_values:
                                write_param(target_db, entity_class, param, alternative_name, new_values, param_listing[param])
                            if not value_given and is_default_value:
                                add_all_entity_combinations_to_class.append(entity_class)
                            break

                    # Keeping code to deal with 'in' in the param dimension defs - needs to be implemented
                        # if not param_dimen_start and not param_attributes_start:
                        #     param_name_alias.append(next_word)
                        # elif not param_dimen_end and not param_attributes_start:
                        #     if len(elements) > i + 2 and elements[i + 1] == "in":
                        #         param_dimen_candidate = elements[i + 2]
                        #         elements.pop(i)
                        #         elements.pop(i)
                        #     elif next_word != ',':
                        #         param_dimen_candidate = next_word
                        #     else:
                        #         continue
                        #     for set_name in set_names:
                        #         if param_dimen_candidate == set_name:
                        #             param_dimens.append(param_dimen_candidate)
                        #             break

        for entity_from_entity in entities_from_entities:
            [[to_entity_class, temp]] = entity_from_entity.items()
            [[from_entity_class, mapping]] = temp.items()
            for entity in target_db.get_entity_items(entity_class_name=from_entity_class):
                entity_dimens = []
                for m in mapping:
                    entity_dimens.append(entity["entity_byname"][m - 1])
                target_db.add_update_entity_item(entity_class_name=to_entity_class,
                                                element_name_list=tuple(entity_dimens))
        try:
            target_db.commit_session("Added entities from entities")
        except NothingToCommit:
            pass
            
    file.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit("You need to provide the following arguments 1. settings file 2. url of the target Spine database 3. file name for the osemosys data")
    with open(sys.argv[1], 'r') as yaml_file:
        settings = yaml.safe_load(yaml_file)
    url_db = settings["target_db"]
    if len(sys.argv) > 2:
        url_db = sys.argv[2]
    if len(sys.argv) > 3:
        file_name = sys.argv[3]
    param_dimens_file='param_dimens.yaml'
    read_mathprog_data(settings, url_db, file_name, param_dimens_file)