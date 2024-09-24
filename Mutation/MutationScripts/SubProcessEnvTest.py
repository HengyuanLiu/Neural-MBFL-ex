import os
import subprocess

def set_java_version(java_home_path):
    new_env = os.environ.copy()
    new_env["JAVA_HOME"] = java_home_path
    new_env["PATH"] = java_home_path + "/bin:" + new_env["PATH"]
    return new_env

def check_java_version(env):
    subprocess.run(["java -version"], env=env, shell=True)

desired_java_home = "/usr/lib/jvm/java-11-openjdk-amd64"

modified_env = set_java_version(desired_java_home)

print("Checking Java version before modification:")
subprocess.run(["java -version"], shell=True)

print("\nChecking Java version after modification:")
check_java_version(modified_env)

