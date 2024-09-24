import subprocess
import pandas as pd
from pathlib import Path
try:
    from .STEnvConfig import get_pathConfig  
except ImportError:
    from STEnvConfig import get_pathConfig  
    
def get_D4Jprojects(DatasetVersion="Custom"):
    if DatasetVersion == "v1.5":
        projects = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"]
    elif DatasetVersion == "Custom":
        projects = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"] + ["Cli", "Codec", "Csv", "Gson", "JacksonCore", "JacksonXml"]
    elif DatasetVersion == "v2.0":
        cmd = f"defects4j pids"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        projects = result.stdout.strip().split("\n")
        
    else:
        projects = ["Chart", "Closure", "Lang", "Math", "Mockito", "Time"]
    return projects
def get_D4Jversions(project):
    cmd = f"defects4j bids -p {project}"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    versions = result.stdout.strip().split("\n")
    
    return versions

def get_SrcPath4D4J(project, version):
    pathConfig = get_pathConfig()
    if pathConfig:
        
        D4J = Path(pathConfig["D4J"])
    
    SrcPath4Project = pd.read_csv(D4J / "src_path" / f"{project}-SrcPath.csv")
    SrcPath = SrcPath4Project.loc[SrcPath4Project["Version"] == int(version), "SrcPath"].item()
    return SrcPath

def get_TestCases4D4J(project, version):
    pathConfig = get_pathConfig()
    if pathConfig:
        try:
            D4J = Path(pathConfig["D4J"])
            file_path = D4J / "TestInfo" / "TestCase" / project / f"{project}_{version}_testcases.txt"
            
            if file_path.exists():
                with file_path.open('r', encoding='utf-8') as file:
                    lines = [line.strip() for line in file if line.strip()]  
                return lines
            else:
                print(f"File not found: {file_path}")
        except KeyError as e:
            print(f"Missing configuration for: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("No path configuration available.")

if __name__ == "__main__":
    projects = get_D4Jprojects()
    
    for project in projects:
        versions = get_D4Jversions(project)
        for version in versions:
            SrcPath = get_SrcPath4D4J(project, version)