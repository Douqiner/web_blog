def strTToHtml(strT):
    hr = 0

    H = 0
    # 判断分割线
    hr = 1
    if (len(strT) < 3):
        hr = 0
    else:
        for ch in strT:
            if (ch != '-'):
                hr = 0
    if (hr):
        return "<hr>"
    # 判断H
    if (strT[0:2] == "# "):
        H = 1
    elif (strT[0:3] == "## "):
        H = 2
    elif (strT[0:4] == "### "):
        H = 3
    elif (strT[0:5] == "#### "):
        H = 4
    elif (strT[0:6] == "##### "):
        H = 5
    elif (strT[0:7] == "###### "):
        H = 6
    if (H > 0):
        strT = strT[H + 1: len(strT)]

    # 字体
    t = strT.count("**")
    if (t % 2 == 1):
        t -= 1
    for i in range(0, t):
        p = strT.find("**")
        if (i % 2 == 0):
            strT = strT[0:p] + "<strong>" + strT[p + 2:len(strT)]
        else:
            strT = strT[0:p] + "</strong>" + strT[p + 2:len(strT)]
    t = strT.count("~~")
    if (t % 2 == 1):
        t -= 1
    for i in range(0, t):
        p = strT.find("~~")
        if (i % 2 == 0):
            strT = strT[0:p] + "<s>" + strT[p + 2:len(strT)]
        else:
            strT = strT[0:p] + "</s>" + strT[p + 2:len(strT)]
    t = strT.count("__")
    if (t % 2 == 1):
        t -= 1
    for i in range(0, t):
        p = strT.find("__")
        if (i % 2 == 0):
            strT = strT[0:p] + "<em>" + strT[p + 2:len(strT)]
        else:
            strT = strT[0:p] + "</em>" + strT[p + 2:len(strT)]

    # 链接 图片
    while (1):
        posmid = strT.find("](")
        if (posmid == -1):
            break
        posfro = strT.rfind("[", 0, posmid)
        if (posfro == -1):
            break
        posbak = strT.find(")", posmid, len(strT))
        if (posbak == -1):
            break
        name = strT[posfro + 1:posmid]
        link = strT[posmid + 2:posbak]
        # 为什么没用
        if (posfro == 0 or strT[posfro - 1] != '!'):  # 链接
            strT = strT[0:posfro] + "<a href=\"" + link + "\" target=\"_blank\">" + name + "</a>" + strT[posbak + 1:len(strT)]
            # strT.replace("["+name+"]("+link+")", "<a href=\""+link+"\">"+name+"</a>")
        else:
            strT = strT[0:posfro - 1] + "<img src=\"" + link + "\" alt=\"" + name + "\">" + strT[posbak + 1:len(strT)]
            # strT.replace("!["+name+"]("+link+")", "<img hrc=\""+link+"\" alt=\""+name+"\">")

    ansstrT = ""
    if (H == 0):
        ansstrT = "<p>" + strT + "</p>"
    else:
        ansstrT = "<h" + str(H) + ">" + strT + "</h" + str(H) + ">"
    return ansstrT

