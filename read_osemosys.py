import sys
import yaml
from pathlib import Path
sys.path.insert(0, '.') #needed if using the zip toolbox
import ines_tools_mathprog.read_mathprog_model_structure as structure
import ines_tools_mathprog.read_mathprog_model_data as data


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("You need to provide the following arguments 1. settings file 2. url of the target Spine database 3. Osemosys-file 4.file name for the osemosys data")

    with open(sys.argv[1], 'r') as yaml_file:
        settings = yaml.safe_load(yaml_file)
    url_db = settings["target_db"]
    if len(sys.argv) > 2:
        url_db = sys.argv[2]
    if len(sys.argv) > 3:
        code_file_name = sys.argv[3]
    if len(sys.argv) > 4:
        data_file_name = sys.argv[4]
    param_dimens_file = str(Path(__file__).parent / "mathprog_files" / 'param_dimens.yaml')

    structure.read_mathprog_structure(settings, url_db, code_file_name, param_dimens_file)
    print("Added model structure")
    data.read_mathprog_data(settings, url_db, data_file_name, param_dimens_file)
    print("Added model data")
