import multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import os
import threading
import subprocess
import math
import time
import json
import shutil
from traceback import print_exc
from SubProcessEnvTest import set_java_version, check_java_version

locka = threading.Lock()

Java11Env = set_java_version("11")
check_java_version(Java11Env)

def get_file_lines(file_path):
    with open(file_path, 'r') as f:
        lines = sum(1 for line in f)
    return lines

def mBert4FILE(source_file_name, line_to_mutate, mutants_directory, max_num_of_mutants=None, method_name=None):
    if max_num_of_mutants is None:
        max_num_of_mutants = 50
    Path(mutants_directory).mkdir(parents=True, exist_ok=True)
    if method_name is None:
        mBert_command = ["bash", "./mBERT.sh", "-in={}".format(source_file_name), "-out={}".format(mutants_directory), "-N={}".format(max_num_of_mutants), "-l={}".format(line_to_mutate)]
        print(' '.join(mBert_command))
        result = subprocess.run(mBert_command, 
                            cwd="/home/rs/WorkEx/Projects/SoftwareTesting/Mutation/NeuralMutation/mbert/MutationTool/mBERT", 
                            env=Java11Env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
        print(result.stderr, result.returncode)
        return result.returncode

project_repo_path = "/home/rs/WorkEx/Projects/SoftwareTesting/DataSet/Defects4J/D4J/project_repository"
faulty_file_path = "/home/rs/WorkEx/Projects/SoftwareTesting/DataSet/Defects4J/D4JClean/faultyFile"
project_mutant_repository_path = "/home/rs/WorkEx/Projects/SoftwareTesting/Mutation/NeuralMutation/mbert/MutantRepo/Defects4J/Mutant4FaultyFile"

Path(project_mutant_repository_path).mkdir(parents=True, exist_ok=True)
version_suffix = "b"

def getMutant(projectList, versionList, process_name):
    for project_id in projectList:
        for version_id in versionList:
            project_version_mutant_repository = f"{project_mutant_repository_path}/{project_id}/{project_id.lower()}_{version_id}_{'buggy' if version_suffix == 'b' else 'fixed'}"
            Path(project_version_mutant_repository).mkdir(parents=True, exist_ok=True)

            log_file_path = f"{project_version_mutant_repository}/mutate_log.txt"
            if not os.path.exists(log_file_path):
                with open(log_file_path, "w") as log_file:
                    json.dump({"time_cost": 0, "mutant_generation_info": {}, "mutate_percentage": {}}, log_file)

            with open(log_file_path, "r") as log_file:
                log_data = json.load(log_file)
            time_cost = log_data["time_cost"]
            mutant_generation_info = log_data["mutant_generation_info"]
            mutate_percentage = log_data["mutate_percentage"]

            try:
                with open(f"{faulty_file_path}/{project_id}.json", "r") as f:
                    code_scope = json.load(f)[f"{project_id}-{version_id}"]
            except FileNotFoundError:
                print("FileNotFoundError 文件没有找到")
                continue

            log_file_name = f"{project_version_mutant_repository}/{project_id}_{version_id}{version_suffix}_mutate_log.txt"
            locka.acquire()
            fp = open(log_file_name, mode="a+", encoding="UTF-8")
            fp.write("")
            fp.close()
            locka.release()

            for i in code_scope:
                src = i
                source_file_name = f"{project_repo_path}/{project_id}/{project_id.lower()}_{version_id}_buggy{src}"
                if not os.path.exists(source_file_name):
                    continue
                lines_num = get_file_lines(source_file_name)
                for line_to_mutate in range(1, lines_num + 1):
                    mutants_directory = f"{project_version_mutant_repository}{src[:-5]}/{line_to_mutate}"
                    if f"{project_version_mutant_repository}{src[:-5]}" not in mutant_generation_info.keys():
                        mutant_generation_info[f"{project_version_mutant_repository}{src[:-5]}"] = []
                        mutate_percentage[f"{project_version_mutant_repository}{src[:-5]}"] = "0%"

                    if f"{line_to_mutate}" in mutant_generation_info[f"{project_version_mutant_repository}{src[:-5]}"]:
                        print(f"-------------跳过！已经完成生成{project_id}-{version_id}-{line_to_mutate}---------------")
                        continue
                    else:
                        if os.path.exists(mutants_directory):
                            shutil.rmtree(mutants_directory)
                        print(f"-------------开始变异{project_id}-{version_id}-行号-{line_to_mutate}---------------")

                    time_start = time.time()
                    mutate_flag = mBert4FILE(source_file_name=source_file_name, line_to_mutate=line_to_mutate, mutants_directory=mutants_directory)
                    locka.acquire()
                    fp = open(log_file_name, mode="a+", encoding="UTF-8")
                    fp.write("{} : line {} : {} Use jincheng {}\n".format(src, line_to_mutate, "PASS" if mutate_flag == 0 else "ERROR", process_name))
                    fp.close()
                    locka.release()
                    print("{} : line {} : {} Use jincheng {}".format(src, line_to_mutate, "PASS" if mutate_flag == 0 else "ERROR", process_name))
                    time_end = time.time()
                    locka.acquire()
                    fp = open(log_file_name, mode="a+", encoding="UTF-8")
                    fp.write("Mutate {}-{}-{} Over! Use jincheng{} [time cost:{:.2f}]\n".format(project_id, version_id, src, process_name, time_end - time_start))
                    fp.write("-" * 50 + "\n")
                    fp.close()
                    locka.release()
                    print("Mutate {}-{}-{} Over! Use jincheng{} [time cost:{:.2f}]".format(project_id, version_id, src, process_name, time_end - time_start))
                    print("-" * 50 + "\n")

                    time_cost += time_end - time_start
                    mutant_generation_info[f"{project_version_mutant_repository}{src[:-5]}"].append(f"{line_to_mutate}")
                    mutate_percentage[f"{project_version_mutant_repository}{src[:-5]}"] = "{:.2f}%".format(len(mutant_generation_info[f"{project_version_mutant_repository}{src[:-5]}"]) / lines_num * 100)

                    with open(log_file_path, "w") as log_file:
                        json.dump({"time_cost": time_cost, "mutant_generation_info": mutant_generation_info, "mutate_percentage": mutate_percentage}, log_file)
def startProcess(projectList, svid, evid, num_threads=10):
    total_versions = evid - svid + 1
    len1 = math.ceil(total_versions / num_threads)
    versionLists = [[] for _ in range(num_threads)]
    No = set()

    for i in range(total_versions):
        version = svid + i
        if str(version) in No:
            continue
        thread_no = i // len1
        if thread_no >= num_threads:
            thread_no = num_threads - 1
        versionLists[thread_no].append(str(version))

    print(versionLists)

    with ProcessPoolExecutor(max_workers=num_threads) as pool:
        futures = [pool.submit(getMutant, projectList, versionList, f'process{index}') for index, versionList in enumerate(versionLists)]
        for future in futures:
            future.result()

def getMutant(projectList, versionList, process_name):
    # The actual implementation of getMutant is omitted as it was not provided in the original code snippet
    pass

if __name__ == '__main__':
    Project_ID = ["JacksonDatabind"]
    startProcess(Project_ID, 1, 112, num_threads=12)
    