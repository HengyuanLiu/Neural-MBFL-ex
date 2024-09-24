import os
import subprocess
import shutil
from pathlib import Path
from time import sleep

software_testing_root_env = os.getenv("SOFTWARE_TESTING_ROOT")
if software_testing_root_env is None:
    raise EnvironmentError("The SOFTWARE_TESTING_ROOT environment variable is not set.")
SOFTWARE_TESTING_ROOT = Path(software_testing_root_env)

D4J_Repo = SOFTWARE_TESTING_ROOT / "DataSet/Defects4J/D4JClean/d4jclean"
TEMP_DIR = Path("/tmp")
TARGET_DIR = SOFTWARE_TESTING_ROOT / "Mutation/TraditionalMutation/major/MutantRepo/Defects4J/Mutant4FaultyFileOrigin"

def run_major_mutation(project, version, project_version_path):
    cmd = [
        "bash", 
        "/home/rs/WorkEx/Projects/SoftwareTesting/Mutation/0MutationScripts/MajorMutation.sh", 
        project, 
        str(version),
        project_version_path.as_posix()
    ]
    try:
        with subprocess.Popen(cmd, cwd=project_version_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True) as proc:
            stdout, stderr = proc.communicate(timeout=600)
            if proc.returncode != 0:
                print(f"Mutation failed for {project_version_path}: {stderr}")
                return False
            print(f"Mutation succeeded for {project_version_path}")
            return True
    except subprocess.TimeoutExpired:
        print(f"Mutation timed out for {project_version_path}")
        proc.kill()
        return False
    except Exception as e:
        print(f"Error during mutation: {str(e)}")
        return False

def init(pid, svid, evid):
    for vid in range(svid, evid + 1):
        if pid in ["Collections", "JxPath", "JacksonDatabind"]:
            original_path = D4J_Repo / f"{pid}/{pid.lower()}_{vid}_buggy"
        else:
            original_path = D4J_Repo / f"{pid}/{vid}b"
        
        temp_path = TEMP_DIR / pid / f"{vid}b"
        
        if original_path.exists():
            shutil.copytree(original_path, temp_path, dirs_exist_ok=True)
            print(f"{original_path}复制成功！")
            
            if run_major_mutation(pid, vid, temp_path):
                mutants_path = temp_path / ".mutants"
                renamed_mutants_path = temp_path / f"{vid}b"
                mutants_path.rename(renamed_mutants_path)
                target_dir = TARGET_DIR / pid / f"{vid}b"
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(str(renamed_mutants_path), str(target_dir), dirs_exist_ok=True)

                mutants_log_path = temp_path / "mutants.log"
                target_dir = TARGET_DIR / pid / f"{vid}b"
                shutil.copy2(str(mutants_log_path), str(target_dir))
            
            temp_path1 = TEMP_DIR / pid
            print(temp_path1)
            shutil.rmtree(temp_path1)
        else:
            print(f"Project version not found: {original_path}")

if __name__ == '__main__':
    init("Compress", 1, 47)
    init("Jsoup", 1, 93)