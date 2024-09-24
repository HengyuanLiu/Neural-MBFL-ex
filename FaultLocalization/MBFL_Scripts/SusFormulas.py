import math

def Ochiai(kf, kp, nf, np, f2p = None, p2f = None):
    tf = kf + nf
    tk = kf + kp
    if tf == 0 or tk == 0:
        return 0
    return kf / math.sqrt(tf * tk)

def Dstar(kf, kp, nf, np, f2p = None, p2f = None):
    if kp + nf == 0:
        return 0
    return (kf * kf) / (kp + nf)

def Gp13(kf, kp, nf, np, f2p = None, p2f = None):
    if (2 * kp + kf) == 0:
        return 0
    return kf + (kf / (2 * kp + kf))

def Jaccard(kf, kp, nf, np, f2p = None, p2f = None):
    if (kf + nf + kp == 0):
        return 0
    return kf / (kf + nf + kp)

def Tarantula(kf, kp, nf, np, f2p = None, p2f = None):
    if kf + kp == 0 or kf + nf == 0:
        return 0
    if kf + nf != 0 and kp + np == 0:
        return 1
    return (kf / (kf + nf)) / ((kf / (kf + nf)) + (kp / (kp + np)))

def Op2(kf, kp, nf, np, f2p = None, p2f = None):
    return kf - kp / (kp + np + 1)

def Muse(kf, kp, nf, np, f2p, p2f):
    if kf + nf == 0:
        return 0
    if p2f != 0:
        alpha = f2p / (kf + nf) * (kp + np) / p2f
        return kf / (kf + nf) - alpha * kp / (kp + np)
    else:
        return kf / (kf + nf)

F_Sus = {
    "Ochiai": Ochiai,
    "Dstar": Dstar,
    "Gp13": Gp13,
    "Jaccard": Jaccard,
    "Tarantula": Tarantula,
    "Op2": Op2,
    "Muse": Muse
}

if __name__ == "__main__":

    result = F_Sus["Op2"](10, 5, 3, 2, 3, 3)
    print("Result of Op2:", result)
    
    result = F_Sus["Muse"](10, 5, 3, 2, 3, 3)
    print("Result of Muse:", result)

