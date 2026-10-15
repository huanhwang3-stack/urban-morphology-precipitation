import os, re, glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from numpy import nanmean

# -----------------------
#  Plot style (LaTeX)
# -----------------------
font = {'family': 'serif', 'size': 24}
matplotlib.rc('font', **font)
plt.rc('legend', fontsize=24)
plt.rc('legend', frameon=False)
plt.rc('text', usetex=True)

# -----------------------
#  helper: safe mean
# -----------------------
def av(arr, axis=None):
    arr = np.isfinite(arr) * arr
    temp_arr = nanmean(arr, axis=axis)
    temp_arr = np.isfinite(temp_arr) * temp_arr
    return temp_arr

# -----------------------
#  user settings
# -----------------------
location1 = 'urban'  #'urban'   LWP
location2 = 'urban' #'urban'  'down' 'urbanin' 'urbanall'
dir_lwp = "1npy"
dir_w2  = "6npy"

size_large = "105fig3large"
size_small = "105fig3small"

#cases_large = ['1LCZ0','2LCZ1','3LCZ3','4LCZ4','5LCZ6','6LCZ8']
#cases_small = ['1LCZ0S','2LCZ1S','3LCZ3S','4LCZ4S','5LCZ6S','6LCZ8S','2LCZ1SU0','2LCZ1SU5']

cases_large = [ '2LCZ1','3LCZ3','4LCZ4','5LCZ6','6LCZ8']
cases_small = [ '2LCZ1S','3LCZ3S','4LCZ4S','5LCZ6S','6LCZ8S']

 

# -----------------------
#  loader functions
# -----------------------
def load_case(size_folder, subfolder, case, location):
    fpath = f"../{size_folder}/{subfolder}/{case}{location}.npy"
    if not os.path.exists(fpath):
        raise FileNotFoundError(f"Missing file: {fpath}")
    return np.load(fpath).astype(float)

def load_series(size_folder, subfolder, cases, location):
    return [load_case(size_folder, subfolder, c, location) for c in cases]

# -----------------------
#  load data
# -----------------------
LWP  = load_series(size_large, dir_lwp, cases_large, location1)
W    = load_series(size_large, dir_w2,  cases_large, location2)

LWPS = load_series(size_small, dir_lwp, cases_small, location1)
WS   = load_series(size_small, dir_w2,  cases_small, location2)

 

# -----------------------
#  reduce each case to scalar
# -----------------------
x_large = [np.nanmean(a) for a in  W]  ##x is not LWP is w
y_large = [np.nanmean(a) for a in LWP]

x_small = [np.nanmean(a) for a in  WS]
y_small = [np.nanmean(a) for a in LWPS]

# -----------------------
#  make base-case names for coloring
#    e.g. 2LCZ1S / 2LCZ1SU0 / 2LCZ1SU5 -> 2LCZ1
# -----------------------
def base_case(name):
    return re.sub(r'(SU0|SU5|S)$', '', name)

base_large = [base_case(c) for c in cases_large]
base_small = [base_case(c) for c in cases_small]

# unique base cases (for consistent colors)
base_all = list(dict.fromkeys(base_large + base_small))  # keep order

import matplotlib.cm as cm
cmap = cm.get_cmap('tab10', len(base_all))
base2color = {b: cmap(i) for i, b in enumerate(base_all)}

# -----------------------
#  scatter plot
# -----------------------
fig, ax = plt.subplots(figsize=(7.3,5.5))
plt.subplots_adjust(left=0.14, bottom=0.18, right=0.95, top=0.95)

lamda_large = {
    '2LCZ1': 0.444,
    '3LCZ3': 0.444,
    '4LCZ4': 0.198,
    '5LCZ6': 0.198,
    '6LCZ8': 0.346,
}

lamda_small = {
    '2LCZ1S': 0.444,
    '3LCZ3S': 0.444,
    '4LCZ4S': 0.198,
    '5LCZ6S': 0.198,
    '6LCZ8S': 0.346,
}

h_large = {
    '2LCZ1': 200,
    '3LCZ3': 50,
    '4LCZ4': 100,
    '5LCZ6': 30,
    '6LCZ8': 30,
}

h_small = {
    '2LCZ1S': 200,
    '3LCZ3S': 50,
    '4LCZ4S': 100,
    '5LCZ6S': 30,
    '6LCZ8S': 30,
}



label_large = {
    '2LCZ1': 'LCZ1',
    '3LCZ3': 'LCZ3',
    '4LCZ4': 'LCZ4',
    '5LCZ6': 'LCZ6',
    '6LCZ8': 'LCZ8',
}

label_small = {
    '2LCZ1S': 'LCZ1',
    '3LCZ3S': 'LCZ3',
    '4LCZ4S': 'LCZ4',
    '5LCZ6S': 'LCZ6',
    '6LCZ8S': 'LCZ8',
}

color_large = {
    '2LCZ1': 'red',
    '3LCZ3': 'orange',
    '4LCZ4': 'limegreen',
    '5LCZ6': 'dodgerblue',
    '6LCZ8': 'purple',
}

color_small = {
    '2LCZ1S': 'red',
    '3LCZ3S': 'orange',
    '4LCZ4S': 'limegreen',
    '5LCZ6S': 'dodgerblue',
    '6LCZ8S': 'purple',
}

# -----------------------
#  取出 h, lamda, LWP (mean) 数值
# -----------------------
# LWP 的均值（你上面已经算过 y_large, y_small）
lwp_large_mean = {c: y for c, y in zip(cases_large, y_large)}
lwp_small_mean = {c: y for c, y in zip(cases_small, y_small)}

# x=h, y=lamda, color=LWP
xL = np.array([h_large[c] for c in cases_large])
yL = np.array([lamda_large[c] for c in cases_large])
cL = np.array([lwp_large_mean[c] for c in cases_large])

xS = np.array([h_small[c] for c in cases_small])
yS = np.array([lamda_small[c] for c in cases_small])
cS = np.array([lwp_small_mean[c] for c in cases_small])

# -----------------------
#  scatter plot: color by LWP
# -----------------------
fig, ax = plt.subplots(figsize=(7.0,5.5))
plt.subplots_adjust(left=0.15, bottom=0.15, right=0.96, top=0.95)

# 统一 color scale（保证 large/small 共用同一套颜色范围）
c_all = np.concatenate([cL, cS])
vmin, vmax = np.nanmin(c_all), np.nanmax(c_all)

scL = ax.scatter(xL, yL, marker='^', s=160, c=cL,
                 cmap='Blues', vmin=2.5, vmax=6,
                 edgecolor='k', linewidth=0.5, label='large')

#scS = ax.scatter(xS, yS, marker='o', s=130, c=cS,
             #    cmap='turbo', vmin=vmin, vmax=vmax,
              #   edgecolor='k', linewidth=0.5, label='small')

# -----------------------
#  text labels (像你图里那样标 LCZ)
# -----------------------
 
for c in cases_large:
    ax.text(
        h_large[c] -13,
        lamda_large[c] + 0.007,
        label_large.get(c, c),   # 用你自定义的 label
        fontsize=23
    )


#for c in cases_small:
    #ax.text(h_small[c]+3, lamda_small[c]+0.005, base_case(c), fontsize=14)

# -----------------------
#  axes labels
# -----------------------
ax.set_xlabel(r'$h\ (m)$')
ax.set_ylabel(r'$\lambda_p$')

# colorbar（颜色= LWP）
cbar = plt.colorbar(scL, ax=ax, pad=0.021)
cbar.set_label(r'$\langle \overline{\mathrm{LWP}} \rangle_{\mathrm{urban}}\ (g\ m^{-2})$')

# 如果你还想保留 large/small 的图例：
#ax.legend(fontsize=12, frameon=False)

plt.savefig('2.png', dpi=300)
 


