# 方法1：从JSON文件执行
manager = CodeExecutionManager()
results = manager.run_from_json('your_file.json')

# 方法2：直接执行代码块
code_blocks = [
    {
        "python核心代码行": "def hello(): return 'Hello World'",
        "python代码调用链代码": ["result = hello()"],
        "python代码关联参数": {},
        "python代码引用依赖库": []
    }
]
results = manager.run_custom_code(code_blocks)
