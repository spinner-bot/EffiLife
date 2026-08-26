def get_level(score):
    temp=score%101+score//101 if score//101 else (109-score)//10+64
    if temp<65:
        return get_level(temp+101)
    elif temp>69:
        return get_level(temp-101)
    else:
        return chr(temp)

for i in range(101):
    print(i, get_level(i), end="\n" if not i%10 else "  ")