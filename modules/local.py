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
    global location
    global fully_parsed
    location.clear()
    fully_parsed = False

def indexing(root,*indexes):
    global fully_parsed
    temp=root
    for index in indexes:
        temp=temp[index]
    return temp

def step(tree):
    global fully_parsed
    if fully_parsed:
        return -1

    global location
    depth=len(location)
    width=len(indexing(tree,location[:-1]))

