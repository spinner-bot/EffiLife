def get_level(score):
    temp=-1 if score//101 else (109-score)//10+64
    if temp<65:
        return get_level(106+temp)
    elif temp>69:
        pass
    else:
        return chr(temp)

for i in range(101):
    print(i, get_level(i), end="\n" if not i%10 else "  ")