import ast
import csv
import glob
import json
import os
import subprocess
import numpy as np
import pandas as pd
import Utils
from tkinter import NO
from pathlib import Path
from SusFormulas import F_Sus

software_testing_root_env = os.getenv("SOFTWARE_TESTING_ROOT")
if software_testing_root_env is None:
    raise EnvironmentError("The SOFTWARE_TESTING_ROOT environment variable is not set.")
SOFTWARE_TESTING_ROOT = Path(software_testing_root_env) 
Mutant_Faulty_Path = SOFTWARE_TESTING_ROOT/"DataSet/Defects4J/D4JClean/faultyLine" 
SUS = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Sus" 
RANK = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Rank" 

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
def get_SusbySusDRankAvg(RankComponents):
    code_entity_linenum_set = set()
    for RankComponent in RankComponents.values():
        code_entity_linenum_set = code_entity_linenum_set.union(set(RankComponent['code_entity_linenum']))
    for component, RankComponent in RankComponents.items():
        RankComponent[f'susDrank_line_{component}'] = RankComponent['sus_line'] / RankComponent['rank']
    MergeSusResult = pd.DataFrame({'code_entity_linenum': list(code_entity_linenum_set)})
    MergeSusResult['code_entity_linenum'] = MergeSusResult['code_entity_linenum'].astype(object)

    for component in RankComponents:
        MergeSusResult = MergeSusResult.merge(RankComponents[component][['code_entity_linenum', f'susDrank_line_{component}']],
                                on='code_entity_linenum', how='left'
                            )
    susDrank_columns = [col for col in MergeSusResult.columns if col.startswith('susDrank_line_')]
    MergeSusResult['sus_line'] = MergeSusResult[susDrank_columns].mean(axis=1)
    MergeSusResult.sort_values(by='sus_line', ascending=False, inplace=True)
    
    return MergeSusResult

def get_SusbyMerge(MergeMethod, merge_method, merge_setting, granularity, dataset, approach, kill_type, aggregation, tie_break, pid, vid, formula, rewrite=False):
    MergeSusResultPath = SUS / granularity / dataset / merge_method / merge_setting / approach / kill_type / aggregation / tie_break / pid / vid / f"{formula}.csv"
    
    if rewrite or not MergeSusResultPath.exists():

        RankComponents = {}
        for merge_mutantion_component, merge_tool_components in MergeMethod[merge_method][merge_setting].items():
            for merge_tool_component in merge_tool_components:
                RankComponentPath = RANK / granularity / dataset / merge_mutantion_component / merge_tool_component / approach / kill_type / aggregation / tie_break / pid / vid / f"{formula}.csv"
                if RankComponentPath.exists():
                    RankComponents[merge_tool_component] = pd.read_csv(RankComponentPath)
                else:
                    print(f"Component Mutants Sus Not Exist: {RankComponentPath}")

        if merge_setting == "SusDRankAvg":
            print("Calculate Sus by SusDRankAvg")
            MergeSusResult = get_SusbySusDRankAvg(RankComponents)
        else:
            print("Invalid merge setting specified.")
            return None
        print(MergeSusResult.head())
        if not MergeSusResultPath.parent.exists():
            MergeSusResultPath.parent.mkdir(parents=True, exist_ok=True)
            print(f"Directory {MergeSusResultPath.parent} does not exist, created now.")
        MergeSusResult.to_csv(MergeSusResultPath, index=False)

    else:
        print(f"{MergeSusResultPath} 已经生成完毕，跳过。")
def init(rewrite=False): 
    MutationType = ["NeuralMutation", "TraditionalMutation"] 
    Tool = {
            "NeuralMutation": ["mBERT"],
            "TraditionalMutation": ["major"],
        }
    MergeMethod = {
        "MergeSus":{
            "SusDRankAvg": {"NeuralMutation": ["mBERT"], "TraditionalMutation": ["major"]},
        }
    } 
    
    Dataset = ["Defects4J"]
    Granularity = ["Statement"] 
    KillType = ["kill_type3"]
    Approach = ["FACombination"]
    Aggregation = ["max"]
    TieBreak = ["Avg"] 
    Formula = list(F_Sus.keys())
    
    granularity = "Statement"
    dataset = "Defects4J"
    for merge_method, merge_settings in MergeMethod.items():
        for merge_setting in merge_settings.keys():
            for kill_type in KillType:
                for approach in Approach:
                    for aggregation in Aggregation:
                        for tie_break in TieBreak:
                            for formula in Formula:
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
                                            
                                            get_SusbyMerge(
                                                MergeMethod, 
                                                merge_method, 
                                                merge_setting, 
                                                granularity, dataset, 
                                                approach, kill_type, 
                                                aggregation, 
                                                tie_break, 
                                                project, 
                                                version, 
                                                formula,
                                                rewrite=rewrite
                                            )
if __name__ == '__main__':
    Debug=False
    rewrite=True

    if Debug:  
        MutationType = ["NeuralMutation", "TraditionalMutation"] 
        Tool = {
            "NeuralMutation": ["mBERT"],
            "TraditionalMutation": ["major"],
        }
        MergeMethod = {
            "MergeSus":{
                "SusDRankAvg": {"NeuralMutation": ["mBERT"], "TraditionalMutation": ["major"]},
            }
        }
        
        granularity = "Statement"
        dataset = "Defects4J"
        
        approach = "FACombination" 
        kill_type = "kill_type3"
        aggregation = "max"
        tie_break = "Avg"
        
        pid = "Closure"
        vid = "2"
        formula = "Jaccard"
        
        merge_method = "MergeSus"
        merge_setting = "SusDRankAvg"
        get_SusbyMerge(
        MergeMethod, 
        merge_method, 
        merge_setting, 
        granularity, dataset, 
        approach, kill_type, 
        aggregation, 
        tie_break, 
        pid, 
        vid, 
        formula,
        rewrite=rewrite
        )
    else:
        init(rewrite=rewrite)
    