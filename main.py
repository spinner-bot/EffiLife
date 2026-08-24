"""
    ============ plan-helper ============
    [repository] https://github.com/spinner-bot/plan-helper
    [description] 暂时还没写……
        by spinner-bot
"""

import modules as m

if __name__ == "__main__":
    print(m.f.report(m.f.build(m.f.TREE,"modules")))
    print(m.pp.report_tp())
    # m.test.t(int(input("请输入测试号：")))
    m.chat.chat_loop("qwen3.5:2b")