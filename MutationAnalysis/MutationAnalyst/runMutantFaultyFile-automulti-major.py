import math
import os
import subprocess
import signal
import threading
import logging
import shutil
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import pdb
import json
import time
from pathlib import Path

software_testing_root_env = os.getenv("SOFTWARE_TESTING_ROOT")
if software_testing_root_env is None:
    raise EnvironmentError("The SOFTWARE_TESTING_ROOT environment variable is not set.")
SOFTWARE_TESTING_ROOT = Path(software_testing_root_env) 
MUTANT_FAULTYFILE = SOFTWARE_TESTING_ROOT/"Mutation/TraditionalMutation/major/MutantRepo/Defects4J/Mutant4FaultyFile" 

D4J_Origin = SOFTWARE_TESTING_ROOT/"DataSet/Defects4J/D4J/project_repository"
Mutant_Log_Faulty_File = SOFTWARE_TESTING_ROOT/"MutationAnalysis/MutantTestResult/TraditionalMutation/major/Defects4J/mutantlog_faulty_file"
Mutant_Testing_Log = SOFTWARE_TESTING_ROOT/"MutationAnalysis/MutantTestResult/TraditionalMutation/major/Defects4J/runMutantLog" 
Mutant_Test_Result_Faulty_File = SOFTWARE_TESTING_ROOT/"MutationAnalysis/MutantTestResult/TraditionalMutation/major/Defects4J/result4FaultFile"

lock = threading.Lock()

def setup_log(adr):
    logging.basicConfig(filename=adr, level=logging.DEBUG)
def mkFile(runMutantPath, project, version):
  runMutantPath = Path(runMutantPath)  
  for i in range(3):
    targetFile = runMutantPath / project / (version + 'b') / str(i)
    targetFile.mkdir(parents=True, exist_ok=True)
  return str(runMutantPath / project / (version + 'b'))  
def copyInitFile(initPath, targetPath):
  initPath = Path(initPath)
  targetPath = Path(targetPath)
  for i in range(3):
    tmptargetPath = targetPath / str(i)
    try:
        shutil.copytree(initPath, tmptargetPath)  
        print(f'复制到{tmptargetPath}完成')
    except Exception as e:
        print(f'复制到{tmptargetPath}失败: {e}')
def split_list(lst, n):
    length = len(lst)
    step = math.ceil(length / n)
    return [lst[i:i+step] for i in range(0, length, step)]
def findMutant(mutantPath):
  search_path = mutantPath
  file_list = []
  find_command = f"find {search_path} -type f -name '*.java'"

  result = subprocess.run(find_command, shell=True, stdout=subprocess.PIPE)

  for file in result.stdout.decode().split('\n'):
      if file:
          file_list.append(file)
  return file_list
def backup_file(file_path):
    file_path = Path(file_path)  
    bak_file_path = file_path.with_suffix(file_path.suffix + '.bak')  
    try:
        shutil.copy(file_path, bak_file_path)  
        with lock:
            logging.info(f"{file_path} 文件备份成功！")
    except IOError as e:
        with lock:
            logging.error(f"{file_path} 文件备份失败：{e}")
def replace_file(src, dst):
  try:
    shutil.copy(src, dst)
    
    with lock:
      logging.info("{} 替换为 {} 成功！".format(dst, src))
  except IOError as e:
    
    with lock:
      logging.error("{} 替换为 {} 失败！{}".format(dst, src, e))
def restore_file(file_path):
    file_path = Path(file_path)  
    bak_file_path = file_path.with_suffix(file_path.suffix + '.bak')  
    if bak_file_path.exists():  
        try:
            bak_file_path.replace(file_path)  
            with lock:
                logging.info(f'{file_path} 还原成功')
            return True
        except Exception as e:
            with lock:
                logging.error(f'{file_path} 还原失败：{e}')
            return False
    else:
        with lock:
            logging.error(f'备份文件不存在：{bak_file_path}')
        return False
def run_d4j_test(run_path, process_name):
    
    run_path = Path(run_path)
    
    cmd = ["defects4j", "test", "-w", str(run_path), "1>/dev/null", "2>&1"]
    
    timeout_seconds = 300
    try:
        start_time = time.time()
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, preexec_fn=os.setsid) as proc:
            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
                elapsed_time = time.time() - start_time
            except subprocess.TimeoutExpired:
                print(f"{run_path} 执行测试超时 {process_name}")
                with lock:
                    logging.error(f"{run_path} 执行测试超时 {process_name}")
                elapsed_time = timeout_seconds
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                return False, elapsed_time, "TIME_OUT"
            if proc.returncode == 0:
                print(f"{run_path} 执行测试成功 {process_name}")
                with lock:
                    logging.info(f"{run_path} 执行测试成功 {process_name}")
                return True, elapsed_time, "SUCC"
            else:
                print(f"{run_path} 执行测试失败 {process_name}")
                with lock:
                    logging.error(f"{run_path} 执行测试失败 {process_name}")
                return False, elapsed_time, "FAIL"
    except subprocess.CalledProcessError as e:
        print(f"{run_path} 执行测试失败")
        with lock:
            logging.error(f"{run_path} 执行测试失败")
            logging.error(f"错误信息：{e.stderr.decode()}")
        return False, elapsed_time
def saveResult(runPath, mutantTestResultPath, target_file_name):
    
    runPath = Path(runPath)
    mutantTestResultPath = Path(mutantTestResultPath)
    
    failtxt = runPath / "failing_tests"
    targetfailtxt = mutantTestResultPath / target_file_name
    try:
        
        shutil.move(failtxt, targetfailtxt)  
        with lock:
            logging.info(f"{failtxt} 转储 {target_file_name} 成功\n------")
    except Exception as e:
        with lock:
            logging.error(f"{failtxt} 转储 {target_file_name} 失败: {e}\n------")
def getRunMutantLog(pid,vid):
  
  runMutantLog_path = Mutant_Testing_Log/pid/f"{pid}-{vid}.json"
  os.makedirs(os.path.dirname(runMutantLog_path), exist_ok=True)
  
  if not os.path.exists(runMutantLog_path):
    with open(runMutantLog_path, 'w', encoding='utf-8') as file:
      
      json.dump({
         "mutantRecord":{},
         "mutantTimeRecord":{},
         "success_mutant_num":{}
      }, file) 
  with open(runMutantLog_path, 'r', encoding='utf-8') as file:
    data = json.load(file)
    return data

def writeRunMutantLog(pid, vid, data):
    runMutantLog_path = Mutant_Testing_Log / pid / f"{pid}-{vid}.json"
    
    runMutantLog_path.parent.mkdir(parents=True, exist_ok=True)
    
    runMutantLog_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
def execMutant(pid, mutantPath, process_name, D4J_Repo_Path): 
    for i in mutantPath:
        mutantList = findMutant(i) 
        vid = i.split("_")[1]
        
        adr = Mutant_Log_Faulty_File/pid/f"{pid}-{vid}.log"  
        adr.parent.mkdir(parents=True, exist_ok=True)  
        setup_log(adr)
        runMutantLog = getRunMutantLog(pid, vid)
        sourceFilePath = D4J_Repo_Path / pid / f"{vid}b" 
        tmpFilePath = Path(f"/tmp/{pid}/{pid.lower()}_{vid}_buggy")
        tmpFilePath.parent.mkdir(parents=True, exist_ok=True)
        
        if tmpFilePath.exists():
            shutil.rmtree(tmpFilePath)
        
        shutil.copytree(sourceFilePath, tmpFilePath)
        for item in mutantList:
            file_path = Path(item) 
            src_start_pos = len(Path(i).parts) 
            new_path = Path(*file_path.parts[src_start_pos:-3])  
            target_path = tmpFilePath / new_path.with_suffix('.java') 
            target_file_name = "-".join(file_path.parts[src_start_pos:-1])
            
            mutantLine = '-'.join(target_file_name.split('-')[:-1]) 
            if str(file_path) in runMutantLog["mutantRecord"]:
                print(f"------------已经执行过变异体项目:{file_path}-------------------")
                continue
            backup_file(target_path) 
            replace_file(file_path, target_path) 
            runresult, elapsed_time, flag = run_d4j_test(tmpFilePath, process_name) 
            print(f"----------变异执行完成:{mutantLine}-runresult为:{runresult}---------")
            restore_file(target_path) 
            runMutantLog["mutantRecord"][str(file_path)] = flag 
            runMutantLog["mutantTimeRecord"][str(file_path)] = elapsed_time
            if runresult: 
                if mutantLine not in runMutantLog["success_mutant_num"]: 
                    runMutantLog["success_mutant_num"][mutantLine] = 1
                else:
                    runMutantLog["success_mutant_num"][mutantLine] += 1
                
                mutantTestResultPath = Mutant_Test_Result_Faulty_File / pid /f"{vid}b"  
                mutantTestResultPath.mkdir(parents=True, exist_ok=True)
                saveResult(tmpFilePath, mutantTestResultPath, target_file_name)
            writeRunMutantLog(pid,vid,runMutantLog) 
def initProgram(runMutantPath, project, version, initPath):
    runMutantPath = Path(runMutantPath)  
    initPath = Path(initPath)
    targetPath = mkFile(runMutantPath, project, version)
    copyInitFile(initPath, targetPath)
def startProcess(mutantPath, pid, svid, evid, num_threads=6, D4J_Repo_Path=None):
    num_threads = num_threads
    total_versions = evid - svid + 1
    len1 = math.ceil(total_versions / num_threads)
    versionLists = [[] for _ in range(num_threads)]
    No = set()

    mutantPath = Path(mutantPath)  

    for i in range(total_versions):
        version = svid + i
        if str(version) in No:
            continue
        thread_no = i // len1
        if thread_no >= num_threads:
            thread_no = num_threads - 1
        
        versionPath = mutantPath / pid / f"{pid.lower()}_{version}_buggy"
        
        if not versionPath.exists():
            print(f"versionPath not exist: {versionPath}")
            continue
        versionLists[thread_no].append(versionPath)
    with ProcessPoolExecutor(max_workers=num_threads) as pool:
        futures = [pool.submit(execMutant, pid, [str(vp) for vp in versionList], f'process{index}', D4J_Repo_Path) for index, versionList in enumerate(versionLists)]
        for future in futures:
            future.result()
if __name__ == '__main__':
    D4J_Repo_Path = D4J_Origin
    startProcess(MUTANT_FAULTYFILE, "Chart", 1, 26, num_threads=4, D4J_Repo_Path=D4J_Repo_Path)
