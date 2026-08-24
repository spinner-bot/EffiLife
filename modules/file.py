"""
    ====== modules/file.py ======
    No description.
        by spinner-bot
"""

TREE = \
    [
        "..",
        [
            "plan",
            [
                "stars",
            ],
            [
                "test",
            ],
        ],
        [
            "data",
            [
                "system",
                [
                    "registry"
                ],
                [
                    "users"
                ],
                [
                    "settings"
                ],
            ],
            [
                "LLM",
                [
                    "prompt",
                    [
                        "sys_prompt",
                    ],
                    [
                        "user_prompt"
                    ]
                ],
                [
                    "knowledge_base",
                    [
                        "product",
                    ],
                    [
                        "oth"
                    ]
                ]
            ]
        ],
        [
            "temp",
            [
                "test"
            ]
        ]
    ]

from pathlib import Path

location = []
fully_parsed = False


def reset():
    global fully_parsed
    location.clear()
    fully_parsed = False


def indexing(root, *indexes):
    temp = root
    for index in indexes:
        for index2 in index:
            temp = temp[index2]
    return temp


def step(tree, branch_parsed=False):
    global fully_parsed
    if fully_parsed:
        return -1

    global location
    if not len(indexing(tree, location)) or not tree or not len(tree) - 1:
        # 情况0：数据无法解析
        reset()
        return -1
    else:
        if len(indexing(tree, location)) - 1 and not branch_parsed:
            # 情况1：地址访问可行
            location.append(1)
            return 0
        else:
            if location:
                if not location[-1] == len(indexing(tree, location[:-1])) - 1:
                    # 情况2：地址扫描可行
                    location[-1] += 1
                    return 0
                else:
                    # 情况3：分支解析完全
                    location.pop(-1)
                    return step(tree, True)
            else:
                # 情况4：数据解析完全
                reset()
                fully_parsed = True
                return 0


def convert(tree):
    path = []
    for depth in range(len(location) + 1):
        path.append(indexing(tree, location[:depth])[0])
    return Path(*path)


def scan(tree):
    global fully_parsed
    if fully_parsed:
        return -1

    if not step(tree):
        return convert(tree) if not fully_parsed else 0
    else:
        return -1


def parse(tree):
    global fully_parsed
    paths = set()
    while not fully_parsed:
        temp = scan(tree)
        if temp != 0 and temp != -1:
            paths.add(temp)
    return paths


def build(tree, anchor=""):
    status = {}
    for path in parse(tree):
        try:
            Path(anchor).joinpath(path).mkdir(parents=True)
            status[path] = (0,)
        except FileExistsError:
            status[path] = (1,)
        except Exception as e:
            status[path] = (2,type(e).__name__,str(e))
    return status

def report(info):
    lines=["","====== 文件系统初始化 ======",""]
    status = [0,0,0]
    err={}
    for key, value in info.items():
        status[value[0]] += 1
        if not value[0]-2:
            if not value[1] in err:
                err[value[1]] = [0,{}]
            err[value[1]][0] += 1
            err[value[1]][1][key] = value[2]
    lines.append(f"初始化结论：{f"success({sum(status)} path{"s" if sum(status)-1 else ""})" if not status[2] else f"{status[2]}/{sum(status)} failed"}")
    for i in range(2):
        if status[i]:
            p=(1000*status[i]+0.5*sum(status))//sum(status)
            lines.append(f"    [{["Created", "Existing", "Failed"][i]}] {status[i]}/{sum(status)} {int(p//10)}.{int(p%10)}%")
    lines.append("")
    if err:
        lines.append("【错误信息】")
        #n=0
        for key, value in err.items():
            #n+=1
            lines.append(f"[{key}]")
            m=0
            for k,v in value[1]:
                m+=1
                lines.append(f"{m}.{k}")
                lines.append(f"    {v}")
        lines.append("")
    r=""
    for l in lines:
        r+=l+"\n"
    return r

if __name__ == "__main__":
    print(build(TREE))