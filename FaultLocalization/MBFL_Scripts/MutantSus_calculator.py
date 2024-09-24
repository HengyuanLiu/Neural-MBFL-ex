import ast
import csv
import glob
import json
import os
import pathlib
from pathlib import Path
import subprocess
import pandas as pd
from SusFormulas import F_Sus
def get_pathConfig(env_var_name="SoftwareTestingPathConfig"):
    if env_var_name in os.environ:
        pathConfg_path = os.environ[env_var_name]
        print(f"获取到环境变量 {env_var_name} 的值为: {pathConfg_path}")
    else:
        print(f"未找到环境变量 {env_var_name}")
        return None
    if os.path.isfile(pathConfg_path) and os.access(pathConfg_path, os.R_OK):
        print(f"JSON 文件 {pathConfg_path} 存在并可读")
        try:
            
            with open(pathConfg_path, 'r') as pathConfg_fp:
                pathConfg = json.load(pathConfg_fp)
            print("成功加载 JSON 数据")
            return pathConfg
        except (json.JSONDecodeError, IOError) as e:
            
            print(f"加载 JSON 数据失败: {e}")
            pass
    else:
        print(f"JSON 文件 {pathConfg_path} 不存在或无读权限")
    return None
def get_projects():
    cmd = f"defects4j pids"
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    projects = result.stdout.strip().split("\n")
    print(f"获取到的项目列表: {projects}")
    return projects
def get_versions(project):
    cmd = f"defects4j bids -p {project}"
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    versions = result.stdout.strip().split("\n")
    print(f"项目 {project} 的版本列表: {versions}")
    return versions
class DataHandler:
    def __init__(self, sheet_names):
        
        self.dfs = {name: pd.DataFrame(columns=['mutant_tool','project','version','code_entity','linenum', 'mutant_id', 'akf', 'akp', 'anf', 'anp', 'f2p', 'p2f', 'Sus']) for name in sheet_names}

    def add_data(self, sheet_name, data_dict):
        
        self.dfs[sheet_name] = self.dfs[sheet_name].append(data_dict, ignore_index=True)

    def save_data(self, filename):
        
        with pd.ExcelWriter(filename) as writer:
            for name, df in self.dfs.items():
                df.to_excel(writer, sheet_name=name, index=False)
                
    def merge_data(self, other_handler):
        
        for sheet_name, df in other_handler.dfs.items():
            if sheet_name in self.dfs:
                
                self.dfs[sheet_name] = pd.concat([self.dfs[sheet_name], df]).reset_index(drop=True)
            else:
                
                self.dfs[sheet_name] = df
def get_non_txt_files(folder_path):
  files = glob.glob(os.path.join(folder_path, "*"))
  non_txt_files = [os.path.basename(f) for f in files if not f.endswith('.txt') and os.path.isfile(f)]
  return non_txt_files
def is_folder_empty(folder_path):
    with os.scandir(folder_path) as entries:
        return not any(entries)  
def find_test_txt_files(file_path, txt_name):
  result = subprocess.run(["find", file_path, "-name", txt_name + ".txt"], stdout=subprocess.PIPE)
  txt_files = result.stdout.decode("utf-8").strip().split("\n")
  return txt_files
def read_txt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines]
    return lines
def get_init_test_result(cover_path):
  tests_txt = find_test_txt_files(cover_path, "all_tests")
  tests_result_txt = find_test_txt_files(cover_path, "inVector")
  
  test_result = {}
  num = 0
  for item in range(len(tests_txt)):
    test_list = read_txt_file(tests_txt[item]) 
    result_list = read_txt_file(tests_result_txt[item])
    
    for test_item in range(len(test_list)):
      
      test_result[str(test_list[test_item])] = result_list[test_item]
      if str(result_list[test_item]) =='1':
         num += 1
  return test_result
def mutant_test(filename):
    with open(filename) as f:
        lines = f.readlines()

    processed_lines = []
    for line in lines:
        line = line.strip()
        left_idx = line.find("(")
        right_idx = line.find(")")
        if left_idx != -1 and right_idx != -1:
            class_name = line[:left_idx].split(".")[-1]
            method_name = line[left_idx+1:right_idx].replace(",", "
            processed_line = f"{method_name}
            processed_lines.append(processed_line)

    return processed_lines
def get_MutantSus(handler, pid, vid, mutant_tool, kill_type, d4jclean_path, buggy_result_path, mutant_result_path):
    
    d4jclean_path = d4jclean_path.as_posix()  
    buggy_result_path = buggy_result_path.as_posix()
    mutant_result_path = mutant_result_path.as_posix()

    print(d4jclean_path, os.path.exists(d4jclean_path))
    print(d4jclean_path + '/all_tests', os.path.exists(d4jclean_path + '/all_tests'))
    print(buggy_result_path, os.path.exists(buggy_result_path))
    print(mutant_result_path, os.path.exists(mutant_result_path))
    if not os.path.exists(d4jclean_path) or not os.path.exists(buggy_result_path) or not os.path.exists(mutant_result_path):
        print("必要路径缺失")
        return 1
    if not os.path.exists(d4jclean_path + '/all_tests'):
        print("必要文件缺失")
        return 1

    print(d4jclean_path, not is_folder_empty(d4jclean_path))
    print(buggy_result_path, not is_folder_empty(buggy_result_path))
    print(mutant_result_path, not is_folder_empty(mutant_result_path))
    if is_folder_empty(d4jclean_path) or is_folder_empty(buggy_result_path) or is_folder_empty(mutant_result_path):
        print("必要路径为空")
        return 1
    mixtest = mutant_test(d4jclean_path + '/all_tests') 
    mutant_result_json = get_non_txt_files(mutant_result_path) 

    f2p = p2f = 0
    f2p_test = []
    p2f_test = []
    
    for item in mutant_result_json:
        
        line_name = "-".join(item.split("-")[:-1]) 
        
        with open(mutant_result_path + '/' + item) as f:
            data = json.load(f)
            
        with open(buggy_result_path + '/failing_tests.json') as f:
            faildata = json.load(f) 
        
        kf = nf = kp = np = 0
        for test_item in mixtest:
            
            if test_item not in faildata:
                if test_item in data:
                    kp += 1
                    p2f_test.append(test_item)
                else:
                    np += 1
            
            else:
                if test_item in data:                    
                    if kill_type == "kill_type3":                       
                        if data[test_item]['type3'] == faildata[test_item]['type3']:
                            nf += 1
                        else:
                            kf += 1
                            f2p_test.append(test_item)
                    else: 
                        print("Warning: Not valid kill_type:", kill_type)
                        nf += 1
                else:
                    kf += 1
                    f2p_test.append(test_item)
        for formula in F_Sus.keys():
            try: 
                int(item.split('-')[-2])
            except:
                print(item)
                breakpoint()
            data_dict = {
                'mutant_tool': mutant_tool,
                'project': pid,
                'version': int(vid),
                'linenum': int(item.split('-')[-2]),
                'code_entity': "-".join(line_name.split("-")[:-1]),
                'mutant_id': item[:-5],
                'akf': kf,
                'akp': kp,
                'anf': nf,
                'anp': np,
                'f2p': None,
                'p2f': None,
                'Sus': None
            }
            
            handler.add_data(formula, data_dict)

    for formula in F_Sus.keys():
        
        kf_nf_values = handler.dfs[formula]['akf'] + handler.dfs[formula]['anf']
        assert kf_nf_values.nunique() == 1, "kf + nf 不是每行都相等"
        kp_np_values = handler.dfs[formula]['akp'] + handler.dfs[formula]['anp']
        assert kp_np_values.nunique() == 1, "kp + np 不是每行都相等"

    f2p = len(set(f2p_test))
    p2f = len(set(p2f_test))
    for formula in F_Sus.keys():
        handler.dfs[formula]['f2p'] = f2p
        handler.dfs[formula]['p2f'] = p2f
        handler.dfs[formula]['Sus'] = handler.dfs[formula].apply(
            lambda row: F_Sus[formula](
                row['akf'], row['akp'], row['anf'], row['anp'], row['f2p'], row['p2f']
            ),
            axis=1
        )
    return 0

def get_MutantSus_bySettings(
    dataset,
    project,
    version,
    mutation_type,
    mutant_tool,
    kill_type, 
    clean_path, 
    buggy_result_path,
    test_result_path,
    rewrite=True
):
    
    params = {
        'dataset': dataset,
        'project': project,
        'version': version,
        'mutation_type': mutation_type,
        'mutant_tool': mutant_tool,
        'kill_type': kill_type,
        'clean_path': clean_path,
        'buggy_result_path': buggy_result_path,
        'test_result_path': test_result_path,
        'rewrite': rewrite,
    }
    for name, value in params.items():
        print(f"{name}: {value}")
        
    mutantSusResultPath = f"{MutantSusPath}/{granularity}/{dataset}/{mutation_type}/{mutant_tool}/{kill_type}/{project}/{project}_{version}.xlsx"
    mutantSusResultPath = Path(mutantSusResultPath)
    
    result_json_path = test_result_path / mutation_type / mutant_tool / dataset / "result4FaultFile_json"

    if rewrite or not mutantSusResultPath.exists():

        if not mutantSusResultPath.parent.exists():
            mutantSusResultPath.parent.mkdir(parents=True, exist_ok=True)
            print(f"目录 {mutantSusResultPath.parent} 不存在，已创建。")

        sheet_names = list(F_Sus.keys())

        project_version_handler = DataHandler(sheet_names)  
        exit_code = get_MutantSus(
            project_version_handler, 
            project,
            str(version),
            mutant_tool,
            kill_type, 
            clean_path / f"{project}/{version}b", 
            buggy_result_path / f"{project}/{version}b",
            result_json_path / f"{project}/{version}b"
        )
        if exit_code == 0:
            project_version_handler.save_data(
                mutantSusResultPath.as_posix()
            )
    
    else:
        print(f"{mutantSusResultPath} 已经生成完毕，跳过。")

if __name__ == '__main__':
    Debug=False
    rewrite=True

    pathConfig = get_pathConfig()
    if pathConfig:
        
        MutantSusPath = Path(pathConfig["MBFL_Sus"])
        MutantTestResultPath = Path(pathConfig["MutantTestResult"])
    
    def costomize_pathConfig4Project(project):
        pathConfig = get_pathConfig()
        if pathConfig:
            MutantSusPath = Path(pathConfig["MBFL_Sus"])
            MutantTestResultPath = Path(pathConfig["MutantTestResult"])
        
            D4JClean = Path(pathConfig["D4J"])
            
            clean_path = D4JClean / "project_repository"
            buggy_result_path = D4JClean / "FaultInfo/FailingTest/FailingTest4ProjectVersions"
            test_result_path = MutantTestResultPath
        return MutantSusPath, MutantTestResultPath, D4JClean, clean_path, buggy_result_path, test_result_path
        
    mutation_types = ["NeuralMutation", "TraditionalMutation"] 
    MutantTools = {
        "NeuralMutation": ["mBERT"],
        "TraditionalMutation": ["major"]
    }

    KillTypes = ["kill_type3"]

    dataset = "Defects4J"

    granularity = "Mutant"
    
    if Debug:
        project = "Jsoup"
        version = 1

        mutation_type = "NeuralMutation"
        mutant_tool = "mBERT"
        kill_type = "kill_type3"

        MutantSusPath, MutantTestResultPath, D4JClean, clean_path, buggy_result_path, test_result_path = costomize_pathConfig4Project(
            project
        )

        get_MutantSus_bySettings(
            dataset,
            project,
            version,
            mutation_type,
            mutant_tool,
            kill_type, 
            clean_path, 
            buggy_result_path,
            test_result_path,
            rewrite
        )
    else:
        for kill_type in KillTypes:
            for mutation_type, mutant_tools in MutantTools.items():
                for mutant_tool in mutant_tools:
                    
                    if dataset == "Defects4J":
                        projects = get_projects()
                        print(f"获取到的项目总数: {len(projects)}")
                        
                        for idx, project in enumerate(projects, start=1):
                            print("~"*50)
                            print(f"正在处理第 {idx} 个项目: {project}")

                            versions = get_versions(project)
                            print(f"该项目的版本数量: {len(versions)}")
                            for version in versions:
                                print("-"*50)
                                print(f"正在处理版本号 {version}")

                                MutantSusPath, MutantTestResultPath, D4JClean, clean_path, buggy_result_path, test_result_path = costomize_pathConfig4Project(
                                    project
                                )

                                get_MutantSus_bySettings(
                                    dataset,
                                    project,
                                    version,
                                    mutation_type,
                                    mutant_tool,
                                    kill_type, 
                                    clean_path, 
                                    buggy_result_path,
                                    test_result_path,
                                    rewrite
                                )
                            
