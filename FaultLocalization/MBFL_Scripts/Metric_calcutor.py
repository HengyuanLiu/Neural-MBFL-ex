import csv
from fileinput import filename
import os
import json
import Utils
from pathlib import Path
import pandas as pd
import logging
from SusFormulas import F_Sus
from Utils import get_projects, get_versions

software_testing_root_env = os.getenv("SOFTWARE_TESTING_ROOT")
if software_testing_root_env is None:
    raise EnvironmentError("The SOFTWARE_TESTING_ROOT environment variable is not set.")
SOFTWARE_TESTING_ROOT = Path(software_testing_root_env)  
RANK = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Rank"  
METRIC = SOFTWARE_TESTING_ROOT / "FaultLocalization/MBFL/Metric"
CheckOrNot = False  

log_file_path = METRIC / "error_log.txt"  
logging.basicConfig(level=logging.ERROR, filename=log_file_path, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def check_file_exists(file_path):
    
    if CheckOrNot:
        file = Path(file_path)
        return file.exists()
    else:
        return False

def read_rank_file(file_path):
    return pd.read_csv(file_path)

def write_to_csv(data_frame, file_path):
    print(file_path)
    directory = file_path.parent
    
    if not directory.exists():
        directory.mkdir(parents=True)
    
    data_frame.to_csv(file_path, index=False)

def calculate_topN(base_path, output_path, project, versions, formula):
    N = [1, 3, 5, 10]
    data_frame = pd.DataFrame(columns=[f'top{n}' for n in N])
    data_frame.loc[0] = [0 for n in N]
    data_frame = data_frame.astype(int)
    for i in versions:
        rank_file_path = base_path / f"{i}" / f"{formula}.csv"
        path = output_path / f"{i}" / f"{formula}.csv"
        if not check_file_exists(path):
            if rank_file_path.exists():
                rank_df = read_rank_file(rank_file_path)
                faulty_rows = rank_df[rank_df['faulty_status'] == True]
                frame = pd.DataFrame({f"top{n}": [faulty_rows['rank'].apply(lambda x: x <= n).sum()] for n in N})
                
                for col in data_frame.columns:
                    data_frame.loc[0, col] += frame.loc[0, col]
                
                write_to_csv(frame, path)
        else:
            print(f"跳过{path}··························")
    return data_frame
def calculate_exam(base_path, output_path, project, versions, formula):
    data_frame = pd.DataFrame(columns=['Project', 'Version', 'faulty_entity', 'Rank', 'EXAM'])
    for i in versions:
        rank_file_path = base_path / f"{i}" / f"{formula}.csv"
        path = output_path / f"{i}" / f"{formula}.csv"
        if not check_file_exists(path):        
            if rank_file_path.exists():     
                rank_df = read_rank_file(rank_file_path)
                faulty_rows = rank_df[rank_df['faulty_status'] == True]
                frame = pd.DataFrame(
                    {
                        'Project': project,
                        'Version': i,
                        'faulty_entity': faulty_rows['code_entity_linenum'],
                        'Rank': faulty_rows['rank'],
                        'EXAM': faulty_rows['rank'] / rank_df.shape[0]
                    }
                )
                data_frame = pd.concat([data_frame, frame], ignore_index=True)
                write_to_csv(frame, path)
        else:
            print(f"跳过{path}··························")
    return data_frame
def calculate_mean(base_path, output_path, project, versions, formula):
    frame_faulty = pd.DataFrame(columns=['MFR', 'MAR', 'MAP'])
    for i in versions:
        rank_file_path = base_path / f"{i}" / f"{formula}.csv"
        path = output_path / f"{i}" / f"{formula}.csv"
        if not check_file_exists(path):
            if rank_file_path.exists():
                rank_df = read_rank_file(rank_file_path)  
                faulty_rows = rank_df[rank_df['faulty_status'] == True]
                
                if not faulty_rows.empty:
                    MFR = faulty_rows['rank'].min()  
                    MAR = faulty_rows['rank'].mean()
                    MAP = (1 / faulty_rows['rank']).mean()
                    data_frame = pd.DataFrame(
                        {
                            'MFR': [MFR], 
                            'MAR': [MAR], 
                            'MAP': [MAP]
                        }
                    )
                    write_to_csv(data_frame, path)  
                    
                    frame_faulty = pd.concat([frame_faulty, data_frame], ignore_index=True)
        else:
            print(f"跳过{path}··························")
    
    if not frame_faulty.empty:
        average_row = frame_faulty.mean()
        average_df = pd.DataFrame([average_row], columns=frame_faulty.columns)
        return average_df
    else:
        return pd.DataFrame(columns=frame_faulty.columns)

def get_metric(*args):
    project, versions, granularity, dataset,  mutanttype, tool, approach, killtype, aggregation, tieBreak, formula, metric = args
    base_path = RANK / granularity / dataset / mutanttype / tool / approach / killtype / aggregation / tieBreak / project
    output_path = METRIC / granularity / dataset / mutanttype / tool / approach / killtype / aggregation / tieBreak / metric / project
    file_path = output_path / "Summary" / f"{formula}.csv"
    
    if metric == "TopN":
        data_frame = calculate_topN(base_path, output_path, project, versions, formula)
    elif metric == "EXAM":
        data_frame = calculate_exam(base_path, output_path, project, versions, formula)
    elif metric == "MEAN":
        data_frame = calculate_mean(base_path, output_path, project, versions, formula)
    else:
        raise ValueError("Unsupported metric")
    
    if not data_frame.empty:
        write_to_csv(data_frame, file_path)

def init(project, versions):
    
    MutationType = ["NeuralMutation", "TraditionalMutation", "MergeMutation", "MergeSus"]
    Tool = {
        "NeuralMutation": ["mBERT"],
        "TraditionalMutation": ["major"],
        "MergeMutation": ["major_SmBERT", "mBERT_Smajor", "U_mBERT_major"],
        "MergeSus": ["BordaCountAvg", "SusAvg"]
    }
    
    Dataset = ["Defects4J"]
    Granularity = ["Statement"]  
    KillType = ["kill_type3"]
    Approach = ["FACombination"]
    Aggregation = ["max"]
    TieBreak = ["Best", "Avg"]
    Metric = ["TopN", "EXAM", "MEAN"]
    Formula = list(F_Sus.keys())
    for granularity in Granularity:
        for dataset in Dataset:
            for mutationtype in MutationType:
                tools = Tool[mutationtype]
                for tool in tools:
                    for approach in Approach:
                        for killtype in KillType:
                            for aggregation in Aggregation:
                                for tiebreak in TieBreak:
                                    for formula in Formula:
                                        for metric in Metric:
                                            try:
                                                get_metric(project, versions, granularity, dataset, mutationtype, tool,
                                                               approach, killtype, aggregation, tiebreak, formula,
                                                               metric)
                                            except Exception as e:
                                                error_message = f"Error occurred: {project}-{dataset}-{mutationtype}-{tool}-{killtype}-{approach}-{aggregation}-{tiebreak}-{formula}-{metric}: {e}"
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