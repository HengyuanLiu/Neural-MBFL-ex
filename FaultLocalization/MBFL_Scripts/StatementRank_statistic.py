import csv
from fileinput import filename
import os
import json
import Utils
from pathlib import Path
import numpy as np
import pandas as pd
import logging
from SusFormulas import F_Sus
from Utils import get_projects, get_versions

software_testing_root_env = os.getenv("SOFTWARE_TESTING_ROOT")
if software_testing_root_env is None:
    raise EnvironmentError("The SOFTWARE_TESTING_ROOT environment variable is not set.")
SOFTWARE_TESTING_ROOT = Path(software_testing_root_env)  
Mutant_Faulty_Path = SOFTWARE_TESTING_ROOT / "DataSet/Defects4J/D4JClean/faultyLinePlus"  
Mutant_Faulty_Path_D4J = SOFTWARE_TESTING_ROOT / "DataSet/Defects4J/D4J/Faultline_D4J.json"  
SUS = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Sus"  
RANK = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Rank"  
CheckOrNot = False  

log_file_path = RANK/"error_log.txt"  
logging.basicConfig(level=logging.ERROR, filename=log_file_path, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def check_file_exists(file_path):
    if CheckOrNot:
        file = Path(file_path)
        return file.exists()
    else:
        return False

def read_txt_file(file_path):
    lines = []
    with open(file_path, 'r') as f:
        for line in f:
            lines.append(line.strip())
    return lines

def changeTxtEqualCsv(mutant_dic):
    faultyList = []
    for key, value in mutant_dic.items():
        faultyLine = key[1:].split(".")[0].replace("/", "-")
        for lineNum in value:
            faultyList.append(faultyLine + "-" + str(lineNum))
    return faultyList
def get_rank_statement(csv_path):
    value_rank_dict = {}
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        
        sus = {}
        rank = 1
        num = 1
        for row in reader:
            sus[row[0]] = row[1]
            value = str(row[1])
            if value not in value_rank_dict:
                
                value_rank_dict[value] = rank
                rank += 1
            
    return sus, value_rank_dict

def load_csv(path, content, formula, rank, faultylist):
    try:
        ans = {}  
        for key, value in content.items():  
            ans[key] = {
                "rank": rank[value],
                "faulty": True if key in faultylist else False,
                "sus": value
            }
        with open(f"{path}/{formula}.json", 'w') as f:
            json.dump(ans, f)
        return True
    except:
        return False

def write_dataframe_to_csv(file_path, dataframe):
    file_path = Path(file_path)

    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(file_path, index=False)
    print(f"写入csv文件 {file_path}")

def convert_str_to_dict(s):
    start_index = 0
    result = {}
    while True:
        key_start_index = s.find("'", start_index) + 1
        if key_start_index == 0:
            break
        key_end_index = s.find("'", key_start_index)
        key = s[key_start_index:key_end_index]
        value_start_index = s.find("[", key_end_index) + 1
        value_end_index = s.find("]", value_start_index)
        value_str = s[value_start_index:value_end_index]
        if value_str:
            value = list(map(int, value_str.split(",")))
            result[key] = value
        start_index = value_end_index
    return result

def getFaultyLineJson(pid):
    mutant_path = Mutant_Faulty_Path / f"{pid}FaultLine.txt"
    faultyInfo = read_txt_file(mutant_path)  
    faultyList = {}
    for _item in faultyInfo:  
        versions = _item.split(" ")[1]
        mutant = _item[(_item.index('{')):]
        mutant_dic = convert_str_to_dict(mutant)
        faultyList[versions] = changeTxtEqualCsv(mutant_dic)
    return faultyList

def getCodeEntityLineNum(pid, version, granularity, dataset, mutanttype, tool, approach, killtype, aggregation, tieBreak, formula):
    if mutanttype == "MergeSus":
        statement_sus_path = SUS / "Statement" / dataset / mutanttype / tool / approach / killtype / aggregation / tieBreak / pid / version / f"{formula}.csv"
    else:
        statement_sus_path = SUS / "Statement" / dataset / mutanttype / tool / approach / killtype / aggregation / pid / version / f"{formula}.csv"
    
    df = pd.read_csv(statement_sus_path)
    return df['code_entity_linenum'].to_frame()
def getRank(pid, version, granularity, dataset, mutanttype, tool, approach, killtype, aggregation, tieBreak, formula, code_entity_linenum_df=None, fillna_strategy='fill_lower_than_min'):    
    faultyFileJson = getFaultyLineJson(pid)
    if pid in ["Collections","JacksonDatabind", "JxPath"]:
        with open(Mutant_Faulty_Path_D4J, 'r') as f:
            Json_file = json.load(f)
        faultyFileJson = Json_file[pid] 
    
    if mutanttype == "MergeSus":
        statement_sus_path = SUS / "Statement" / dataset / mutanttype / tool / approach / killtype / aggregation / tieBreak / pid / version / f"{formula}.csv"
    else:
        statement_sus_path = SUS / "Statement" / dataset / mutanttype / tool / approach / killtype / aggregation / pid / version / f"{formula}.csv"
    
    output_path = RANK / granularity / dataset / mutanttype / tool / approach / killtype / aggregation / tieBreak / pid / version / f"{formula}.csv"
    if not check_file_exists(output_path):  
        
        df = pd.read_csv(statement_sus_path)
        if code_entity_linenum_df is not None:
            df = code_entity_linenum_df.merge(df, on='code_entity_linenum', how='left')
        
        df['is_missing'] = df['sus_line'].isna()
        default_fill_value = 0
        
        if df['sus_line'].isna().all():
            df['sus_line_processed'] = df['sus_line'].fillna(default_fill_value)
        else:
            
            if fillna_strategy == 'neglect':
                
                df['sus_line_processed'] = df['sus_line']
            elif fillna_strategy == 'fill_min':
                
                min_value = df['sus_line'].min()
                df['sus_line_processed'] = df['sus_line'].fillna(min_value)
            elif fillna_strategy == 'fill_lower_than_min':
                
                min_value = df['sus_line'].min()
                smallest_value = min_value - 1 if pd.notna(min_value) else default_fill_value - 1
                df['sus_line_processed'] = df['sus_line'].fillna(smallest_value)
            else:
                raise ValueError(f"Unknown fillna strategy {fillna_strategy}")
        
        df['rank'] = df['sus_line_processed'].rank(method='average', ascending=False)
        df.drop(columns=['is_missing', 'sus_line_processed'], inplace=True)
        list_faultyline = faultyFileJson[version]
        
        df['faulty_status'] = df['code_entity_linenum'].apply(lambda x: True if x in list_faultyline else False)
        print(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
    else:
        print(f"文件已存在: {output_path}")
def init(pid, versions):
    MutationType = ["NeuralMutation", "TraditionalMutation", "MergeMutation", "MergeSus"]
    Tool = {
        "NeuralMutation": ["mBERT"],
        "TraditionalMutation": ["major"],
        "MergeMutation": ["major_SmBERT", "mBERT_Smajor", "U_mBERT_major"],
        "MergeSus": ["SusDRank"]
    }
    
    Dataset = ["Defects4J"]
    Granularity = ["Statement"]  
    KillType = ["kill_type3"]
    Approach = ["FACombination"]
    Aggregation = ["max"]
    TieBreak = ["Avg"]
    Formula = list(F_Sus.keys())
    for granularity in Granularity:
        for dataset in Dataset:
            for approach in Approach:
                for killtype in KillType:
                    for aggregation in Aggregation:
                        for tiebreak in TieBreak:
                            for formula in Formula:
                                for version in versions:
                                    
                                    code_entity_linenum_dfs = []
                                    for mutationtype in MutationType:
                                        tools = Tool[mutationtype]
                                        for tool in tools:
                                            try:
                                                code_entity_linenum_df = getCodeEntityLineNum(pid, f"{version}", granularity, dataset, mutationtype, tool,
                                                        approach, killtype, aggregation, tiebreak, formula)
                                                code_entity_linenum_dfs.append(code_entity_linenum_df)
                                            except Exception as e:
                                                error_message = f"Error occurred: {pid}-{version}-{dataset}-{mutationtype}-{tool}-{killtype}-{approach}-{aggregation}-{tiebreak}-{formula}: {e}"
                                                logging.error(error_message)
                                                print(error_message)
                                    if len(code_entity_linenum_dfs) > 0:
                                        code_entity_linenum_df = pd.concat(code_entity_linenum_dfs)
                                        code_entity_linenum_df = code_entity_linenum_df.drop_duplicates().reset_index(drop=True)

                                        for mutationtype in MutationType:
                                            tools = Tool[mutationtype]
                                            for tool in tools:
                                                try:
                                                    getRank(pid, f"{version}", granularity, dataset, mutationtype, tool,
                                                            approach, killtype, aggregation, tiebreak, formula, 
                                                            code_entity_linenum_df=code_entity_linenum_df, fillna_strategy='fill_lower_than_min')
                                                except Exception as e:
                                                    error_message = f"Error occurred: {pid}-{version}-{dataset}-{mutationtype}-{tool}-{killtype}-{approach}-{aggregation}-{tiebreak}-{formula}: {e}"
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
        init(project, versions)

    