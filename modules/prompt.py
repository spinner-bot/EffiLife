"""
    ====== modules/prompt.py ======
    No description.
        by spinner-bot
"""

TEST_INTRODUCTIONS = {
    1: {
        "summary": "运行plan.py和text.py内置测试，启动wizard主循环，清理测试产物。",
        "scope": [
            "Plan类核心功能（初始化、章节/任务/分组管理、时间统计、日志、持久化）",
            "text转换（JSON到TXT）",
            "wizard交互式主循环"
        ],
        "inputs": "无（内部生成测试数据）",
        "outputs": [
            "test_plan_data.json",
            "output/test_plan_render.txt"
        ],
        "cleanup": "强制删除test_plan_data.json和output目录（含内部所有文件）",
        "requirements": "无",
        "notes": "wizard.main需用户手动输入ph退出"
    },
    2: {"name": "base2_test",
        "summary": "创建预定义计划，保存JSON，转换TXT，用记事本打开等待关闭，删除文件并释放索引。",
        "scope": [
            "Plan注册与索引冲突处理（12→10012→100012...）",
            "Plan.save_json",
            "text.convert",
            "外部程序调用（notepad）并等待关闭",
            "文件清理与注册表释放"
        ],
        "inputs": "_build_plan_data预定义计划数据",
        "outputs": [
            "plan_<index>.json",
            "plan_<index>.txt"
        ],
        "cleanup": "删除上述两个文件，从Plan.registry释放对应索引",
        "requirements": "Windows环境（notepad）",
        "notes": "索引冲突时按10^x+12递增（x从4开始）"
    }
}