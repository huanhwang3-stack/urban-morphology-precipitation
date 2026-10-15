import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# ===== plot设置 =====
font = {'family': 'serif', 'size': 18}
matplotlib.rc('font', **font)
plt.rc('text', usetex=True)

# ===== 读取数据 =====
LCZ1 = np.load("./0npy/LCZ1.npy")
LCZ3 = np.load("./0npy/LCZ3.npy")
LCZ4 = np.load("./0npy/LCZ4.npy")
LCZ6 = np.load("./0npy/LCZ6.npy")
LCZ8 = np.load("./0npy/LCZ8.npy")

# ===== 构造 x =====
nx = len(LCZ1)
x = np.linspace(0, 15000, nx)

# ===== 城市位置 =====
x_upwind = 3990
x_downwind = 6510

# ===== 函数 =====

def get_LWP_peak(profile):
    # 平滑避免噪声
    window = 15
    smooth = np.convolve(profile, np.ones(window)/window, mode='same')
    return np.max(smooth)


def get_LWP_mean(profile, x, x1, x2):
    mask = (x >= x1) & (x <= x2)
    return np.nanmean(profile[mask])


# ===== 计算指标 =====

def compute_metrics(profile):
    peak = get_LWP_peak(profile)
    urban = get_LWP_mean(profile, x, x_upwind, x_downwind)
    down  = get_LWP_mean(profile, x, x_downwind, x[-1])
    return peak, urban, down


peak1, urban1, down1 = compute_metrics(LCZ1)
peak3, urban3, down3 = compute_metrics(LCZ3)
peak4, urban4, down4 = compute_metrics(LCZ4)
peak6, urban6, down6 = compute_metrics(LCZ6)
peak8, urban8, down8 = compute_metrics(LCZ8)


# ===== 整理数据 =====

labels = ['LCZ1', 'LCZ3', 'LCZ4', 'LCZ6', 'LCZ8']

peak_vals  = [peak1, peak3, peak4, peak6, peak8]
urban_vals = [urban1, urban3, urban4, urban6, urban8]
down_vals  = [down1, down3, down4, down6, down8]


# ============================================================
# Macaron colors
# ============================================================

macaron_pink  = '#E64B35'   # pastel pink
macaron_blue  = '#4DBBD5'   # pastel blue
macaron_green = '#00A087'   # pastel green


# ===== 画图 =====

fig, ax = plt.subplots(figsize=(7, 5))

plt.subplots_adjust(
    left=0.14,
    right=0.94,
    bottom=0.14,
    top=0.98
)


x_pos = np.arange(len(labels))
width = 0.25


# Peak
ax.bar(
    x_pos - width,
    peak_vals,
    width,
    color=macaron_pink,
    label='Peak'
)

# Urban
ax.bar(
    x_pos,
    urban_vals,
    width,
    color=macaron_blue,
    label='Urban'
)

# Downwind
ax.bar(
    x_pos + width,
    down_vals,
    width,
    color=macaron_green,
    label='Down'
)


# ===== 坐标 =====

ax.set_xticks(x_pos)
ax.set_xticklabels(labels)

ax.set_ylabel(
    r'$\overline{LWP}\ \mathrm{(g\,m^{-2})}$',
    fontsize=18
)

ax.set_xlabel(
    'LCZ type',
    fontsize=18
)

ax.set_ylim(0, 110)


# ===== legend =====

ax.legend(
    [
        r'$\langle \overline{LWP}\rangle_{\mathrm{peak}}$',
        r'$\langle \overline{LWP}\rangle_{\mathrm{urban}}$',
        r'$\langle \overline{LWP}\rangle_{\mathrm{downwind}}$'
    ],
    bbox_to_anchor=(0.32, 0.62)
)


# ===== 保存 =====

plt.savefig(
    './2LWPpeak.png',
    dpi=300,
    bbox_inches='tight'
)

 
