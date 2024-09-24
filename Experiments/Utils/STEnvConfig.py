import os
import json

def get_pathConfig(env_var_name="SoftwareTestingPathConfig", Debug=False):
    if env_var_name in os.environ:
        pathConfg_path = os.environ[env_var_name]
        if Debug:
            print(f"获取到环境变量 {env_var_name} 的值为: {pathConfg_path}")
    else:
        if Debug:
            print(f"未找到环境变量 {env_var_name}")
        return None
    if os.path.isfile(pathConfg_path) and os.access(pathConfg_path, os.R_OK):
        if Debug:
            print(f"JSON 文件 {pathConfg_path} 存在并可读")
        try:
            
            with open(pathConfg_path, 'r') as pathConfg_fp:
                pathConfg = json.load(pathConfg_fp)
            if Debug:
                print("成功加载 JSON 数据")
            return pathConfg
        except (json.JSONDecodeError, IOError) as e:
            
            if Debug:
                print(f"加载 JSON 数据失败: {e}") 
            pass
    else:
        if Debug:
            print(f"JSON 文件 {pathConfg_path} 不存在或无读权限") 
    return None

if __name__ == "__main__":
    pathConfg = get_pathConfig()
    print(f"获取到的 pathConfg: {pathConfg}")
