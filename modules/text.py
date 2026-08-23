"""
    ====== modules/text.py ======
    No description.
        by spinner-bot
"""

import json
import os


def _format_time(time_list):
    """
    核心时间格式化器
    """
    if not isinstance(time_list, list) or len(time_list) < 2:
        return ""
    h, m = time_list[0], time_list[1]

    # 模糊时间处理 (精确到小时，分钟为99)
    if m == 99:
        period = "am" if h < 12 else "pm"
        display_h = h % 12
        if display_h == 0:
            display_h = 12
        return f"{display_h}{period}"

    # 精确时间处理
    return f"{h:02d}:{m:02d}"


def _build_header(head):
    """自适应构建头部标题"""
    date = head.get('date', [0, 0, 0])
    date_str = f"{date[0]}/{date[1]}/{date[2]}"
    index = head.get('index', '')
    name = head.get('name')

    title = f"====== {date_str}  Plan {index}"
    if name:
        title += f"（{name}）"
    title += " ======\n\n\n"
    return title


def _build_sections(main, logs):
    """自适应构建章节与任务列表"""
    text = ""
    total_minutes = 0

    for sec_idx, section in enumerate(main):
        sec_letter = chr(ord('A') + sec_idx)
        sec_name = section.get('name', '未命名章节')
        sec_info = section.get('info')

        sec_title = f"【Section {sec_letter}】{sec_name}"
        if sec_info:
            sec_title += f"（{sec_info}）"
        text += sec_title + "\n"

        # 解析并排序 Groups
        groups = section.get('group', {})
        parsed_groups = []
        for k, v in groups.items():
            try:
                pre, last = map(int, k.split('_'))
                parsed_groups.append((pre, last, v.get('title', '组'), v.get('description', '')))
            except ValueError:
                continue
        parsed_groups.sort(key=lambda x: x[0])

        active_group_end = -1
        tasks = section.get('plan', [])

        for task_num, task in enumerate(tasks):
            if task is None:
                continue

            # 组标题处理
            for g_pre, g_last, g_title, g_desc in parsed_groups:
                if task_num == g_pre:
                    text += f"({g_title}) - {g_desc}\n"
                    active_group_end = g_last
                    break

            t_m = task.get('t_m', 0)
            minutes = t_m * 6
            total_minutes += minutes

            indent = "    " if task_num <= active_group_end else ""
            # 分钟数取整，不显示小数
            line = f"{indent}{task_num}.{task.get('content', '')}（{round(minutes)}分钟"

            line += "）\n"
            text += line

            if task_num == active_group_end:
                active_group_end = -1

        text += "\n"

    return text, total_minutes


def _build_logs(logs):
    """构建进展日志部分"""
    if not logs:
        return ""

    text = "------------------------------------------------------------\n"
    text += "进展：【time | plan】\n\n"

    for i, log in enumerate(logs, 1):
        t = _format_time(log.get('time'))
        p = log.get('plan', 'base')
        c = log.get('content', '')
        text += f"{i}.【{t} | {p}】{c}\n"

    return text


def convert(path_in: str, path_out: str) -> int:
    """
    主转换接口
    :param path_in: JSON 数据文件路径
    :param path_out: 输出的文本文件路径
    :return: 0 表示成功，-1 表示非致命数据警告。致命错误（如文件不存在）直接抛出异常。
    """
    # 致命错误：文件不存在或JSON格式损坏，直接抛出异常让主程序处理
    with open(path_in, 'r', encoding='utf-8') as f:
        data = json.load(f)

    head = data.get('head', {})
    main = data.get('main', [])
    logs = data.get('log', [])

    # 1. 组装各部分内容 (内部已做非致命错误的容错处理)
    header_text = _build_header(head)
    sections_text, total_minutes = _build_sections(main, logs)

    # 2. 自适应总时间统计
    total_hours = total_minutes / 60
    if total_hours.is_integer():
        h_str = f"{int(total_hours)}h"
    else:
        h_str = f"{total_hours:.1f}h"
    summary_text = f"\n这份计划需要 {h_str} 的有效工作时间。\n"

    # 3. 组装日志
    logs_text = _build_logs(logs)

    # 4. 写入文件
    final_text = header_text + sections_text + summary_text + logs_text

    out_dir = os.path.dirname(path_out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(path_out, 'w', encoding='utf-8') as f:
        f.write(final_text)

    return 0



def run_test2():
    test_in = "test_plan_data.json"
    test_out = "output/test_plan_render.txt"

    try:
        res = convert(test_in, test_out)
        if res == 0:
            print(f"✅ 测试通过：转换成功，已保存至 {test_out}")
        else:
            print(f"⚠️ 测试警告：转换完成但存在数据缺失，返回码 {res}")
    except FileNotFoundError:
        print(f"❌ 测试失败：找不到输入文件 {test_in}")
    except json.JSONDecodeError:
        print(f"❌ 测试失败：{test_in} 不是合法的 JSON 文件")
    except Exception as e:
        print(f"❌ 测试失败：发生未知错误 -> {e}")

# ==========================================
# 测试代码 (仅在直接运行此文件时执行)
# ==========================================
if __name__ == "__main__":
    run_test2()