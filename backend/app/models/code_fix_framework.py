# code_fix_framework.py
import os
import json
import time
from typing import Dict, Optional, Tuple
from pathlib import Path


from our_utils import model_generate, parser_json, prompts, config_list

class CodeFixFramework:
    """基于LLM的代码修改框架，包含诊断、分类和修复功能"""
    
    def __init__(self, max_retries: int = 3):
        """
        初始化代码修复框架
        
        参数:
            max_retries: 最大重试次数
        """
        self.max_retries = max_retries
        self.error_categories = {
            "syntax": "语法错误",
            "dependency": "依赖问题",
            "logic": "逻辑错误",
            "environment": "环境问题",
            "data": "数据问题",
            "path":"路径问题",
            "connect":"网络问题",
            "other": "其他错误"
        }
    
    def diagnose_error(self, code: str, error_msg: str, language: str = "R") -> Tuple[Optional[Dict], int, int]:
        """
        诊断代码错误并分类
        
        参数:
            code: 源代码
            error_msg: 错误信息
            language: 编程语言
            
        返回:
            (诊断结果字典, 输入token数, 输出token数)
        """
        prompt = f"""
        请分析以下{language}代码错误并分类:

        代码:
        ```{language.lower()}
        {code}
        ```

        错误信息:
        {error_msg}

        请用JSON格式回复，包含以下字段:
        - "error_type": 错误类型(从{sorted(self.error_categories.values())}中选择)
        - "confidence": 置信度(0-1)
        - "root_cause": 根本原因分析(中文)
        - "suggested_fix": 修复建议(中文)
        """
        
        response, input_tokens, output_tokens = model_generate(prompt)
        
        if not response:
            return None, input_tokens, output_tokens
            
        try:
            diagnosis, parse_input, parse_output = parser_json(response, prompts)
            return diagnosis, input_tokens + parse_input, output_tokens + parse_output
        except Exception as e:
            print(f"解析诊断结果失败: {str(e)}")
            return None, input_tokens, output_tokens
    
    def generate_fix(self, code: str, diagnosis: Dict, language: str = "R") -> Tuple[Optional[str], int, int]:
        """
        根据诊断结果生成修复后的代码
        
        参数:
            code: 源代码
            diagnosis: 诊断结果
            language: 编程语言
            
        返回:
            (修复后的代码, 输入token数, 输出token数)
        """
        if not diagnosis:
            return None, 0, 0
            
        prompt = f"""
        根据以下错误诊断修复{language}代码:

        诊断结果:
        {json.dumps(diagnosis, indent=2, ensure_ascii=False)}

        原始代码:
        ```{language.lower()}
        {code}
        ```

        要求:
        1. 返回完整的修复后代码
        2. 添加注释说明修改原因，每行注释前记得加'#'
        3. 保持原始功能不变
        4. 使用英文注释
        """
        
        fixed_code, input_tokens, output_tokens = model_generate(
            prompt
        )
        
        return fixed_code, input_tokens, output_tokens
    
    def auto_fix(self, code: str, error_msg: str, language: str = "R") -> Tuple[Optional[str], Dict, int, int]:
        """
        自动诊断并修复代码错误
        
        参数:
            code: 源代码
            error_msg: 错误信息
            language: 编程语言
            
        返回:
            (修复后的代码, 诊断结果, 总输入token数, 总输出token数)
        """
        total_input = 0
        total_output = 0
        
        # 第一步：诊断错误
        diagnosis, diag_input, diag_output = self.diagnose_error(code, error_msg, language)
        total_input += diag_input
        total_output += diag_output
        
        if not diagnosis:
            print("错误诊断失败")
            return None, {}, total_input, total_output
        
        print(f"诊断结果: {diagnosis.get('error_type', '未知错误')}")
        print(f"原因分析: {diagnosis.get('root_cause', '无')}")
        
        # 第二步：生成修复
        fixed_code, fix_input, fix_output = self.generate_fix(code, diagnosis, language)
        total_input += fix_input
        total_output += fix_output
        
        return fixed_code, diagnosis, total_input, total_output

def test_framework():
    """测试代码修复框架"""
    framework = CodeFixFramework()
    
    # 测试案例1：简单的R代码语法错误
    print("\n=== 测试案例1: 语法错误 ===")
    r_code = """
    # 计算平均值
    calculate_mean <- function(x) {
      mean_value <- sum(x) / lenght(x)  # 故意拼错length
      return(mean_value)
    }
    
    result <- calculate_mean(c(1, 2, 3))
    """
    error_msg = "Error in sum(x)/lenght(x) : could not find function \"lenght\""
    
    fixed_code, diagnosis, input_tokens, output_tokens = framework.auto_fix(r_code, error_msg)
    
    if fixed_code:
        print("\n修复后的代码:")
        print(fixed_code)
    else:
        print("修复失败")
    
    print(f"\n资源消耗: 输入token={input_tokens}, 输出token={output_tokens}")
    
    # 测试案例2：Python依赖错误
    print("\n=== 测试案例2: 依赖错误 ===")
    py_code = """
    import numpy as np
    import non_existent_lib
    
    def process_data(data):
        arr = np.array(data)
        result = non_existent_lib.magic_process(arr)
        return result
    """
    error_msg = "ModuleNotFoundError: No module named 'non_existent_lib'"
    
    fixed_code, diagnosis, input_tokens, output_tokens = framework.auto_fix(py_code, error_msg, language="python")
    
    if fixed_code:
        print("\n修复后的代码:")
        print(fixed_code)
    else:
        print("修复失败")
    
    print(f"\n资源消耗: 输入token={input_tokens}, 输出token={output_tokens}")

if __name__ == "__main__":
    test_framework()

