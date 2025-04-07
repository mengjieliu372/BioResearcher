import os
import json
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Optional, List
from code_fix_framework import CodeFixFramework

class LocalRExecutor:
    """本地R代码执行器"""
    
    def __init__(self, timeout: int = 60):
        """
        初始化本地执行器
        
        参数:
            timeout: 执行超时时间(秒)
        """
        self.timeout = timeout
        self.fix_framework = CodeFixFramework()
        self.skip_errors = [
            "there is no package called",
            "installation of package",
            "failed to download",
            "cannot open URL",
            "cannot change working directory",
            "No such file or directory",
            "网络连接问题",
            "internet routines cannot be loaded"
        ]
    
    def should_skip_error(self, error_msg: str) -> bool:
        """检查错误是否属于应跳过的类型"""
        return any(skip_str.lower() in error_msg.lower() for skip_str in self.skip_errors)
    
    def execute_r_script(self, script_path: str) -> Tuple[bool, str, Optional[str], bool]:
        """
        执行R脚本并返回结果
        
        参数:
            script_path: R脚本路径
            
        返回:
            (执行是否成功, 执行输出或错误信息, 修复后的代码路径, 是否应跳过)
        """
        try:
            # 直接使用本地Rscript执行命令
            rscript_path = r"C:\Program Files\R\R-4.4.3\bin\x64\Rscript.exe"
            cmd = f'"{rscript_path}" "{script_path}"'
            
            # 执行命令
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                timeout=self.timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return True, result.stdout, None, False
            
        except subprocess.CalledProcessError as e:
            # 执行失败，提取错误信息
            error_msg = e.stderr if e.stderr else str(e)
            
            # 检查是否应跳过
            if self.should_skip_error(error_msg):
                return False, error_msg, None, True
                
            return False, error_msg, None, False
            
        except subprocess.TimeoutExpired:
            return False, f"执行超时(超过{self.timeout}秒)", None, False
    
    def diagnose_and_fix(self, script_path: str, error_msg: str, max_attempts: int = 3) -> Tuple[bool, Optional[str], Dict, bool]:
        """
        诊断并修复R脚本错误
        
        参数:
            script_path: 脚本路径
            error_msg: 错误信息
            max_attempts: 最大修复尝试次数
            
        返回:
            (是否修复成功, 修复后的代码路径, 诊断信息, 是否应跳过)
        """
        # 检查是否应跳过
        if self.should_skip_error(error_msg):
            return False, None, {"error_type": "skip_error"}, True
            
        with open(script_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # 准备修复后的文件路径
        original_dir = os.path.dirname(script_path)
        original_name = os.path.basename(script_path)
        fixed_path = os.path.join(original_dir, f"fixed_{original_name}")
        
        for attempt in range(max_attempts):
            print(f"\n尝试修复 {original_name} (第 {attempt + 1} 次)...")
            
            # 使用修复框架诊断和修复
            fixed_code, diagnosis, _, _ = self.fix_framework.auto_fix(
                original_code, 
                error_msg,
                language="R"
            )
            
            if not fixed_code:
                print("修复失败: 无法生成修复代码")
                return False, None, diagnosis, False
            
            # 保存修复后的代码
            with open(fixed_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            
            # 测试修复后的代码
            success, output, _, should_skip = self.execute_r_script(fixed_path)
            
            if should_skip:
                return False, None, diagnosis, True
                
            if success:
                print(f"修复成功! 修复后的文件保存为: {fixed_path}")
                return True, fixed_path, diagnosis, False
            else:
                print(f"修复尝试 {attempt + 1} 失败")
                print("新错误信息:", output)
                error_msg = output  # 使用新错误信息进行下一次尝试
        
        return False, None, diagnosis, False
    
    def execute_with_auto_fix(self, script_path: str, max_attempts: int = 3) -> Tuple[bool, Optional[str], bool]:
        """
        执行R脚本并自动修复错误
        
        参数:
            script_path: 脚本路径
            max_attempts: 最大修复尝试次数
            
        返回:
            (最终是否成功, 最终可执行文件路径, 是否因特定错误被跳过)
        """
        # 初始执行
        success, output, _, should_skip = self.execute_r_script(script_path)
        
        if should_skip:
            print(f"跳过执行 {script_path}，原因: {output}")
            return False, None, True
            
        if success:
            print("脚本执行成功!")
            return True, script_path, False
        
        print("初始执行失败，开始自动修复流程...")
        print("错误信息:", output)
        
        # 尝试修复
        fixed, fixed_path, diagnosis, should_skip = self.diagnose_and_fix(
            script_path,
            output,
            max_attempts
        )
        
        if should_skip:
            print(f"跳过修复 {script_path}，原因: {diagnosis.get('error_type', '未知错误')}")
            return False, None, True
            
        if fixed:
            return True, fixed_path, False
        
        print(f"经过 {max_attempts} 次尝试后仍无法修复")
        return False, None, False

def batch_execute_r_scripts(directory: str):
    """
    批量执行目录下的所有R脚本
    
    参数:
        directory: 包含R脚本的目录路径
    """
    # 检查Rscript是否可用
    try:
        subprocess.run(["Rscript", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 系统中未找到Rscript，请确保R已安装并添加到PATH环境变量中")
        return
    
    executor = LocalRExecutor()
    
    # 确保是绝对路径
    directory = os.path.abspath(directory)
    print(f"\n开始处理目录: {directory}")
    
    # 查找所有R脚本文件
    r_files = [f for f in os.listdir(directory) if f.endswith('.r') or f.endswith('.R')]
    
    if not r_files:
        print("目录中没有找到R脚本文件")
        return
    
    results = []
    skipped_files = []
    
    for r_file in r_files:
        file_path = os.path.join(directory, r_file)
        print(f"\n处理文件: {r_file}")
        
        success, final_path, skipped = executor.execute_with_auto_fix(file_path)
        
        if skipped:
            skipped_files.append(r_file)
            continue
            
        results.append({
            "file": r_file,
            "success": success,
            "final_path": final_path,
            "fixed": final_path != file_path if final_path else False
        })
    
    # 保存执行结果摘要
    summary_path = os.path.join(directory, "execution_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            "executed_files": results,
            "skipped_files": skipped_files,
            "skip_reasons": "网络问题或路径问题等不可修复错误"
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n处理完成! 结果摘要已保存到: {summary_path}")
    if skipped_files:
        print(f"以下文件因不可修复错误被跳过: {', '.join(skipped_files)}")

if __name__ == "__main__":
    # 示例用法
    r_scripts_directory = r"app\data\16317\coding3"
    batch_execute_r_scripts(r_scripts_directory)

    
'''import os
import json
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Optional
from code_fix_framework import CodeFixFramework

class LocalRExecutor:
    """本地R代码执行器"""
    
    def __init__(self, timeout: int = 60):
        """
        初始化本地执行器
        
        参数:
            timeout: 执行超时时间(秒)
        """
        self.timeout = timeout
        self.fix_framework = CodeFixFramework()
    
    def execute_r_script(self, script_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        执行R脚本并返回结果
        
        参数:
            script_path: R脚本路径
            
        返回:
            (执行是否成功, 执行输出或错误信息, 修复后的代码路径)
        """
        try:
            # 直接使用本地Rscript执行命令
            rscript_path = r"C:\Program Files\R\R-4.4.3\bin\x64\Rscript.exe"
            cmd = f'"{rscript_path}" "{script_path}"'
            
            # 执行命令
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                timeout=self.timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return True, result.stdout, None
            
        except subprocess.CalledProcessError as e:
            # 执行失败，提取错误信息
            error_msg = e.stderr if e.stderr else str(e)
            return False, error_msg, None
            
        except subprocess.TimeoutExpired:
            return False, f"执行超时(超过{self.timeout}秒)", None
    
    def diagnose_and_fix(self, script_path: str, error_msg: str, max_attempts: int = 3) -> Tuple[bool, Optional[str], Dict]:
        """
        诊断并修复R脚本错误
        
        参数:
            script_path: 脚本路径
            error_msg: 错误信息
            max_attempts: 最大修复尝试次数
            
        返回:
            (是否修复成功, 修复后的代码路径, 诊断信息)
        """
        with open(script_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # 准备修复后的文件路径
        original_dir = os.path.dirname(script_path)
        original_name = os.path.basename(script_path)
        fixed_path = os.path.join(original_dir, f"fixed_{original_name}")
        
        for attempt in range(max_attempts):
            print(f"\n尝试修复 {original_name} (第 {attempt + 1} 次)...")
            
            # 使用修复框架诊断和修复
            fixed_code, diagnosis, _, _ = self.fix_framework.auto_fix(
                original_code, 
                error_msg,
                language="R"
            )
            
            if not fixed_code:
                print("修复失败: 无法生成修复代码")
                return False, None, diagnosis
            
            # 保存修复后的代码
            with open(fixed_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            
            # 测试修复后的代码
            success, output, _ = self.execute_r_script(fixed_path)
            
            if success:
                print(f"修复成功! 修复后的文件保存为: {fixed_path}")
                return True, fixed_path, diagnosis
            else:
                print(f"修复尝试 {attempt + 1} 失败")
                print("新错误信息:", output)
                error_msg = output  # 使用新错误信息进行下一次尝试
        
        return False, None, diagnosis
    
    def execute_with_auto_fix(self, script_path: str, max_attempts: int = 3) -> Tuple[bool, Optional[str]]:
        """
        执行R脚本并自动修复错误
        
        参数:
            script_path: 脚本路径
            max_attempts: 最大修复尝试次数
            
        返回:
            (最终是否成功, 最终可执行文件路径)
        """
        # 初始执行
        success, output, _ = self.execute_r_script(script_path)
        
        if success:
            print("脚本执行成功!")
            return True, script_path
        
        print("初始执行失败，开始自动修复流程...")
        print("错误信息:", output)
        
        # 尝试修复
        fixed, fixed_path, diagnosis = self.diagnose_and_fix(
            script_path,
            output,
            max_attempts
        )
        
        if fixed:
            return True, fixed_path
        
        print(f"经过 {max_attempts} 次尝试后仍无法修复")
        return False, None

def batch_execute_r_scripts(directory: str):
    """
    批量执行目录下的所有R脚本
    
    参数:
        directory: 包含R脚本的目录路径
    """
    # 检查Rscript是否可用
    try:
        subprocess.run(["Rscript", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 系统中未找到Rscript，请确保R已安装并添加到PATH环境变量中")
        return
    
    executor = LocalRExecutor()
    
    # 确保是绝对路径
    directory = os.path.abspath(directory)
    print(f"\n开始处理目录: {directory}")
    
    # 查找所有R脚本文件
    r_files = [f for f in os.listdir(directory) if f.endswith('.r') or f.endswith('.R')]
    
    if not r_files:
        print("目录中没有找到R脚本文件")
        return
    
    results = []
    
    for r_file in r_files:
        file_path = os.path.join(directory, r_file)
        print(f"\n处理文件: {r_file}")
        
        success, final_path = executor.execute_with_auto_fix(file_path)
        
        results.append({
            "file": r_file,
            "success": success,
            "final_path": final_path,
            "fixed": final_path != file_path if final_path else False
        })
    
    # 保存执行结果摘要
    summary_path = os.path.join(directory, "execution_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n处理完成! 结果摘要已保存到: {summary_path}")

if __name__ == "__main__":
    # 示例用法
    r_scripts_directory = r"app\data\16317\coding3"
    batch_execute_r_scripts(r_scripts_directory)
    '''