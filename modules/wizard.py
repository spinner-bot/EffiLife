"""
    ====== wizard.py ======
    No description.
        by spinner-bot
"""
import os
import json
import datetime
from plan import Plan  # 假设 plan.py 在同级目录
import text  # 假设 text.py 在同级目录


# ==========================================
# 辅助工具函数
# ==========================================

def parse_time_input(time_str: str) -> list:
    """
    解析用户输入的时间字符串。
    支持格式: "10:30", "8am", "2pm", "12pm"
    返回: [hour, minute] 列表。如果是模糊时间(am/pm)，minute 设为 99。
    """
    time_str = time_str.strip().lower()
    if not time_str:
        return None

    if 'am' in time_str or 'pm' in time_str:
        period = 'am' if 'am' in time_str else 'pm'
        h_str = time_str.replace('am', '').replace('pm', '').strip()
        try:
            h = int(h_str)
            if period == 'pm' and h != 12:
                h += 12
            elif period == 'am' and h == 12:
                h = 0
            return [h, 99]
        except ValueError:
            return None
    elif ':' in time_str:
        try:
            h, m = map(int, time_str.split(':'))
            return [h, m]
        except ValueError:
            return None
    return None


def get_valid_int(prompt: str, min_val: int, max_val: int, allow_zero=False) -> int:
    """安全获取整数输入"""
    while True:
        try:
            val = int(input(prompt))
            if allow_zero and val == 0:
                return 0
            if min_val <= val <= max_val:
                return val
            print(f"⚠️ 输入无效，请输入 {min_val} 到 {max_val} 之间的数字。")
        except ValueError:
            print("⚠️ 请输入有效的数字。")


def confirm_action(prompt: str) -> bool:
    """二次确认"""
    choice = input(f"{prompt} (y/n): ").strip().lower()
    return choice == 'y' or choice == 'yes'


# ==========================================
# 核心交互流程
# ==========================================

def create_plan_flow():
    """流程 1-9：创建新计划"""
    print("\n" + "=" * 40)
    print("🚀 创建新计划模式")
    print("=" * 40)

    # (隐式) 2. 申请 Index (临时逻辑：默认使用 1，或让用户输入)
    index = Plan.request_id()
    print(f"ℹ️ Plan ID: {index}")

    # (显式) 3. 询问名称和日期
    name = input("请输入 Plan 名称 (回车跳过): ").strip() or None

    today = datetime.date.today()
    date_prompt = f"请输入日期 (YYYY-MM-DD, 回车使用今天 {today}): "
    date_str = input(date_prompt).strip()
    if date_str:
        try:
            y, m, d = map(int, date_str.split('-'))
            date_tuple = (y, m, d)
        except ValueError:
            print("⚠️ 日期格式错误，已回退使用今天日期。")
            date_tuple = (today.year, today.month, today.day)
    else:
        date_tuple = (today.year, today.month, today.day)

    # (隐式) 4. 实例化 Plan
    p = Plan(index, name, date_tuple)
    print(f"✅ 计划实例已创建: Plan {index}")

    # (显式) 5 & 6. 进入 Section 层编辑
    section_layer(p)

    # (显式) 7. 提示创建成功及总时间
    total_h, total_m = p.time_sum()
    print("\n" + "=" * 40)
    print("🎉 计划构建完成！")
    print(f"⏱️ 这份计划预计需要 {total_h:.1f} 小时 的有效工作时间。")
    print("=" * 40)

    # (隐式/临时) 8. 询问 JSON 保存地址
    json_name = f"plan_{index}.json"
    json_path = input(f"请输入 JSON 保存路径 (回车保存至当前目录 ./{json_name}): ").strip()
    if not json_path:
        json_path = json_name

    # 确保目录存在并保存
    out_dir = os.path.dirname(json_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)
    p.save_json(json_path)  # 假设 plan.py 有 save_json 方法，或者直接 p.save(json_path)
    print(f"✅ JSON 已保存至: {json_path}")

    # (显式/临时) 9. 转 TXT
    txt_path = json_path.replace('.json', '.txt')
    txt_input = input(f"请输入 TXT 保存路径 (回车保存至当前目录 ./{txt_path}): ").strip()
    if txt_input:
        txt_path = txt_input

    text.convert(json_path, txt_path)
    print(f"✅ TXT 已生成并保存至: {txt_path}")


def section_layer(p: Plan):
    """流程 5：Section 层交互"""
    while True:
        print("\n--- 📂 Section 层 ---")
        valid_sections = [(i, sec) for i, sec in enumerate(p.plan['main']) if sec is not None]

        if not valid_sections:
            print("[当前暂无 Section，请先创建]")
        else:
            for i, sec in valid_sections:
                info = f" ({sec['info']})" if sec.get('info') else ""
                print(f"  {i}. {sec['name']}{info}")

        print("\n[操作菜单]")
        print("  1. 创建 Section")
        print("  2. 进入 Section")
        print("  3. 注销 Section")
        print("  0. 确认编辑 (完成并返回)")

        choice = input("请选择操作: ").strip()

        if choice == '1':
            sec_name = input("  请输入模块名: ").strip()
            if not sec_name:
                print("  ⚠️ 模块名不能为空。")
                continue
            sec_info = input("  请输入补充信息 (回车跳过): ").strip()

            p.add_section(sec_name, sec_info)
            print(f"  ✅ Section '{sec_name}' 创建成功，自动进入编辑...")
            # 自动进入刚创建的 Section (索引为 len(main)-1)
            plan_layer(p, len(p.plan['main']) - 1)

        elif choice == '2':
            if not valid_sections: continue
            idx = get_valid_int("  请输入要进入的 Section 编号: ", 0, len(p.plan['main']) - 1)
            if p.plan['main'][idx] is None:
                print("  ⚠️ 该 Section 已被注销。")
                continue
            plan_layer(p, idx)

        elif choice == '3':
            if not valid_sections: continue
            idx = get_valid_int("  请输入要注销的 Section 编号: ", 0, len(p.plan['main']) - 1)
            if p.plan['main'][idx] is None:
                print("  ⚠️ 该 Section 已被注销。")
                continue
            if confirm_action(f"  确定要注销 Section '{p.plan['main'][idx]['name']}' 吗？(此操作为软删除)"):
                # 调用 del_section 或直接软删除
                if hasattr(p, 'del_section'):
                    p.del_section(idx)
                else:
                    p.plan['main'][idx] = None
                print("  ✅ Section 已注销。")

        elif choice == '0':
            print("✅ 退出 Section 层。")
            break
        else:
            print("⚠️ 无效输入。")


def plan_layer(p: Plan, sec_idx: int):
    """流程 6：Plan (Task) 层交互"""
    section = p.plan['main'][sec_idx]
    tasks = section['plan']
    group_stack = []  # 用于管理嵌套组的栈：存储 (start_idx, title, desc)

    while True:
        print(f"\n--- 📝 Plan 层: {section['name']} ---")
        valid_tasks = [(i, t) for i, t in enumerate(tasks) if t is not None and i > 0]

        if not valid_tasks:
            print("[当前暂无计划，请先创建]")
        else:
            for i, t in valid_tasks:
                mins = t['t_m'] * 6
                print(f"  {i}. {t['content']} ({mins}分钟)")

        # 显示当前组栈状态
        if group_stack:
            print(f"  📌 当前处于组嵌套中 (深度: {len(group_stack)})")

        print("\n[操作菜单]")
        print("  1. 创建计划 (向前一步)")
        print("  2. 创建组 (向下一级)")
        print("  3. 声明组结束 (向上一级)")
        print("  4. 注销计划")
        print("  5. 清空 Section")
        print("  0. 完成编辑 (返回 Section 层)")

        choice = input("请选择操作: ").strip()

        if choice == '1':
            content = input("  请输入计划内容: ").strip()
            if not content:
                print("  ⚠️ 内容不能为空。")
                continue
            mins_str = input("  请输入预计耗时 (分钟): ").strip()
            try:
                mins = float(mins_str)
                t_m = mins / 6  # 转换为底层存储的 t_m 单位
            except ValueError:
                print("  ⚠️ 耗时必须是数字。")
                continue

            p.add_plan(sec_idx, content, t_m)
            print(f"  ✅ 计划已添加。")

        elif choice == '2':
            title = input("  请输入组标题 (如 '组'): ").strip() or "组"
            desc = input("  请输入组描述: ").strip()
            # 记录下一个要创建的 task 的索引作为起点
            start_idx = len(tasks)
            group_stack.append((start_idx, title, desc))
            print(f"  ✅ 组 '{title}' 开始，起点索引: {start_idx}")

        elif choice == '3':
            if not group_stack:
                print("  ⚠️ 当前没有未结束的组。")
                continue
            start_idx, title, desc = group_stack.pop()
            # 最后一个有效 task 的索引作为终点
            end_idx = len(tasks) - 1
            if end_idx < start_idx:
                print("  ⚠️ 组内没有有效计划，无法结束。")
                group_stack.append((start_idx, title, desc))  # 压回去
                continue

            p.add_group(sec_idx, title, desc, start_idx, end_idx)
            print(f"  ✅ 组 '{title}' 结束，范围: {start_idx} ~ {end_idx}")

        elif choice == '4':
            if not valid_tasks: continue
            t_idx = get_valid_int("  请输入要注销的计划编号: ", 1, len(tasks) - 1)
            if tasks[t_idx] is None:
                print("  ⚠️ 该计划已被注销。")
                continue
            if confirm_action(f"  确定要注销计划 '{tasks[t_idx]['content']}' 吗？"):
                tasks[t_idx] = None
                print("  ✅ 计划已注销。")

        elif choice == '5':
            if confirm_action("  ⚠️ 确定要清空该 Section 下的所有计划吗？(不可恢复)"):
                # 保留索引 0 的占位符，其余全部置为 None
                section['plan'] = [None]
                section['group'] = {}
                group_stack.clear()
                print("  ✅ Section 已清空。")

        elif choice == '0':
            # 约束：必须至少含有 1 个有效 plan 才可返回
            if not valid_tasks:
                print("  ⚠️ 拒绝返回：Section 中必须至少含有 1 个有效计划。")
                continue
            if group_stack:
                print("  ⚠️ 拒绝返回：还有未结束的组，请先声明组结束。")
                continue
            print("✅ 退出 Plan 层。")
            break
        else:
            print("⚠️ 无效输入。")


def add_log_flow():
    """流程 10：增加记录模式 (临时实现)"""
    print("\n" + "=" * 40)
    print("📝 增加记录模式")
    print("=" * 40)

    base_path = input("请输入计划文件相对路径/名称 (如 plan_1，无需后缀): ").strip()
    if not base_path:
        print("⚠️ 路径不能为空。")
        return

    json_path = f"{base_path}.json"
    txt_path = f"{base_path}.txt"

    if not os.path.exists(json_path):
        print(f"❌ 找不到文件: {json_path}")
        return

    # 加载 JSON 到内存实例 (临时逻辑：直接读取字典并挂载到 Plan 实例)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 假设 Plan 可以通过传入基础参数实例化，然后直接覆盖 plan 属性
    p = Plan(data['head']['index'], data['head'].get('name'), tuple(data['head']['date']))
    p.plan = data

    print(f"✅ 成功加载计划: Plan {p.plan['head']['index']}")

    while True:
        print("\n--- 添加新日志 ---")
        plan_id = input("请输入归属计划 ID (如 A1, 或 base, 输入 q 退出): ").strip()
        if plan_id.lower() == 'q':
            break

        time_str = input("请输入时间 (如 10:30, 8am, 回车使用当前时间): ").strip()
        if not time_str:
            now = datetime.datetime.now()
            time_list = [now.hour, now.minute]
        else:
            time_list = parse_time_input(time_str)
            if not time_list:
                print("⚠️ 时间格式错误，请重试。")
                continue

        content = input("请输入进展内容: ").strip()
        if not content:
            print("⚠️ 内容不能为空。")
            continue

        # 添加日志 (假设 add_log 签名为 index, plan_id, time, content)
        # 注意：这里的 index 是 log 的自增索引，可以用 len(logs) 代替
        log_idx = len(p.plan.get('log', []))
        p.add_log(log_idx, plan_id, time_list, content)
        print(f"✅ 日志已添加: [{time_list} | {plan_id}] {content}")

        # 实时保存
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(p.plan, f, ensure_ascii=False, indent=4)
        text.convert(json_path, txt_path)
        print("✅ 已同步保存至 JSON 和 TXT。")


# ==========================================
# 主程序入口
# ==========================================

def main():
    while True:
        print("\n" + "=" * 40)
        print("🧙‍♂️ Plan Wizard 主控台")
        print("=" * 40)
        print("  1. 创建新计划")
        print("  2. 增加记录")
        print("  0. 退出")

        choice = input("请选择模式: ").strip()

        if choice == '1':
            create_plan_flow()
        elif choice == '2':
            add_log_flow()
        elif choice == '0':
            print("👋 再见！")
            break
        else:
            print("⚠️ 无效输入，请重新选择。")


if __name__ == "__main__":
    main()