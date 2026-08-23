# plan组装件
from datetime import datetime
import json
from pathlib import Path
import os

def t(index):
    now = datetime.now()
    y = now.year
    m = now.month
    d = now.day
    h = now.hour
    mi = now.minute
    s = now.second
    h12 = (h-1)%12+1
    pm = h//12
    pms = 'pm' if pm == 1 else 'am'
    items=(now, y, m, d, h, mi, s, h12, pm, pms)
    if str(index).isdigit():
        return items[int(index) if int(index) < 10 else 0]
    else:
        temp=("y","m","d","h","mi","s","h12","pm","pms")
        if index in temp:
            return items[1+temp.index(index)]
        else:
            return items[0]

class Plan:
    registry = {}

    def __init__(self, index, name=None, date=None):
        if str(index).isdigit():
            if not int(index) in Plan.registry:
                self.index = int(index)
                self.plan = Plan.reset(index, name, date)
                Plan.registry[self.index] = self
            else:
                raise IndexError("index occupied")
        else:
            raise IndexError("index not valid")

    @staticmethod
    def reset(index, name=None, date=None):
        temp={
            "head": {
                "index": index,
                "name": name,
                "date": date if date else (t(1),t(2),t(3))
            },
            "main": [],
            "log":[]
        }
        return temp

    @staticmethod
    def num2char(num):
        result = ""
        n = int(num)
        while n >= 0:
            result = chr(65 + n % 26) + result
            n = n // 26 - 1
        return result

    @staticmethod
    def char2num(char):
        index=-1
        for i in range(len(char)):
            if ord(char[i])>=65 and ord(char[i])<=90:
                index+=(ord(char[i])-64)*(26**(len(char)-1-i))
            else:
                index=-1
                break
        return index

    @staticmethod
    def sep_index(char):
        if char:
            index = ["", 0]
            temp = 0
            bad_char = True
            for i in range(len(char)):
                if ord(char[i]) >= 65 and ord(char[i]) <= 90:
                    index[0] += char[i]
                else:
                    if i > 0:
                        bad_char = False
                        index[0] = Plan.char2num(index[0])
                        temp = i
                        break
                    else:
                        return (-2, -2)
            if bad_char:
                index[0] = Plan.char2num(index[0])
                temp = len(char)
            spare = char[temp:]
            if spare:
                if spare.isdigit():
                    try:
                        index[1] = int(spare)
                    except:
                        return (index[0], -2)
                else:
                    index[1] = -2
            else:
                index[1] = -1
            return tuple(index)
        return(-3,-3)

    @staticmethod
    def index_valid(char):
        test=Plan.sep_index(char)
        valid=1
        for i in range(2):
            if test[i]<0:
                return False
        else:
            return True

    @staticmethod
    def syn_index(section, plan):
        return Plan.num2char(section)+str(plan) if str(section).isdigit() and str(plan).isdigit() else ""

    def add_section(self, name, info):
        self.plan["main"].append({
            "name":name,
            "info":info,
            "plan":[None,],
            "group":{}
        })

    def del_section(self, index):
        self.plan["main"][index]["plan"] = [None,]

    def pur_section(self, index):
        pass # 这个功能较难实现，暂时空置

    def add_plan(self, section, content, t_m):
        self.plan["main"][section]["plan"].append({
            "is_active": True,
            "content": content,
            "t_m": t_m
        })
        return Plan.syn_index(section, len(self.plan["main"][section]["plan"])-1)

    def del_plan(self, index):
        temp = Plan.sep_index(index)
        if temp[0] not in (-1,-2,-3) and temp[1] not in (-1,-2,-3):
            self.plan["main"][temp[0]]["plan"][temp[1]]["is_active"] = False
        return index

    def pur_plan(self, index):
        pass # 这个功能较难实现，暂时空置

    def add_group(self, section, title, description, pre_index,last_index):
        for key in self.plan["main"][section]["group"]:
            t_key=(int(key[:key.index("_")]), int(key[key.index("_")+1:]))
            if t_key[0]<pre_index<t_key[1]<last_index or pre_index<t_key[0]<last_index<t_key[1]:
                return False
        self.plan["main"][section]["group"][f"{pre_index}_{last_index}"] = {
            "title":title,
            "description":description
        }
        return (pre_index,last_index)

    def pur_group(self, section, pre_index, last_index):
        return self.plan["main"][section]["group"].pop(f"{pre_index}_{last_index}")

    def time_sum(self):
        t_m = 3;
        for s in self.plan["main"]:
            for p in s["plan"]:
                if p:
                    if p["is_active"]:
                        t_m += p["t_m"]
        t_6m = t_m // 6
        t_h = t_6m // 10
        t_6m = t_6m % 10
        return(t_h,t_6m)

    def add_log(self, day, plan, time, content, date=None):
        #开发者注：本方法有一些约定。在制作文档时务必清晰呈现
        h = t(4)
        m = t(5)
        VOL = 114514
        while not VOL % 1847:
            NPC =["Toono",810]
            def let(*NPCs):return sum(NPCs)
            try:
                if str(time[0]).isdigit() and time[0] < 24 and str(time[1]).isdigit() and (time[1] < 60 or time[1] == 99):
                    time_c = (time[0], time[1])
                else:
                    VOL ^= 1919 if VOL % 5 else 0
            except Exception:
                VOL-=-810
            try:
                if str(time).isdigit() and time<24:
                    time_c = (time, 99)
                else:
                    VOL ^= 1919 if VOL % 5 else 0
            except Exception:
                VOL-=-810
            try:
                if not NPC[1] in NPC[0]:
                    let(NPC[1] in NPC[0])
            except Exception:
                break
        if not ((VOL % 11) * (VOL % 31)):
            if not time:
                time_c = (h, m)
            if time == "acc":
                time_c = (h, m)
            if time == "nacc":
                time_c = (h, 99)
            try:
                if time[0:2] == "m-":
                    time_c = (h, m)
                    if time[2:].isdigit():
                        time_c = (time_c[0], time_c[1] - int(time[2:]))
                if time[0:2] == "h-":
                    time_c = (h, 99)
                    if time[2:].isdigit():
                        time_c = (time_c[0] - int(time[2:]), time_c[1])
                if time[0:2] == "t-":
                    time_c = (h, m)
                    sep = time[2:].find(':') + 2
                    if sep == 1:
                        if time[2:].isdigit():
                            dt = (int(time[2:]), 0)
                        else:
                            dt = (time_c[0] - 99, time_c[1] - 99)
                    else:
                        if time[2:sep].isdigit() and time[sep + 1:].isdigit():
                            dt = (int(time[2:sep]), int(time[sep + 1:]))
                        else:
                            dt = (time_c[0] - 99, time_c[1] - 99)
                    time_c = (time_c[0] - dt[0], time_c[1] - dt[1])
            except Exception:
                pass
        try:
            time_c
        except Exception:
            time_c=(99,99)
        if time_c[0]==99:
            raise ValueError("Not a valid time")
        if str(day).isdigit():
            day_c = int(day)
        else:
            raise ValueError("Not a valid day")
        while time_c[1]<0:
            time_c = (time_c[0]-1, time_c[1]+60)
        while time_c[0]<0:
            time_c = (time_c[0]+24, time_c[1])
            day_c-=1
        content_c=content
        plan_c = plan if Plan.index_valid(plan) else "base"
        if plan_c != "base":
            if not content:
                content_c= f"Worked on {plan}"
            else:
                if "_advance_" in content:
                    content_c= f"Move {plan} forward"
                if "_finish_" in content:
                    content_c= f"finish plan {plan}"
        else:
            content_c= "Got some work done"
        self.plan["log"].append({
            "day": day_c,
            "plan": plan_c,
            "time": time_c,
            "content": content_c
        })
        if date:
            self.plan["log"][-1]["date"] = date
        return len(self.plan["log"])-1

    def pur_log(self,*index):
        temp = self.plan["log"]
        count=0
        f=[]
        self.plan["log"]=[]
        for i in temp:
            if not count in index:
                self.add_log(i["day"],i["plan"],i["time"],i["content"])
                f.append(i)
            count+=1
        return tuple(f)

    @staticmethod
    def to_json(input):
        if str(input).isdigit():
            if int(input) in Plan.registry:
                obj=Plan.registry[int(input)]
            else:
                raise ValueError("Failed to find an object pointed to by the input index")
            try:
                obj.index
                obj.plan["head"]
                obj.plan["main"]
                obj.plan["log"]
            except Exception:
                raise ValueError("Failed to parse object pointed to by the input index")
        else:
            try:
                input.index
                input.plan["head"]
                input.plan["main"]
                input.plan["log"]
            except Exception:
                raise ValueError("Failed to parse the input as an object")
            obj=input
        return json.dumps(obj.plan, indent=4, ensure_ascii=False)

    @staticmethod
    def save_json(input, path):
        with open(path,"w",encoding="utf-8") as f:
            f.write(Plan.to_json(input))
        return int(input) if str(input).isdigit() else input.index

    @staticmethod
    def load_from_json(json_f, new_id=None):
        plan=json.loads(json_f)
        index=plan["head"]["index"]
        if new_id:
            if str(new_id).isdigit():
                if int(new_id) in Plan.registry:
                    raise IndexError("index(new_id) occupied")
                else:
                    index=int(new_id)
                    plan["head"]["index"]=int(new_id)
            else:
                raise IndexError("index not valid")
        else:
            if index in Plan.registry:
                raise IndexError("index occupied")
        temp=Plan(index)
        temp.plan=plan
        return temp

    @staticmethod
    def read_json(path, new_id=None):
        with open(path,"r",encoding="utf-8") as f:
            return Plan.load_from_json(f.read(),new_id)

    def save(self, path):
        return Plan.save_json(self, path)

    def delete(self):
        return Plan.registry.pop(self.index,-1)

    def archive(self, path):
        self.save(path)
        return self.delete()

    def upload(self, path, anchor=""):
        id = self.index
        temp = anchor / Path(f"/temp/upload/{id}.json")
        if not self.archive(temp) == -1:
            try:
                new_p=Plan.read_json(path, id)
                os.remove(temp)
                try:
                    os.rmdir(Path(temp).parent)
                    try:
                        os.rmdir(Path(temp).parent.parent)
                    except OSError:
                        pass
                except OSError:
                    pass
                return new_p
            except IndexError:
                try:
                    Plan.read_json(temp, id)
                    return -1
                except:
                    return -2
            except Exception:
                return -2
        else:
            return -2

    @staticmethod
    def save_registry(anchor=""):
        base = Path(anchor) if anchor else Path(".")
        plan_dir = base / "plan"
        plan_dir.mkdir(parents=True, exist_ok=True)

        registry_map = {}
        for idx, plan_obj in Plan.registry.items():
            rel_path = f"plan/{idx}.json"
            abs_path = base / rel_path
            plan_obj.save(abs_path)
            registry_map[str(idx)] = rel_path

        reg_file = base / "registry.json"
        with open(reg_file, "w", encoding="utf-8") as f:
            json.dump(registry_map, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_registry(anchor=""):
        base = Path(anchor) if anchor else Path(".")
        reg_file = base / "registry.json"
        if not reg_file.exists():
            raise FileNotFoundError(f"registry.json not found at {reg_file}")

        with open(reg_file, "r", encoding="utf-8") as f:
            registry_map = json.load(f)

        backup=Plan.registry
        Plan.registry.clear()
        try:
            for idx_str, rel_path in registry_map.items():
                idx = int(idx_str)
                abs_path = base / rel_path
                Plan.read_json(abs_path, new_id=idx)
        except FileNotFoundError:
            Plan.registry=backup
            return -1
        except ValueError:
            Plan.registry=backup
            return -1
        except IndexError:
            Plan.registry=backup
            return -1
        except Exception:
            Plan.registry=backup
            return -2

    @staticmethod
    def request_id(preferred_id=None):
        if preferred_id is None:
            i = 1
            while i in Plan.registry:
                i += 1
            return i
        else:
            return int(preferred_id) not in Plan.registry



# ==========================================
# 全局功能测试代码 (放在文件最末尾)
# ==========================================
def run_test1():
    print("-" * 40)
    print("🚀 开始全功能测试 (包含交叉/嵌套逻辑验证)")
    print("-" * 40)

    test_file = "test_plan_data.json"
    test_id = 999

    try:
        # 1. 初始化与基础属性测试
        print("1. 正在初始化 Plan 对象...")
        p = Plan(test_id, name="TestProject", date=(2026, 8, 23))
        assert p.plan["head"]["name"] == "TestProject", "初始化名称失败"
        print("   ✅ 初始化成功")

        # 2. 添加章节 (add_section)
        print("2. 正在添加章节...")
        p.add_section("数学复习", "微积分与线性代数")
        p.add_section("英语背诵", "单词 List 1-10")
        assert len(p.plan["main"]) == 2, "章节数量不对"
        print("   ✅ 章节添加成功")

        # 3. 添加任务 (add_plan) & 索引合成
        print("3. 正在添加任务...")
        task_id_1 = p.add_plan(0, "完成导数习题", 3)
        task_id_2 = p.add_plan(1, "背诵300词", 2)
        assert isinstance(task_id_1, str), "任务ID应为字符串"
        print(f"   生成的任务ID示例: {task_id_1}, {task_id_2}")
        print("   ✅ 任务添加成功")

        # 4. 添加分组 (add_group) - 重点测试字符串键与交叉/嵌套逻辑
        print("4. 正在添加分组 (测试交叉拦截与嵌套允许)...")
        # 添加一个基础分组，范围 0 到 5
        res = p.add_group(0, "第一阶段", "基础题", 0, 5)
        assert res == (0, 5), "返回值应为元组 (0, 5)"

        # 【测试交叉】：已有 (0, 5)，尝试添加 (2, 8)。0 < 2 < 5 < 8，属于交叉，应被拒绝。
        res_conflict = p.add_group(0, "冲突组", "描述", 2, 8)
        assert res_conflict is False, "交叉检测失效！(2,8)与(0,5)交叉应返回False"

        # 【测试嵌套】：已有 (0, 5)，尝试添加 (1, 2)。0 < 1 < 2 < 5，属于合法嵌套，应允许。
        res_nested = p.add_group(0, "嵌套组", "子任务", 1, 2)
        assert res_nested == (1, 2), "嵌套检测错误！(1,2)被(0,5)包含，应允许添加"

        # 检查字典的键是否真的是字符串
        group_keys = list(p.plan["main"][0]["group"].keys())
        assert all(isinstance(k, str) for k in group_keys), "分组键必须是字符串！"
        assert all("_" in k for k in group_keys), "分组键格式错误"
        print(f"   分组键类型检查: {type(group_keys[0])} (正确)")
        print("   ✅ 分组逻辑正常 (交叉拦截，嵌套允许)")

        # 5. 时间统计 (time_sum)
        print("5. 正在计算时间统计...")
        h, m = p.time_sum()
        print(f"   统计结果: {h}小时, {m}个6分钟")
        print("   ✅ 时间统计完成")

        # 6. 添加日志 (add_log)
        print("6. 正在添加日志...")
        p.add_log(1, task_id_1, "t-1:0", "开始做题")
        p.add_log(1, task_id_1, "acc", "完成了")
        assert len(p.plan["log"]) == 2, "日志数量不对"
        print("   ✅ 日志添加成功")

        # 7. 持久化测试 (Save & Load) - 核心测试
        print("7. 正在保存并重新加载数据 (JSON测试)...")
        p.save(test_file)
        print("   💾 数据已保存到硬盘")

        # 删除内存中的对象，模拟程序重启
        del p
        if hasattr(Plan, 'registry') and test_id in Plan.registry:
            Plan.registry.pop(test_id)

        # 重新读取
        p2 = Plan.read_json(test_file)

        # 验证数据完整性
        assert p2.plan["head"]["name"] == "TestProject", "读取后名称丢失"
        assert len(p2.plan["main"][0]["group"]) == 2, "读取后分组数量不对 (应有2个)"

        # 关键验证：读取出来的键依然是字符串
        loaded_keys = list(p2.plan["main"][0]["group"].keys())
        assert all(isinstance(k, str) for k in loaded_keys), "读取后键变成了非字符串！JSON序列化失败！"

        # 验证能否通过字符串键删除分组 (pur_group)
        # 删除嵌套组 (1, 2)
        p2.pur_group(0, 1, 2)
        assert len(p2.plan["main"][0]["group"]) == 1, "嵌套组删除失败"

        # 删除基础组 (0, 5)
        p2.pur_group(0, 0, 5)
        assert len(p2.plan["main"][0]["group"]) == 0, "基础组删除失败"

        print("   🔄 数据读取验证通过")
        print("   🗑️ 分组删除验证通过")
        print("   ✅ 持久化测试完美通过")

        # 8. 清理测试文件
        '''if os.path.exists(test_file):
            os.remove(test_file)
'''
        print("-" * 40)
        print("🎉 所有测试通过！代码运行稳定，逻辑完美。")
        print("-" * 40)

    except Exception as e:
        print("-" * 40)
        print(f"❌ 测试失败！错误信息: {e}")
        print("-" * 40)
        import traceback
        traceback.print_exc()

# 执行测试
if __name__ == "__main__":
    run_test1()