import os
import json
import subprocess

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

def process_sus_list(sus_list, converge):
    return max(sus_list)