"""合成十五种宠物的叫声（纯 Python，无第三方依赖）。

不是真实录音，是按各种动物叫声的特点用"谐波 + 共振峰"合成的萌系音效：
  小猫  喵：音高先升后降，元音从 i 滑到 a 再到 o
  小狗  汪汪：两声短促的低音，元音从 u 张到 a
  豚鼠  吱吱：三声高音上滑的尖叫（wheek）
  蜜袋鼯 啾啾：一串很快的高频小啁啾
  小蛇  嘶：一口柔和的气声，带一点点"啵"
  蜥蜴  咯咯：守宫那种短促的咔嗒声

运行：python make_cries.py
输出：android/app/src/main/res/raw/cry_<宠物>.wav（22050Hz 单声道 16 位）
"""
import math
import os
import random
import struct
import wave

SR = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'res', 'raw')
random.seed(7)

# 元音共振峰（F1, F2, F3）
VOWELS = {
    'i': (300, 2300, 3000), 'a': (800, 1300, 2600), 'o': (500, 900, 2500),
    'u': (350, 800, 2300), 'e': (500, 1900, 2600),
}


def lerp(a, b, t):
    return a + (b - a) * t


def formants_at(path, t):
    """path: [(时间比例, 元音), ...]，在相邻元音之间插值"""
    for (t0, v0), (t1, v1) in zip(path, path[1:]):
        if t <= t1:
            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(lerp(a, b, k) for a, b in zip(VOWELS[v0], VOWELS[v1]))
    return VOWELS[path[-1][1]]


def voice(dur, f0_fn, vowel_path, env_fn, bw=(90, 120, 160), breath=0.0, vibrato=(0, 0)):
    """谐波合成：每个谐波按共振峰增益加权，听起来像元音"""
    n = int(SR * dur)
    out = [0.0] * n
    phase = 0.0
    harm_phase = [0.0] * 40
    for i in range(n):
        t = i / n
        f0 = f0_fn(t) * (1 + vibrato[1] * math.sin(2 * math.pi * vibrato[0] * i / SR))
        fs = formants_at(vowel_path, t)
        s = 0.0
        for k in range(1, 40):
            fk = f0 * k
            if fk > SR / 2 - 500:
                break
            g = 0.0
            for f, b in zip(fs, bw):
                g += math.exp(-((fk - f) / b) ** 2 / 2)
            g = g / (k ** 0.3)
            harm_phase[k] += 2 * math.pi * fk / SR
            s += g * math.sin(harm_phase[k])
        if breath:
            s += breath * (random.random() * 2 - 1)
        out[i] = s * env_fn(t)
    return out


def env_adsr(a=0.05, r=0.35):
    def f(t):
        if t < a:
            return t / a
        if t > 1 - r:
            return max(0.0, (1 - t) / r)
        return 1.0
    return f


def silence(sec):
    return [0.0] * int(SR * sec)


def noise_band(dur, lo, hi, env_fn):
    """带通噪声（简单的一阶高通 + 低通组合）"""
    n = int(SR * dur)
    out = []
    lp = hp_prev_in = hp_prev_out = 0.0
    a_lp = math.exp(-2 * math.pi * hi / SR)
    a_hp = math.exp(-2 * math.pi * lo / SR)
    for i in range(n):
        x = random.random() * 2 - 1
        lp = (1 - a_lp) * x + a_lp * lp
        hp = a_hp * (hp_prev_out + lp - hp_prev_in)
        hp_prev_in, hp_prev_out = lp, hp
        out.append(hp * env_fn(i / n))
    return out


def tone(dur, f_fn, env_fn, harmonics=((1, 1.0), (2, 0.35), (3, 0.15))):
    n = int(SR * dur)
    out = []
    ph = 0.0
    for i in range(n):
        t = i / n
        ph += 2 * math.pi * f_fn(t) / SR
        out.append(sum(a * math.sin(ph * h) for h, a in harmonics) * env_fn(t))
    return out


def mix_add(a, b, offset=0):
    n = max(len(a), offset + len(b))
    out = a + [0.0] * (n - len(a))
    for i, v in enumerate(b):
        out[offset + i] += v
    return out


def save(name, samples, peak=0.95):
    m = max(abs(v) for v in samples) or 1
    k = peak / m
    # 结尾 15ms 淡出，避免爆音
    fade = int(SR * 0.015)
    data = bytearray()
    for i, v in enumerate(samples):
        if i > len(samples) - fade:
            v *= (len(samples) - i) / fade
        data += struct.pack('<h', int(max(-1, min(1, v * k)) * 32767))
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, f'cry_{name}.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(bytes(data))
    print(name, f'{len(samples) / SR:.2f}s')


def cat():
    # 喵：0.62 秒，音高 560→880→620，元音 i→a→o，开头有一点鼻音 m
    f0 = lambda t: 560 + 320 * math.sin(math.pi * min(1, t * 1.25)) if t < 0.8 else lerp(700, 600, (t - 0.8) / 0.2)
    s = voice(0.62, f0, [(0, 'u'), (0.12, 'i'), (0.45, 'a'), (1.0, 'o')], env_adsr(0.08, 0.4),
              bw=(110, 160, 200), breath=0.02, vibrato=(6, 0.012))
    return s


def dog():
    # 汪汪：两声，每声 0.18 秒，音高 420→300，元音 u→a
    one = lambda p: voice(0.18, lambda t: lerp(430 * p, 300 * p, t), [(0, 'u'), (0.3, 'a'), (1, 'o')],
                          env_adsr(0.02, 0.5), bw=(140, 200, 260), breath=0.06)
    return one(1.0) + silence(0.09) + one(1.08)


def guinea_pig():
    # 吱吱吱：三声 wheek，每声 0.16 秒，1300→2100Hz 上滑
    out = []
    for k, p in enumerate((1.0, 1.06, 1.12)):
        out += tone(0.16, lambda t, p=p: lerp(1300, 2100, t ** 0.7) * p, env_adsr(0.03, 0.3),
                    harmonics=((1, 1.0), (2, 0.25)))
        out += silence(0.06)
    return out


def sugar_glider():
    # 啾啾啾啾：四个很快的小啁啾，2800→3600Hz
    out = []
    for p in (1.0, 1.05, 0.98, 1.1):
        out += tone(0.055, lambda t, p=p: lerp(2800, 3600, t) * p, env_adsr(0.15, 0.5),
                    harmonics=((1, 1.0), (2, 0.15)))
        out += silence(0.045)
    return out


def snake():
    # 嘶：0.55 秒柔和的气声（3k–7kHz 噪声），前面加一个小"啵"让它不那么凶
    pop = tone(0.05, lambda t: lerp(900, 500, t), env_adsr(0.1, 0.6))
    hiss = noise_band(0.55, 3000, 7500, lambda t: (min(1, t / 0.12)) * (1 - t) ** 1.4)
    return mix_add([v * 0.5 for v in pop] + silence(0.03), hiss, offset=int(SR * 0.05))


def lizard():
    # 咯咯咯：守宫的短促咔嗒，三声，每声是很短的 1800Hz 衰减音 + 一点噪声
    out = []
    for p in (1.0, 0.94, 1.04):
        click = tone(0.045, lambda t, p=p: 1800 * p * (1 - 0.3 * t),
                     lambda t: math.exp(-t * 7), harmonics=((1, 1.0), (2, 0.5), (3, 0.3)))
        nz = noise_band(0.02, 1500, 5000, lambda t: math.exp(-t * 6))
        out += mix_add(click, [v * 0.6 for v in nz]) + silence(0.07)
    return out


# ---------------- 第二批（0.3.1）

def chinchilla():
    # 龙猫：两声软软的"叽"，1500→1950Hz，带一点气声
    out = []
    for p in (1.0, 1.08):
        out += tone(0.09, lambda t, p=p: lerp(1500, 1950, t) * p, env_adsr(0.1, 0.45), harmonics=((1, 1.0), (2, 0.3)))
        out += silence(0.05)
    return out


def hamster():
    # 仓鼠：三声又细又短的"吱"，2400Hz 上下
    out = []
    for p in (1.0, 1.1, 0.95):
        out += tone(0.05, lambda t, p=p: lerp(2300, 2700, t) * p, env_adsr(0.15, 0.5), harmonics=((1, 1.0), (2, 0.2)))
        out += silence(0.04)
    return out


def turtle():
    # 乌龟基本不叫：缩头时"噗"地喷一小口气，低沉的一声 + 气声
    puff = noise_band(0.25, 300, 1800, lambda t: min(1, t / 0.08) * (1 - t) ** 2)
    low = tone(0.18, lambda t: lerp(220, 160, t), lambda t: math.exp(-t * 4))
    return mix_add([v * 0.5 for v in low], puff)


def bunny():
    # 兔子：后腿"咚咚"跺两下地，再一声小鼻子哼
    def thump():
        return mix_add(tone(0.09, lambda t: lerp(130, 70, t), lambda t: math.exp(-t * 9)),
                       [v * 0.4 for v in noise_band(0.04, 100, 900, lambda t: math.exp(-t * 8))])
    sniff = noise_band(0.12, 2000, 6000, lambda t: math.sin(math.pi * t) ** 2)
    return thump() + silence(0.08) + thump() + silence(0.1) + [v * 0.35 for v in sniff]


def clownfish():
    # 小丑鱼：咕嘟咕嘟三个泡泡，每个是快速上滑的"啵"
    out = []
    for p in (1.0, 1.2, 0.9):
        out += tone(0.07, lambda t, p=p: lerp(380, 950, t ** 0.6) * p, lambda t: math.sin(math.pi * t) * math.exp(-t * 2),
                    harmonics=((1, 1.0), (2, 0.15)))
        out += silence(0.05)
    return out


def hedgehog():
    # 刺猬：一串"呼哧呼哧"的小鼻息
    out = []
    for k in range(4):
        out += noise_band(0.07, 900, 3500, lambda t: math.sin(math.pi * t) ** 1.5) + silence(0.035)
    return out


def swan():
    # 天鹅："嗷——"一声带鼻音的号叫，500→420Hz，元音 a→o
    return voice(0.38, lambda t: lerp(500, 420, t), [(0, 'e'), (0.25, 'a'), (1, 'o')], env_adsr(0.06, 0.4),
                 bw=(120, 180, 240), breath=0.04, vibrato=(9, 0.02))


def pig():
    # 小香猪：哼哼两声，低沉、带鼻音和气声
    one = lambda p: voice(0.16, lambda t: lerp(260 * p, 200 * p, t), [(0, 'u'), (0.5, 'o'), (1, 'u')],
                          env_adsr(0.05, 0.45), bw=(90, 130, 180), breath=0.12, vibrato=(28, 0.05))
    return one(1.0) + silence(0.06) + one(1.1)


def tarantula():
    # 毒蛛不会叫：腿上的刚毛互相摩擦，发出一串细碎的"沙沙"声
    out = []
    for k in range(7):
        out += noise_band(0.018, 4000, 9000, lambda t: math.exp(-t * 5)) + silence(0.022)
    return out


if __name__ == '__main__':
    save('cat', cat())
    save('dog', dog())
    save('guinea_pig', guinea_pig())
    save('sugar_glider', sugar_glider())
    save('snake', snake(), peak=0.8)
    save('lizard', lizard())
    for name in ('chinchilla', 'hamster', 'turtle', 'bunny', 'clownfish', 'hedgehog', 'swan', 'pig', 'tarantula'):
        save(name, globals()[name](), peak=0.8 if name in ('turtle', 'tarantula', 'hedgehog') else 0.95)
