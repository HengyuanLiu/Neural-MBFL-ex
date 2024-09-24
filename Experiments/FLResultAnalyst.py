import pandas as pd
from itertools import product
from pathlib import Path

from Utils.STEnvConfig import get_pathConfig
from Utils.DatasetConfig import get_D4Jprojects, get_D4Jversions
from Utils.PandasHelper import move_column_to_pos, move_rows_with_value_to_end

class FLResultAnalyst:
    
    pathConfig = get_pathConfig()
    if pathConfig:
        
        MBFL_Metric = Path(pathConfig["MBFL_Metric"])
        
    MutationType = ["NeuralMutation", "TraditionalMutation", "MergeMutation", "MergeSus"]
    Tool = {
        "NeuralMutation": ["mBERT"],
        "TraditionalMutation": ["major"],
        "MergeMutation": ["major_SmBERT", "mBERT_Smajor", "U_mBERT_major"],
        "MergeSus": ["SusDRankAvg"]
    }
    Dataset = ["Defects4J"]
    DatasetVersion = {
        "Defects4J": "v2.0"
    }
    Granularity = ["Statement"]  
    KillType = ["kill_type3"]
    KillTypeName = {
        "kill_type3": "Weak Kill"
    }
    Approach = ["Metallaxis", "MUSE", "FACombination"]
    ApproachFormula = {
        "Metallaxis": ["Dstar", "Ochiai", "Jaccard", "Op2", "Tarantula", "Gp13"],
        "MUSE": ["Muse"],
        "FACombination": ["Dstar", "Ochiai", "Jaccard", "Op2", "Tarantula", "Gp13", "Muse"]
    }
    ApproachAggregation = {
        "Metallaxis": ["max"],
        "MUSE": ["avg"],
        "FACombination": ["max"]
    }
    Aggregation = ["max"]
    TieBreak = ["Avg"]
    Metric = ["TopN", "EXAM", "MEAN"]
    Formula = ["Dstar", "Ochiai", "Jaccard", "Op2", "Tarantula", "Gp13", "Muse"]

    def __init__(
        self,
        granularity="Statement", 
        dataset="Defects4J", 
        mutant_type="NeuralMutation",
        tool="mBERT", 
        approach="FACombination", 
        kill_type="kill_type3", 
        aggregation="max",
        formula="Dstar",
        tie_break="Avg"
    ):
        
        self.granularity = granularity
        self.dataset = dataset
        self.mutant_type = mutant_type
        self.tool = tool
        self.approach = approach
        self.kill_type = kill_type
        self.aggregation = aggregation
        self.formula = formula
        self.tie_break = tie_break
        
        self.path_mappings = {
            "Granularity": [self.granularity],
            "Dataset": [self.dataset],
            "Mutation Type": [self.mutant_type],
            "Mutation Method": [self.tool],
            "Approach": [self.approach],
            "Kill Type": [self.kill_type],  
            "Aggregation": [self.aggregation],
            "Formula": [self.formula],
            "Tie Break": [self.tie_break]
        }
    
    @staticmethod
    def merge_topn_mean_summary(MethodSettingPath, formula):
        projects = get_D4Jprojects(DatasetVersion=FLResultAnalyst.DatasetVersion[FLResultAnalyst.Dataset[0]])
        summary_data = []

        for project in projects:
            topn_path = MethodSettingPath / "MEAN" / f"{project}" / "Summary" / f"{formula}.csv"
            mean_path = MethodSettingPath / "TopN" / f"{project}" / "Summary" / f"{formula}.csv"

            if not topn_path.exists() or not mean_path.exists():
                print(f"跳过项目 {project}，因为TopN或MEAN数据文件不存在。")
                continue

            try:
                topn_df = pd.read_csv(topn_path)
                mean_df = pd.read_csv(mean_path)
            except Exception as e:
                print(f"读取项目 {project} 的TopN或MEAN数据时发生错误: {e}")
                continue

            merged_row = {**{'Project': project}, **topn_df.iloc[0].to_dict(), **mean_df.iloc[0].to_dict()}
            summary_data.append(merged_row)

        summary_df = pd.DataFrame(summary_data)
        summary_row = {
            'Project': 'Summary',
            **{col: summary_df[col].mean() for col in ['MFR', 'MAR', 'MAP'] if col in summary_df},
            **{col: summary_df[col].sum() for col in ['top1', 'top3', 'top5', 'top10'] if col in summary_df}
        }
        summary_df = pd.concat([summary_df, pd.DataFrame([summary_row])], ignore_index=True)

        return summary_df
    
    @staticmethod
    def merge_exam_summary(MethodSettingPath, formula):
        projects = get_D4Jprojects(DatasetVersion=FLResultAnalyst.DatasetVersion[FLResultAnalyst.Dataset[0]])
        summary_data = []

        for project in projects:
            exam_path = MethodSettingPath / "EXAM" / f"{project}" / "Summary" / f"{formula}.csv"

            if not exam_path.exists():
                print(f"跳过项目 {project}，因为EXAM数据文件不存在。")
                continue

            try:
                exam_df = pd.read_csv(exam_path)
            except Exception as e:
                print(f"读取项目 {project} 的EXAM数据时发生错误: {e}")
                continue

            summary_data.append(exam_df)

        summary_df = pd.concat(summary_data, ignore_index=True)

        return summary_df
    
    def is_valid_param(self, param, max_independent_variable_num=2):
        filtered = {key: value for key, value in param.items() if isinstance(value, list) and len(value) >= 2 and key != "Mutation Type"}
        if len(filtered) > max_independent_variable_num:
            return False
        else:
            return True

    def valid_combinations_generator(self, param):
        path_mappings = self.path_mappings.copy()
        
        for key, values in param.items():
            if key in path_mappings:
                path_mappings[key] = values
                
        keys, values_lists = zip(*path_mappings.items())
        for values in product(*values_lists):
            combo = dict(zip(keys, values))
            if combo["Mutation Method"] in self.Tool.get(combo["Mutation Type"], []) and combo["Formula"] in self.ApproachFormula.get(combo["Approach"], []):
                yield combo
        
    def compare_topn_mean_summary_by_combination(self, combinations):
        all_summary_dfs = pd.DataFrame()  
        
        for combo in combinations:
            
            method_setting_path = self.MBFL_Metric / combo["Granularity"] / combo["Dataset"] / combo["Mutation Type"] / combo["Mutation Method"] / combo["Approach"] / combo["Kill Type"] / combo["Aggregation"] / combo["Tie Break"]
            summary_df = self.merge_topn_mean_summary(method_setting_path, combo["Formula"])
            
            for key in combo.keys():
                if key == "Kill Type":
                    summary_df[key] = self.KillTypeName[combo[key]]
                else:
                    summary_df[key] = combo[key]
            
            all_summary_dfs = pd.concat([all_summary_dfs, summary_df], ignore_index=True)
        return all_summary_dfs
    
    def compare_topn_mean_summary_by_param(self, param):
        
        path_mappings = self.path_mappings.copy()
        
        combinations = list(self.valid_combinations_generator(param))
        
        all_summary_dfs = self.compare_topn_mean_summary_by_combination(combinations)
        
        all_summary_dfs = all_summary_dfs.sort_values(by=['Project'] + list(param.keys()), ignore_index=True)
        
        for pos, key in enumerate(param.keys(), 1):
            all_summary_dfs = move_column_to_pos(all_summary_dfs, key, pos)
            
        for key in reversed(path_mappings.keys()):
            if key not in param.keys():
                all_summary_dfs = move_column_to_pos(all_summary_dfs, key, 0)
        all_summary_dfs = move_rows_with_value_to_end(all_summary_dfs, 'Project', 'Summary')
        
        return all_summary_dfs
    
    def compare_exam_summary_by_combination(self, combinations, independent_variable, drop_rank=True):
        exam_dfs = []
        for combo in combinations:
            
            method_setting_path = self.MBFL_Metric / combo["Granularity"] / combo["Dataset"] / combo["Mutation Type"] / combo["Mutation Method"] / combo["Approach"] / combo["Kill Type"] / combo["Aggregation"] / combo["Tie Break"]
            exam_df = self.merge_exam_summary(method_setting_path, combo["Formula"])
            if drop_rank:
                exam_df.drop(columns='Rank', inplace=True)
                exclude_result_col_num = 1
            else:
                exclude_result_col_num = 2
            
            if independent_variable == "Kill Type":
                exam_df.rename(columns={'Rank': f'Rank_{self.KillTypeName[combo[independent_variable]]}'}, inplace=True)
                exam_df.rename(columns={'EXAM': f'EXAM_{self.KillTypeName[combo[independent_variable]]}'}, inplace=True)
            else:
                exam_df.rename(columns={'Rank': f'Rank_{combo[independent_variable]}'}, inplace=True)
                exam_df.rename(columns={'EXAM': f'EXAM_{combo[independent_variable]}'}, inplace=True)
                
            exam_dfs.append(exam_df)
        all_exam_dfs = exam_dfs[0]
        on_column_num = len(all_exam_dfs.columns[:-exclude_result_col_num])
        
        for exam_df in exam_dfs[1:]:  
            all_exam_dfs = pd.merge(all_exam_dfs, exam_df, on=all_exam_dfs.columns[:on_column_num].tolist(), how='outer')
            
        return all_exam_dfs
    
    def compare_exam_summary_by_param(self, param, independent_variable, drop_rank=True):
        
        if self.is_valid_param(param, max_independent_variable_num=1):
            combinations = list(self.valid_combinations_generator(param))

            exam_summary_dfs = self.compare_exam_summary_by_combination(combinations, independent_variable=independent_variable, drop_rank=drop_rank)

            return exam_summary_dfs
        else:
            return pd.DataFrame()