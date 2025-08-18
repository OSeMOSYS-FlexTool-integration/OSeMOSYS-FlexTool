import sys
import shutil
from pathlib import Path
import spinedb_api as api
from collections import defaultdict
from spinedb_api.exception import NothingToCommit
from sqlalchemy.exc import DBAPIError
from itertools import accumulate
import os
import csv
import yaml


def main(flextool_input):
    current_dir = Path().parent
    result_files_path = current_dir / "results"
    with api.DatabaseMapping(flextool_input) as target_db:
        target_db.add_alternative_item(name=default_alternative)
        one_unit_capacities = target_db.get_parameter_value_items(entity_class_name="unit", parameter_definition_name="virtual_unitsize")
        
        capacity = defaultdict(list)
        with open(result_files_path / "TotalCapacityAnnual.csv", 'r') as result_file:
            filereader = csv.reader(result_file, delimiter=',')
            header = next(filereader)
            while True:
                try:
                    row = next(filereader)
                    unit_name = f'{row[0]}__{row[1]}'
                    capacity[unit_name].append(row[2:])
                except StopIteration:
                    break
        for unit_name, values in capacity.items():
            unit_capacity = None
            for unit in one_unit_capacities:
                if unit["entity_byname"][0] == unit_name:
                    unit_capacity = api.from_database(unit["value"], unit["type"])
                    break
            if not unit_capacity:
                print(f"Unit {unit_name} not found in database, skipping.")
                continue
            periods = [str(x[0]) for x in values]
            values = [round(float(x[1]) / unit_capacity * capacity_unit_ratio, 4) for x in values]
            timeblocks_map = api.Map(indexes=periods, values = values, index_name="period")
            p_value, p_type = api.to_database(timeblocks_map)
            added, updated, error = target_db.add_update_item("parameter_value", 
                                                     entity_class_name="unit",
                                                     entity_byname=(unit_name,),
                                                     parameter_definition_name="existing",
                                                     alternative_name=default_alternative,
                                                     value=p_value,
                                                     type=p_type)
            if error:
                sys.exit("Could not capacities to flextool database: " + error)
        
        one_storage_capacities = target_db.get_parameter_value_items(entity_class_name="node", parameter_definition_name="virtual_unitsize")
        storage_capacity_results = defaultdict(list)
        with open(result_files_path / "NewStorageCapacity.csv", 'r') as result_file:
            filereader = csv.reader(result_file, delimiter=',')
            header = next(filereader)
            while True:
                try:
                    row = next(filereader)
                    unit_name = f'{row[0]}__{row[1]}'
                    storage_capacity_results[unit_name].append(row[2:])
                except StopIteration:
                    break
        for storage_name, values in storage_capacity_results.items():
            storage_capacity = None
            for storage in one_storage_capacities:
                if storage["entity_byname"][0] == storage_name:
                    storage_capacity = api.from_database(storage["value"], storage["type"])
                    break
            if not storage_capacity:
                print(f"storage {storage_name} not found in database, skipping.")
                continue
            periods = [str(x[0]) for x in values]
            accumulated_storage_capacity = list(accumulate(values))
            values = [round(float(x[1]) / storage_capacity * storage_unit_ratio, 4) for x in accumulated_storage_capacity]
            timeblocks_map = api.Map(indexes=periods, values = values, index_name="period")
            p_value, p_type = api.to_database(timeblocks_map)
            added, updated, error = target_db.add_update_item("parameter_value", 
                                                     entity_class_name="node",
                                                     entity_byname=(unit_name,),
                                                     parameter_definition_name="existing",
                                                     alternative_name=default_alternative,
                                                     value=p_value,
                                                     type=p_type)
            if error:
                sys.exit("Could not capacities to flextool database: " + error)

        try:
            target_db.commit_session("Added scenarios and alternatives")
        except NothingToCommit:
            print("Nothing to commit")
        except DBAPIError as e:
            print(e)

if __name__ == "__main__":
    settings_file = sys.argv[1]
    flextool_input = sys.argv[2]
    with open(settings_file, 'r') as yaml_file:
        settings = yaml.safe_load(yaml_file)

    default_alternative = "results_from_Osemosys"
    
    default_unit_size = float(settings["default_unit_size"])

    capacity_unit_ratio = float(settings["capacity_unit_to_MW_ratio"])
    storage_unit_ratio = float(settings["storage_capacity_unit_to_MWh_ratio"])
    demand_unit_ratio = float(settings["demand_unit_to_MWh_ratio"])
    investment_unit_ratio = float(settings["investment_unit_to_CUR/MW_ratio"])
    alternative_name = "Osemosys_results"
    main(flextool_input)