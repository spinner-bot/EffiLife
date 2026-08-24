"""
    ====== modules/prompt.py ======
    No description.
        by spinner-bot
"""

import json
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

PLAN_PROMPT = {
    "type": "plan_generation_prompt",
    "version": "1.1",
    "prompt": """你是一个计划生成助手，需要根据用户需求生成一个结构化的计划数据，并以 JSON 格式输出。请严格遵循以下数据结构和规则。

## 整体结构
输出一个 JSON 对象，包含三个顶层键：`head`、`main`、`log`。

### head
{
    "index": 整数,          // 计划唯一索引，可随机生成但需唯一
    "name": 字符串或 null,   // 计划名称，可空
    "date": [年, 月, 日]    // 计划日期，整数列表
}

### main
`main` 是一个列表，每个元素代表一个章节（Section），章节顺序对应字母 A、B、C...（第一个章节为 A，第二个为 B，以此类推）。

每个章节对象包含：
- `"name"`: 字符串，章节主名称。
- `"info"`: 字符串，补充说明，可为空字符串。
- `"plan"`: 列表，任务列表。**第一个元素必须为 null**，之后每个任务按顺序排列，任务在列表中的索引即为任务编号（从 1 开始）。任务对象包含：
  - `"is_active"`: 布尔值，通常为 true。
  - `"content"`: 字符串，任务描述。
  - `"t_m"`: 数字，预计耗时的 6 分钟块数。实际分钟数 = t_m * 6。例如 15 分钟 -> 2.5，30 分钟 -> 5，75 分钟 -> 12.5。
  - 可选 `"finish"`: 对象，如果任务已完成。包含 `"time"`: [小时, 分钟] 和 `"day"`: 整数天数偏移。
- `"group"`: 对象，用于将连续的任务分组。键格式为 `"起始任务索引_结束任务索引"`（字符串），值包含 `"title"`（组标题）和 `"description"`（组描述）。例如 `"2_4"` 表示从任务2到任务4属于同一组。

### log
`log` 是一个列表，记录进展日志，可为空。每条日志对象包含：
- `"day"`: 整数，相对于计划起始日的天数偏移（0 或 1 等）。
- `"plan"`: 字符串，关联的任务 ID（如 "A1"）或 "base" 表示非特定任务。
- `"time"`: [小时, 分钟]，分钟为 99 表示只精确到小时（如 [9, 99] 表示 9am），否则为 [时, 分] 精确时间。
- `"content"`: 字符串，进展内容。

## 任务 ID 生成规则
任务 ID 由章节字母和任务索引组成，例如第一个章节（A）的第一个任务为 "A1"，第二个为 "A2"；第二个章节（B）的第一个任务为 "B1"。

## 时间格式
- 小时：0-23 整数。
- 分钟：0-59 整数，或 99 表示模糊时间（如 9am 用 [9,99]）。
- 日期为 [年, 月, 日] 整数列表。

## 其他注意事项
- 确保 main 中每个 plan 列表的第一个元素是 null。
- 组（group）的范围不能重叠或交叉，但可以嵌套（完全包含）。不要生成重叠范围。
- 任务内容应简洁明确。
- 输出必须是合法的 JSON，不包含任何额外解释或代码块标记（如 ```json```）。

请根据用户输入的需求，生成一个完整的计划 JSON。"""
}

def test_prompt(mode=0):
    if not mode-1:
        TEST_INTRODUCTIONS.clear()
        return 0
    try:
        fp="data/LLM/knowledge_base/product/test_introductions.json"
        with open(fp,'w',encoding='utf-8') as f:
            json.dump(TEST_INTRODUCTIONS, f, ensure_ascii=False, indent=4)
        return 0
    except Exception as e:
        return e

def report_tp():
    return f"\n====== 测试知识库初始化 ======\n\n{f"success:{len(TEST_INTRODUCTIONS)} (data/LLM/knowledge_base/product/test_introductions.json)" if not test_prompt() else "failed to save TEST_INTRODUCTIONS"}{f"\n释放内存成功：TEST_INTRODUCTIONS已清空" if not test_prompt(1) else ""}\n"