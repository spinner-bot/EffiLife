"""
    ============ plan-helper ============
    [repository] https://github.com/spinner-bot/plan-helper
    [description] 暂时还没写……
        by spinner-bot
"""

import modules as m

if __name__ == "__main__":
    #print(m.f.report(m.f.build(m.f.TREE,"modules")))
    #print(m.pp.report_tp())
    # m.test.t(int(input("请输入测试号：")))

    sys1=m.pp.PLAN_PROMPT["prompt"]
    ass1=[{"role": "assistant", "content": "你好！我是你的计划定制助手，负责协助您定制个性化计划。请告诉我你的需求吧！"},]
    print("[message from model] 你好！我是你的计划定制助手，负责协助您定制个性化计划。请告诉我你的需求吧！")
    m.chat.chat_loop(history=ass1, sys_prompt=sys1, model="qwen3.5:2b", stream=True)