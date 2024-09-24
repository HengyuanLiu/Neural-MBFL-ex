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
import pandas as pd

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

    def merge_data_from_handlers(self, other_handlers, main_handler_name):
        
        if any(self.dfs[sheet].shape[0] > 0 for sheet in self.dfs):
            print("Current DataHandler instance is not empty. Exiting to avoid data loss.")
            return
        if main_handler_name is None or main_handler_name not in other_handlers:
            if main_handler_name is not None:
                print(f"Main handler '{main_handler_name}' not found. Using the current instance as the main handler.")
            else:
                print("No main handler specified. Using the current instance as the main handler.")
        else:
            
            print(f"Using '{main_handler_name}' as the main handler. Copying data to the current instance.")
            main_handler = other_handlers[main_handler_name]
            for sheet_name in main_handler.dfs:
                self.dfs[sheet_name] = main_handler.dfs[sheet_name].copy()
        original_keys = {
            sheet: set(self.dfs[sheet][['project', 'version', 'code_entity', 'linenum']].apply(tuple, axis=1))
            for sheet in self.dfs
        }
        for name, handler in other_handlers.items():
            if name == main_handler_name:
                continue  
            for sheet_name in self.dfs:
                if sheet_name in handler.dfs:
                    
                    for _, row in handler.dfs[sheet_name].iterrows():
                        row_key = (row['project'], row['version'], row['code_entity'], row['linenum'])
                        
                        if row_key not in original_keys[sheet_name]:
                            self.dfs[sheet_name] = self.dfs[sheet_name].append(row, ignore_index=True)

    def load_data_from_excel(self, filepath):
        
        xl = pd.ExcelFile(filepath)
        for sheet_name in xl.sheet_names:
            if sheet_name in self.dfs:
                self.dfs[sheet_name] = pd.read_excel(xl, sheet_name=sheet_name)
            else:
                print(f"Sheet name '{sheet_name}' not found in initialized DataFrames. Skipping.")
def get_MergeMutantSus_bySettings(
    dataset,
    project,
    version,
    mutation_type,
    mutant_tool,
    kill_type, 
    rewrite=True
):
    
    params = {
        'dataset': dataset,
        'project': project,
        'version': version,
        'mutation_type': mutation_type,
        'mutant_tool': mutant_tool,
        'kill_type': kill_type,
        'rewrite': rewrite,
    }
    for name, value in params.items():
        print(f"{name}: {value}")
        
    mutantSusResultComponents = {} 
    mutantSusResultPath = f"{MutantSusPath}/{granularity}/{dataset}/{mutation_type}/{mutant_tool}/{kill_type}/{project}/{project}_{version}.xlsx"
    mutantSusResultPath = Path(mutantSusResultPath)

    if rewrite or not mutantSusResultPath.exists():
        print("Checking for rewrite or file non-existence")
        if not mutantSusResultPath.parent.exists():
            mutantSusResultPath.parent.mkdir(parents=True, exist_ok=True)
            print(f"Directory {mutantSusResultPath.parent} does not exist, created now.")

        sheet_names = list(F_Sus.keys())
        mutantSusResultComponent_handlers = {}
        for mutation_type_component, mutant_tool_components in MutantTools[mutation_type][mutant_tool].items():
            for mutant_tool_component in mutant_tool_components:
                mutantSusResultComponentPath = f"{MutantSusPath}/{granularity}/{dataset}/{mutation_type_component}/{mutant_tool_component}/{kill_type}/{project}/{project}_{version}.xlsx"
                mutantSusResultComponentPath = Path(mutantSusResultComponentPath)

                if mutantSusResultComponentPath.exists():
                    mutantSusResultComponent_handler = DataHandler(sheet_names)
                    mutantSusResultComponent_handler.load_data_from_excel(mutantSusResultComponentPath)
                    mutantSusResultComponent_handlers[mutant_tool_component] = mutantSusResultComponent_handler
                else:
                    print(f"Component Mutants Sus Not Exist: {mutantSusResultComponentPath}")
                    
        if mutantSusResultComponent_handlers:
            print("Processing mutantSusResultComponent_handlers")
            mutantSusResult_handler = DataHandler(sheet_names)
            
            if mutant_tool == "U_mBERT_major":
                for mutant_tool_component, mutantSusResultComponent_handler in mutantSusResultComponent_handlers.items():
                    
                    mutantSusResult_handler.merge_data(mutantSusResultComponent_handler)
            elif mutant_tool == "mBERT_Smajor":
                mutantSusResult_handler.merge_data_from_handlers(mutantSusResultComponent_handlers, "mBERT")
            elif mutant_tool == "major_SmBERT":
                mutantSusResult_handler.merge_data_from_handlers(mutantSusResultComponent_handlers, "major")
            mutantSusResult_handler.save_data(
                mutantSusResultPath.as_posix()
            )
            print("Finished processing mutantSusResultComponent_handlers")  
        else:
            print("No mutant data in mutantSusResultComponent_handlers, skipping.")    
    else:
        print("File already exists and no rewrite needed, skipping.")

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
        
    mutation_types = ["NeuralMutation", "TraditionalMutation", "MergeMutation"] 
    MutantTools = {
        "MergeMutation": {
            
            "U_mBERT_major": {"NeuralMutation": ["mBERT"], "TraditionalMutation": ["major"]},
            
            "mBERT_Smajor": {"NeuralMutation": ["mBERT"], "TraditionalMutation": ["major"]},
            
            "major_SmBERT": {"TraditionalMutation": ["major"], "NeuralMutation": ["mBERT"]},
        }
    }

    KillTypes = ["kill_type3"]

    dataset = "Defects4J"

    granularity = "Mutant"
    if Debug:
        project = "Collections"
        version = 25

        mutation_type = "MergeMutation"
        
        mutant_tool = "U_mBERT_major" 

        kill_type = "kill_type3"

        MutantSusPath, MutantTestResultPath, D4JClean, clean_path, buggy_result_path, test_result_path = costomize_pathConfig4Project(
            project
        )

        get_MergeMutantSus_bySettings(
            dataset,
            project,
            version,
            mutation_type,
            mutant_tool,
            kill_type, 
            rewrite=rewrite
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

                                get_MergeMutantSus_bySettings(
                                    dataset,
                                    project,
                                    version,
                                    mutation_type,
                                    mutant_tool,
                                    kill_type, 
                                    rewrite=rewrite
                                )
                                