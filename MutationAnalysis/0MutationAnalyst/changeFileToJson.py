import json
import os
import glob
import subprocess

class MutationAnalysisConverter:
    def __init__(self, config_path):
        print("Initializing MutationAnalysisConverter...")
        self.path_info = self.load_path_config(config_path)
        print("Configuration loaded successfully.")

    @staticmethod
    def load_path_config(config_path):
        print(f"Loading configuration from {config_path}...")
        with open(config_path, 'r', encoding='utf-8') as path_file:
            return json.load(path_file)

    @staticmethod
    def get_non_txt_files(folder_path):
        print(f"Scanning for non-txt files in {folder_path}...")
        files = glob.glob(os.path.join(folder_path, "*"))
        non_txt_files = [os.path.basename(f) for f in files if not f.endswith((".txt", ".json")) and os.path.isfile(f)]
        print(f"Found {len(non_txt_files)} non-txt files.")
        return non_txt_files

    @staticmethod
    def parse_file(filename):
        print(f"Parsing file: {filename}")
        with open(filename) as f:
            lines = f.readlines()

        result, key, value = {}, None, ""

        for line in lines:
            if line.startswith('---'):
                if key:
                    result[key] = {"type3": value.split('\n')[0].replace(' ', '')}
                key = line.replace(' ', '').replace('\n', '').replace('---', '').replace('::', '#')
                value = ""
            else:
                value += line

        if key:
            result[key] = {"type3": value.split('\n')[0].replace(' ', '')}
        print(f"File parsed successfully. Extracted {len(result)} entries.")
        return result

    @staticmethod
    def get_json_file(json_path, data, file_name):
        target_file_path = os.path.join(json_path, f'{file_name}.json')
        print(f"Preparing to write data to {target_file_path}")
        os.makedirs(json_path, exist_ok=True)
        with open(target_file_path, 'w') as f:
            json.dump(data, f)
        print("Data written successfully.")
    
    @staticmethod
    def read_json_file(file_path):
        """
        Reads a JSON file and returns the parsed data.
        Parameters:
        - file_path (str): The path to the JSON file.

        Returns:
        - data (dict): The parsed JSON data.
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def process_folder_mBERT(self, pid, version, project_subfolder):
        result_path = f"{self.path_info['NeuralMutationResult']}/mBERT/Defects4J/{project_subfolder}/{pid}/{version}b"
        if os.path.exists(result_path):
            print(f"Path exists: {result_path}. Processing...")
        else:
            print(f'Path not exists: {result_path}. Skipped!')
            return 1
            
        print(f"Processing folder: {result_path}")
        results = self.get_non_txt_files(result_path)
        json_path = result_path.replace(project_subfolder, f'{project_subfolder}_json')

        for item in results:
            target_json_file_path = os.path.join(json_path, f'{item}.json')
            if os.path.exists(target_json_file_path):
                print(f"Skipping {target_json_file_path} as it has already been converted.")
                continue

            test_result = self.parse_file(os.path.join(result_path, item))
            self.get_json_file(json_path, test_result, item)
        print(f"Folder {result_path} processed successfully.")
        return 0
        
    def process_folder_major(self, pid, version, project_subfolder):
        result_path = f"{self.path_info['TraditionalMutationResult']}/major/Defects4J/{project_subfolder}/{pid}/{version}b"
        if os.path.exists(result_path):
            print(f"Path exists: {result_path}. Processing...")
        else:
            print(f'Path not exists: {result_path}. Skipped!')
            return 1
            
        print(f"Processing folder: {result_path}")
        results = self.get_non_txt_files(result_path)
        json_path = result_path.replace(project_subfolder, f'{project_subfolder}_json')

        for item in results:
            target_json_file_path = os.path.join(json_path, f'{item}.json')
            if os.path.exists(target_json_file_path):
                print(f"Skipping {target_json_file_path} as it has already been converted.")
                continue

            test_result = self.parse_file(os.path.join(result_path, item))
            self.get_json_file(json_path, test_result, item)
        print(f"Folder {result_path} processed successfully.")
        return 0

    def process_folder_major_old(self, pid, version, project_subfolder):
        result_path = f"{self.path_info['TraditionalMutationResult']}/major/Defects4J/{project_subfolder}/{pid}/{version}b"
        if os.path.exists(result_path):
            print(f"Path exists: {result_path}. Processing...")
        else:
            print(f'Path not exists: {result_path}. Skipped!')
            return 1
        
        print(f"Processing folder: {result_path}")
        
        results = self.get_non_txt_files(f"{result_path}/failing_tests")
        mutantInfo = self.read_json_file(f"{result_path}/mutantInfo.json")
        
        mutantInfodata = {}
        for item in mutantInfo:
            mutantInfodata[str(item['index'])] = item 
        
        linemap = {}
        for item in mutantInfo:
            num = item['linenum']
            if num in linemap:
                linemap[num] += 1
            else:
                linemap[num] = 1

            json_path = result_path.replace(project_subfolder, f'{project_subfolder}_json')
            targetName = item['relativePath'].split('.')[0].replace('/', '-') + f'-{num}-{linemap[num]}'
            target_json_file_path = os.path.join(json_path, f'{targetName}.json')
            if os.path.exists(target_json_file_path):
                print(f"Skipping {target_json_file_path} as it has already been converted.")
                continue

            filepath = f"{result_path}/failing_tests/{item['index']}"
            if not os.path.exists(filepath):
                continue
            test_result = self.parse_file(filepath)
            self.get_json_file(json_path, test_result, targetName)
            
            print(f"Folder {result_path} processed successfully.")
        return 0

    @staticmethod
    def run_command(command):
        """Run a command in the shell and return its output."""
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"Error running command: {command}\nError: {stderr}")
            return None
        return stdout.splitlines()

    def start(self, pid, project_subfolder):
        print(f"Starting processing for PID: {pid} with project_subfolder: {project_subfolder}")
        versions = self.run_command(f"defects4j bids -p {pid}")
        if versions is None:
            print(f"Could not obtain versions for PID: {pid}")
            return
        for version in versions:
            self.process_folder_mBERT(pid, version, project_subfolder)
            self.process_folder_major(pid, version, project_subfolder)

    def initialize_projects(self, pid):
        self.start(pid, 'result4FaultFile')

    def initialize(self):
        pids = self.run_command("defects4j pids")
        if pids is None:
            print("Could not obtain PID list from defects4j.")
            return
        for pid in pids:
            self.start(pid, 'result4FaultFile')

if __name__ == '__main__':
    pathConfig = "project_root_path/pathConfig.json"
    converter = MutationAnalysisConverter("/home/rs/WorkEx/Projects/SoftwareTesting/pathConfig.json")

