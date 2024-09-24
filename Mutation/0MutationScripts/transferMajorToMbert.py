import os
import json
import pandas as pd
from pathlib import Path
import subprocess
import shutil

software_testing_root_env = os.getenv("SOFTWARE_TESTING_ROOT")
if software_testing_root_env is None:
    raise EnvironmentError("The SOFTWARE_TESTING_ROOT environment variable is not set.")
SOFTWARE_TESTING_ROOT = Path(software_testing_root_env)
MAJOR_FILE_ORIGIN = SOFTWARE_TESTING_ROOT / "Mutation/TraditionalMutation/major/MutantRepo/Defects4J/Mutant4FaultyFileOrigin"
MAJOR_FILE = SOFTWARE_TESTING_ROOT / "Mutation/TraditionalMutation/major/MutantRepo/Defects4J/Mutant4FaultyFile"
SRC_PATH = SOFTWARE_TESTING_ROOT / "DataSet/Defects4J/D4J/src_path"
def get_versions(project):
    cmd = f"defects4j bids -p {project}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    versions = result.stdout.strip().split("\n")
    return versions
def get_src_path(Project, Version):
    Version = int(Version)
    path = SRC_PATH / f"{Project}-SrcPath.csv"
    print(f"读取{path}-{Project}-{Version}的SrcPath")
    df = pd.read_csv(path)
    SrcPath = df.loc[(df['Project'] == Project) & (df['Version'] == Version), 'SrcPath'].values[0]
    return SrcPath
def processLogFile(file_input_path, file_output_path, prefix_path,project,version):
    with open(file_input_path, "r") as file:
        mutants_log = file.readlines()

    mutants_data = []
    linenum_index_map = {}

    for line in mutants_log:
        line = line.strip()
        parts = line.split(":", )
        index = int(parts[0])
        mutation_type = parts[1]
        file_path = parts[4].split('@')[0]
        file_path = file_path.split('$')[0] 
        file_path = file_path.replace(".", "/")
        linenum = parts[5] 
        if linenum in linenum_index_map:
            linenum_index_map[linenum] += 1
        else:
            linenum_index_map[linenum] = 0
        linenum_index = linenum_index_map[linenum] 
        major_origin_file_path = f"{index}/{file_path}.java"
        standard_file_path = f"{MAJOR_FILE}/{project}/{project.lower()}_{version}_buggy/{prefix_path}/{file_path}/{linenum}/{linenum_index}"
        mutant_info = {
            "index": index,
            "mutation_type": mutation_type,
            "line": linenum,
            "line_index": linenum_index,
            "major_origin_file_path": major_origin_file_path,
            "standard_file_path": standard_file_path
        }
        print(mutant_info)
        mutants_data.append(mutant_info)

    with open(file_output_path, "w") as file:
        json.dump(mutants_data, file)
def processJsonFile(Json_File, project, version):
    with open(Json_File, "r") as file:
        mutants_data = json.load(file)
    
    for mutant in mutants_data:
        try:
            major_file_path = MAJOR_FILE_ORIGIN / f"{project}/{version}b" / mutant["major_origin_file_path"]
            standard_file_path = MAJOR_FILE / f"{project}/{version}b" / mutant["standard_file_path"]
            standard_file_path.mkdir(parents=True, exist_ok=True)  
            target_file_path = standard_file_path / major_file_path.name

            shutil.copy(major_file_path, target_file_path)
            
        except FileNotFoundError as e:
            print(f"File not found error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
def init():
    projects = ["Collections", "Compress", "Jsoup", "JacksonDatabind", "JxPath"]
    for project in projects:
        versionsnum = get_versions(project)
        for version in versionsnum:
            Log_Dir = MAJOR_FILE_ORIGIN / f"{project}/{version}b"
            Log_File = Log_Dir / "mutants.log"
            Json_File = Log_Dir / "mutants.json"
            print(Log_File, Json_File)
            src_path = get_src_path(project, version)
            processLogFile(Log_File, Json_File, src_path, project, version)
            processJsonFile(Json_File, project, version)
if __name__ == '__main__':
    init()
