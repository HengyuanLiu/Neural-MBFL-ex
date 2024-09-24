import ast
import csv
import glob
import json
import os
import subprocess
import pandas as pd
import Utils
from tkinter import NO
from pathlib import Path
import logging
from SusFormulas import F_Sus
from Utils import get_projects, get_versions

software_testing_root_env = os.getenv("SOFTWARE_TESTING_ROOT")
if software_testing_root_env is None:
    raise EnvironmentError("The SOFTWARE_TESTING_ROOT environment variable is not set.")
SOFTWARE_TESTING_ROOT = Path(software_testing_root_env)  
SUS = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Sus"
Mutant_Test_Result = SOFTWARE_TESTING_ROOT / "MutationAnalysis/MutantTestResult"  
Sus_MBFL_FL = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Sus"  
CheckOrNot = False  

log_file_path = SUS / "Statement/Defects4J/error_log.txt"  
logging.basicConfig(level=logging.ERROR, filename=log_file_path, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def check_file_exists(file_path):
    
    if CheckOrNot:
        file = Path(file_path)
        return file.exists()
    else:
        return False
def write_dataframe_to_csv(file_path, dataframe):
    
    file_path = Path(file_path)
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(file_path, index=False)
    print(f"写入csv文件 {file_path}")
def processExcel_FACombination(excel_file_path, output_csv_path,
                               aggregation):  
    excel_file = pd.ExcelFile(excel_file_path)
    sheet_names = excel_file.sheet_names
    output_csv_path.mkdir(parents=True, exist_ok=True)  
    for sheet in sheet_names:
        df = pd.read_excel(excel_file_path, sheet_name=sheet)
        
        grouped = df.groupby(['version', 'code_entity', 'linenum']).agg({'Sus': lambda x: list(x)}).reset_index()
        
        grouped['sus_line'] = grouped['Sus'].apply(lambda x: Utils.process_sus_list(x, aggregation))
        
        grouped['code_entity_linenum'] = grouped['code_entity'] + "-" + grouped['linenum'].astype(str)
        
        selected_columns = grouped[['code_entity_linenum', 'sus_line']]
        
        selected_columns.sort_values(by='sus_line', ascending=False, inplace=True)
        output_csv_file = output_csv_path / f"{sheet}.csv"
        
        write_dataframe_to_csv(output_csv_file,selected_columns)
def getLineSus(project, version, dataset, mutanttype, tool, killtype, approach, aggregation):
    excel_file_path = SUS / "Mutant" / dataset / mutanttype / tool / killtype / project / f"{project}_{version}.xlsx"
    
    output_csv_path = SUS / "Statement" / dataset / mutanttype / tool / approach / killtype / aggregation / project / version
    if not check_file_exists(output_csv_path):  
        print(f"输入文件夹是{excel_file_path}，输出文件夹是{output_csv_path}")
        
        processExcel_FACombination(excel_file_path, output_csv_path, aggregation)
    else:
        print(f"we have already processed {excel_file_path}")
def init(project, version):
    MutationType = ["NeuralMutation", "TraditionalMutation", "MergeMutation"]
    
    Tool = {
        "NeuralMutation": ["mBERT"],
        "TraditionalMutation": ["major"],
        "MergeMutation": ["major_SmBERT", "mBERT_Smajor", "U_mBERT_major"]
    }
    
    Dataset = ["Defects4J"]
    Granularity = ["Mutant"]  
    KillType = ["kill_type3"]
    Approach = ["FACombination"]
    Aggregation = ["max"]
    Formula = list(F_Sus.keys())
    for mutationtype in MutationType:
        tools = Tool[mutationtype]
        for tool in tools:
            for dataset in Dataset:
                for killtype in KillType:
                    for approach in Approach:
                        for aggregation in Aggregation:
                            
                            try:
                                getLineSus(project, f"{version}", dataset, mutationtype, tool, killtype, approach, aggregation)
                            except Exception as e:
                                error_message = f"Error occurred: {project}-{version}-{dataset}-{mutationtype}-{tool}-{killtype}-{approach}-{aggregation}: {e}"
                                logging.error(error_message)
                                print(error_message)

if __name__ == '__main__':
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
            init(project, version)

    