import os
import subprocess
def find_files_with_find(directory, suffix=".java", recursive=True):
    command = ['find', directory, '-type', 'f', '-name', f'*{suffix}']
    if not recursive:
        command.insert(2, '-maxdepth')
        command.insert(3, '1')
        
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip().split('\n')

def find_files_with_os_walk(directory, suffix=".java", recursive=True):
    java_files = []
    for root, dirs, files in os.walk(directory):
        if not recursive:
            dirs[:] = []  
        for file in files:
            if file.endswith(suffix):
                full_path = os.path.join(root, file)
                java_files.append(full_path)
    return java_files

def get_files_with_suffix(directory, method='auto', suffix=".java", recursive=True):
    if method == 'find':
        return find_files_with_find(directory, suffix, recursive)
    elif method == 'os_walk':
        return find_files_with_os_walk(directory, suffix, recursive)
    else:
        
        try:
            return find_files_with_find(directory, suffix, recursive)
        except (subprocess.CalledProcessError, FileNotFoundError):
            
            return find_files_with_os_walk(directory, suffix, recursive)
def count_lines_wc(file_path, include_empty_lines=True):
    if include_empty_lines:
        command = ['wc', '-l', file_path]
    else:
        
        command = ['grep', '-cve', '^\s*$', file_path]

    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode == 0:
        return int(result.stdout.strip().split()[0])
    else:
        raise Exception(f"Error executing command: {result.stderr}")

def count_lines_python(file_path, include_empty_lines=True):
    with open(file_path, 'r', encoding='utf-8') as file:
        if include_empty_lines:
            return sum(1 for line in file)
        else:
            return sum(1 for line in file if line.strip())

def count_lines(file_path, method='auto', include_empty_lines=True):
    if method == 'wc-l':
        return count_lines_wc(file_path, include_empty_lines)
    elif method == 'python':
        return count_lines_python(file_path, include_empty_lines)
    elif method == 'auto':
        if os.name == 'posix':  
            try:
                return count_lines_wc(file_path, include_empty_lines)
            except Exception as e:
                print(f"Falling back to Python method due to: {e}")
                return count_lines_python(file_path, include_empty_lines)
        else:
            return count_lines_python(file_path, include_empty_lines)
    else:
        raise ValueError("Invalid method specified. Use 'auto', 'wc-l', or 'python'.")
