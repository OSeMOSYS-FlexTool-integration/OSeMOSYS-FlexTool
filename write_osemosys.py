import sys
import yaml
from pathlib import Path
sys.path.insert(0, '.') #needed if using the zip toolbox
sys.path.insert(0,str(Path(__file__).parent.parent / "ines-tools"/ "ines_tools"/ "tool_specific"/ "mathprog")) 
from read_mathprog_model_structure import read_mathprog_structure
from write_mathprog_model_data import write_mathprog_data

from pathlib import Path

if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.exit("You need to provide the url of the source Spine database as the second argument")
    url_db = sys.argv[2]
    with open(sys.argv[1], 'r') as yaml_file:
        settings = yaml.safe_load(yaml_file)
    if len(sys.argv) < 3:
        sys.exit("You need to provide the osemosys code as the third argument")
    code_file_name = sys.argv[3]
    param_dimens_file = str(Path(__file__).parent / 'param_dimens.yaml')

    read_mathprog_structure(settings, url_db, code_file_name, param_dimens_file, write_to_db=False)
    print("Added model structure")

    with open(param_dimens_file, 'r') as yaml_file:
        param_listing = yaml.safe_load(yaml_file)

    with open(settings["new_model_name"], 'w+') as output_file:
        write_mathprog_data(url_db, output_file, param_listing)
    print("Added model data")
