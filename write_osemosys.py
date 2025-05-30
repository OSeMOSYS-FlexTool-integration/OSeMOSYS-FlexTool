import sys
import yaml
sys.path.insert(0, '.') #needed if using the zip toolbox
import ines_tools_mathprog.read_mathprog_model_structure as structure
import ines_tools_mathprog.write_mathprog_model_data as data
from pathlib import Path

if __name__ == "__main__":

    if len(sys.argv) < 2:
        exit("You need to provide the url of the source Spine database as an argument")
    url_db = sys.argv[2]
    with open(sys.argv[1], 'r') as yaml_file:
        settings = yaml.safe_load(yaml_file)
    
    code_file_name = str(Path(__file__).parent / "mathprog_files" / settings["model_code"])
    param_dimens_file = str(Path(__file__).parent / "mathprog_files" / 'param_dimens.yaml')

    structure.read_mathprog_structure(settings, url_db, code_file_name, param_dimens_file, write_to_db=False)
    print("Added model structure")

    with open(str(Path(__file__).parent / "mathprog_files" / 'param_dimens.yaml'), 'r') as yaml_file:
        param_listing = yaml.safe_load(yaml_file)

    with open(settings["new_model_name"], 'w+') as output_file:
        data.write_mathprog_data(url_db, output_file, param_listing)
    print("Added model data")
