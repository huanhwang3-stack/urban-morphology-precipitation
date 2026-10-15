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
plt.rc('legend', fontsize=18)
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

 
print("LWP",LWP)
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

label_large = {
    '2LCZ1': 'LCZ1 ',
    '3LCZ3': 'LCZ3 ',
    '4LCZ4': 'LCZ4 ',
    '5LCZ6': 'LCZ6 ',
    '6LCZ8': 'LCZ8 ',
}

label_small = {
    '2LCZ1S': 'LCZ1 (small)',
    '3LCZ3S': 'LCZ3 (small)',
    '4LCZ4S': 'LCZ4 (small)',
    '5LCZ6S': 'LCZ6 (small)',
    '6LCZ8S': 'LCZ8 (small)',
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

for c, b, x, y in zip(cases_large, base_large, x_large, y_large):
    ax.scatter(x, y, marker='^', s=140,
               color=color_large[c],
               label=label_large.get(c, c))

#for c, b, x, y in zip(cases_small, base_small, x_small, y_small):
   # ax.scatter(x, y, marker='o', s=110,
             #  facecolor=color_small[c],  # or color=
             #  edgecolor='k',
             #  label=label_small.get(c, c))

from scipy.stats import linregress

x_fit = np.array(x_large)
y_fit = np.array(y_large)

res = linregress(x_fit, y_fit)
m, b0 = res.slope, res.intercept
r2 = res.rvalue**2
p  = res.pvalue

# 打印到屏幕
print(rf"y = {m:.3f} x {b0:+.3f},  R^2 = {r2:.2f},  p = {p:.2e}")

# 画拟合线
xx = np.linspace(x_fit.min(), x_fit.max(), 200)
yy = m*xx + b0
ax.plot(xx, yy, color='k', linewidth=2)

# 在图上写公式（可选）
ax.text(0.2, 0.15,
        rf"$y={m:.3f}x{b0:+.3f}$"+"\n"+rf"$R^2={r2:.2f},\ p={p:.2e}$",
        transform=ax.transAxes, ha='left', va='top',
        fontsize=18, color='k')


 
 
ax.set_xlabel(r'$\int_{L_{CB}}^{L_z} \langle \overline{TKE} \rangle_{w,\mathrm{urban}}\,dz\ \left(kg\ s^{-2}\right)$')
ax.set_ylabel(
    r'$\langle \overline{LWP} \rangle_{\mathrm{urban}}'
    r'\ \left(\mathrm{g\,m^{-2}}\right)$'
)

# legend 去重
handles, labels = ax.get_legend_handles_labels()
uniq = dict(zip(labels, handles))
ax.legend(uniq.values(), uniq.keys(), fontsize=18, ncol=1, frameon=False)

plt.savefig('./2.png', dpi=300)
 

