signs = [" + ", " - "]

def EquationIntegrity(arr : list) -> bool:
    n = len(arr)
    if n == 0:
        return False
    
    if n == 1 and arr[0] in signs:
        return False
    
    if (arr[n-1] in signs):
        return False
    
    isPreviousSign = False
    for x in arr:
        if x in signs:
            if isPreviousSign:
                return False
            isPreviousSign = True
        else:
            isPreviousSign = False
    return True

signs = [" + ", " - "]

def Equal(arr : list) -> int:
    new_arr = []
    signage = []
    for x in arr:
        if (x in signs):
            if (x == " + "):
                signage.append(1)
            elif (x == " - "):
                signage.append(-1)
            new_arr.append("X")
        else:
            new_arr.append(x)
    text = "".join(map(str, new_arr))
    text = text.split("X")
    sum = 0
    if (len(text) != len(signage)):
        signage.insert(0,1)
    for i in range(len(text)):
        sum += int(text[i]) * signage[i]
    
    return sum
    
