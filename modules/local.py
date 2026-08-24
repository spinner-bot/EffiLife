"""
    ====== modules/local.py ======
    No description.
        by spinner-bot
"""

from pathlib import Path

TREE=\
[
    "..",
    [
        "plan",
        [
            "star",
        ],
        [
            "test",
        ],
    ],
    [
        "data",
        [
            "registry"
        ]
    ],
    [
        "temp",
        [
            "test",
        ]
    ]
]

#plan_dir.mkdir(parents=True, exist_ok=True)

location=[]
fully_parsed=False

def reset():
    global fully_parsed
    location.clear()
    fully_parsed = False

def indexing(root,*indexes):
    temp=root
    for index in indexes:
        temp=temp[index]
    return temp

def step(tree,branch_parsed=False):
    global fully_parsed
    if fully_parsed:
        return -1

    global location
    if not len(indexing(tree,location)):
        # 情况0：数据无法解析
        reset()
        return -1
    else:
        if not len(indexing(tree,location))-1 and not branch_parsed:
            # 情况1：地址访问可行
            location.append(1)
            return 0
        else:
            if location[-1]==len(indexing(tree,location[:-1]))-1:
                # 情况2：地址扫描可行
                location[-1]+=1
                return 0
            else:
                if location:
                    # 情况3：分支解析完全
                    location.pop(-1)
                    return step(tree,True)
                else:
                    # 情况4：数据解析完全
                    reset()
                    fully_parsed=True
                    return 0