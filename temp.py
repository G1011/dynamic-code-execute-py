import json
import os
import tempfile
import importlib.util
import sys
from typing import List, Dict, Any, Tuple
import traceback
import shutil

class CodeExecutor:
    def __init__(self):
        self.temp_dir = None
        self.temp_files = []
        
    def setup_temp_directory(self):
        """创建临时目录用于存储生成的文件"""
        self.temp_dir = tempfile.mkdtemp(prefix="code_executor_")
        print(f"创建临时目录: {self.temp_dir}")
        
    def cleanup_temp_directory(self):
        """清理临时目录"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"清理临时目录: {self.temp_dir}")
            
    def create_module_file(self, module_name: str, code_content: str) -> str:
        """创建模块文件"""
        file_path = os.path.join(self.temp_dir, f"{module_name}.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        self.temp_files.append(file_path)
        return file_path
        
    def create_test_suite_file(self, suite_name: str, code_content: str) -> str:
        """创建测试套件文件"""
        file_path = os.path.join(self.temp_dir, f"{suite_name}.testsuit.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        self.temp_files.append(file_path)
        return file_path
        
    def create_enx_file(self, enx_name: str, code_content: str) -> str:
        """创建enx文件"""
        file_path = os.path.join(self.temp_dir, f"{enx_name}.enx.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        self.temp_files.append(file_path)
        return file_path
        
    def execute_code_chain(self, code_chain: List[str], dependencies: List[str]) -> Dict[str, Any]:
        """执行代码调用链"""
        results = {}
        
        # 处理依赖库
        for dep in dependencies:
            try:
                if dep not in sys.modules:
                    importlib.import_module(dep)
                    print(f"导入依赖库: {dep}")
            except ImportError as e:
                print(f"导入依赖库失败 {dep}: {e}")
                
        # 创建临时目录
        self.setup_temp_directory()
        
        try:
            # 执行每个代码片段
            for i, code_item in enumerate(code_chain):
                if isinstance(code_item, dict):
                    # 如果是字典格式，提取各个字段
                    module_name = code_item.get('python代码仓', f'module_{i}')
                    code_path = code_item.get('python代码路径', '')
                    core_code = code_item.get('python核心代码行', '')
                    call_chain = code_item.get('python代码调用链代码', [])
                    params = code_item.get('python代码关联参数', {})
                    deps = code_item.get('python代码引用依赖库', [])
                    
                    # 创建模块文件
                    if core_code:
                        module_file = self.create_module_file(module_name, core_code)
                        print(f"创建模块文件: {module_file}")
                        
                        # 动态导入模块
                        spec = importlib.util.spec_from_file_location(module_name, module_file)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # 执行相关代码
                        if call_chain:
                            result = self.execute_call_chain(module, call_chain, params)
                            results[f'call_chain_{i}'] = result
                            
                elif isinstance(code_item, str):
                    # 如果是字符串，直接执行
                    result = self.execute_single_code(code_item, f"code_{i}")
                    results[f'code_{i}'] = result
                    
        except Exception as e:
            print(f"执行过程中出现错误: {e}")
            traceback.print_exc()
        finally:
            # 清理临时文件
            self.cleanup_temp_directory()
            
        return results
        
    def execute_call_chain(self, module, call_chain: List[str], params: Dict) -> Dict:
        """执行调用链"""
        results = {
            'parameters': params,
            'results': {}
        }
        
        try:
            # 将参数添加到模块的全局命名空间
            for key, value in params.items():
                setattr(module, key, value)
                
            # 执行调用链中的每个函数调用
            for i, call in enumerate(call_chain):
                try:
                    # 使用eval或exec执行调用
                    if call.strip().startswith('def ') or call.strip().startswith('class '):
                        # 这是定义语句，需要使用exec
                        exec(call, module.__dict__)
                    else:
                        # 这是调用语句，可以使用eval
                        if '=' in call:
                            # 赋值语句
                            exec(call, module.__dict__)
                        else:
                            # 函数调用
                            result = eval(call, module.__dict__)
                            results['results'][f'call_{i}'] = result
                except Exception as e:
                    print(f"执行调用链第{i}项失败: {call}, 错误: {e}")
                    results['results'][f'call_{i}_error'] = str(e)
                    
        except Exception as e:
            print(f"执行调用链时出错: {e}")
            results['error'] = str(e)
            
        return results
        
    def execute_single_code(self, code: str, name: str) -> Dict:
        """执行单个代码段"""
        results = {
            'code': code,
            'name': name,
            'result': None,
            'error': None
        }
        
        try:
            # 创建临时文件
            temp_file = os.path.join(self.temp_dir, f"{name}.py")
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)
                
            # 动态执行
            spec = importlib.util.spec_from_file_location(name, temp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取模块中的所有变量
            module_vars = {k: v for k, v in module.__dict__.items() 
                          if not k.startswith('_') and not callable(v)}
            results['result'] = module_vars
            
        except Exception as e:
            results['error'] = str(e)
            print(f"执行代码失败: {e}")
            
        return results
        
    def process_json_file(self, json_file_path: str) -> Dict[str, Any]:
        """处理JSON文件"""
        results = {}
        
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"加载了 {len(data)} 个代码对象")
            
            # 遍历每个代码对象
            for i, item in enumerate(data):
                print(f"\n处理第 {i+1} 个代码对象...")
                
                # 提取字段
                python_code_repo = item.get('python代码仓', '')
                python_code_path = item.get('python代码路径', '')
                core_code = item.get('python核心代码行', '')
                call_chain = item.get('python代码调用链代码', [])
                params = item.get('python代码关联参数', {})
                dependencies = item.get('python代码引用依赖库', [])
                
                print(f"代码仓: {python_code_repo}")
                print(f"代码路径: {python_code_path}")
                print(f"核心代码长度: {len(core_code) if core_code else 0}")
                print(f"调用链长度: {len(call_chain) if call_chain else 0}")
                print(f"参数: {params}")
                print(f"依赖库: {dependencies}")
                
                # 执行代码链
                execution_result = self.execute_code_chain([core_code], dependencies)
                results[f'item_{i}'] = {
                    'code_repo': python_code_repo,
                    'code_path': python_code_path,
                    'core_code': core_code,
                    'call_chain': call_chain,
                    'parameters': params,
                    'dependencies': dependencies,
                    'execution_result': execution_result
                }
                
        except Exception as e:
            print(f"处理JSON文件时出错: {e}")
            traceback.print_exc()
            
        return results

# 示例使用类
class CodeExecutionManager:
    def __init__(self):
        self.executor = CodeExecutor()
        
    def run_from_json(self, json_file_path: str) -> Dict[str, Any]:
        """从JSON文件运行代码执行"""
        return self.executor.process_json_file(json_file_path)
        
    def run_custom_code(self, code_blocks: List[Dict]) -> Dict[str, Any]:
        """运行自定义代码块"""
        results = {}
        
        for i, block in enumerate(code_blocks):
            try:
                # 提取字段
                core_code = block.get('python核心代码行', '')
                call_chain = block.get('python代码调用链代码', [])
                params = block.get('python代码关联参数', {})
                dependencies = block.get('python代码引用依赖库', [])
                
                # 执行代码
                result = self.executor.execute_code_chain([core_code], dependencies)
                results[f'block_{i}'] = {
                    'core_code': core_code,
                    'call_chain': call_chain,
                    'parameters': params,
                    'dependencies': dependencies,
                    'result': result
                }
            except Exception as e:
                results[f'block_{i}_error'] = str(e)
                
        return results

# 创建示例JSON数据的函数
def create_sample_json():
    """创建示例JSON文件"""
    sample_data = [
        {
            "python代码仓": "example_repo",
            "python代码路径": "/path/to/example.py",
            "python核心代码行": """
def add_numbers(a, b):
    return a + b

def multiply_numbers(x, y):
    return x * y

def process_data(data_list):
    return [x * 2 for x in data_list]
""",
            "python代码调用链代码": [
                "result1 = add_numbers(5, 3)",
                "result2 = multiply_numbers(result1, 2)",
                "data = [1, 2, 3, 4]",
                "processed_data = process_data(data)"
            ],
            "python代码关联参数": {
                "param1": 10,
                "param2": 20
            },
            "python代码引用依赖库": ["math", "collections"]
        },
        {
            "python代码仓": "another_repo",
            "python代码路径": "/path/to/another.py",
            "python核心代码行": """
import math

def calculate_circle_area(radius):
    return math.pi * radius ** 2

def format_number(num, decimals=2):
    return round(num, decimals)
""",
            "python代码调用链代码": [
                "area = calculate_circle_area(5)",
                "formatted_area = format_number(area)"
            ],
            "python代码关联参数": {
                "radius": 5.0
            },
            "python代码引用依赖库": ["math"]
        }
    ]
    
    with open('sample_codes.json', 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print("已创建示例JSON文件: sample_codes.json")

# 主程序入口
def main():
    """主函数"""
    # 创建示例数据
    create_sample_json()
    
    # 创建执行管理器
    manager = CodeExecutionManager()
    
    try:
        # 从JSON文件执行
        print("开始执行JSON文件中的代码...")
        results = manager.run_from_json('sample_codes.json')
        
        # 输出结果
        print("\n" + "="*50)
        print("执行结果:")
        print("="*50)
        
        for key, value in results.items():
            print(f"\n{key}:")
            print(f"  代码仓: {value['code_repo']}")
            print(f"  参数: {value['parameters']}")
            print(f"  执行结果: {value['execution_result']}")
            
    except Exception as e:
        print(f"程序执行出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
