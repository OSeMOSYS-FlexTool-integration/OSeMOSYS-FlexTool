import subprocess
import sys
import logging
import yaml
from pathlib import Path

def run_osemosys(modelfile, infile, outfile):
    logger = logging.getLogger(__name__)
    directory = Path(__file__).parent
    glpsol_dir = directory / "glpsol_files"
    glpsol_cmd = [str(glpsol_dir / "glpsol.exe"), '-m', str(directory / "mathprog_files" / modelfile), '-d',  str(directory / infile), '--cbg','-w', str(directory / outfile)]
    completed = subprocess.run(glpsol_cmd)
    if completed.returncode != 0:
        logger.error(f'{completed.returncode}')
        sys.exit(completed.returncode)

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as yaml_file:
        settings = yaml.safe_load(yaml_file)
    modelfile = settings["model_code"]
    infile = settings["new_model_name"]
    outfile = settings["solution_file"]
    run_osemosys(modelfile, infile, outfile)