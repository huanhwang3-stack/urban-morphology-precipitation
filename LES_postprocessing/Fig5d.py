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
location1 = 'down'  #'urban'   LWP
location2 = 'urban' #'urban'  'down' 'urbanin' 'urbanall'
location3 = 'down' #'urban'  'down' 'urbanin' 'urbanall'
dir_lwp = "1npy"
dir_w2  = "6npy"

size_large = "105fig3large"
 
cases_large = [ '2LCZ1','3LCZ3','4LCZ4','5LCZ6','6LCZ8']
 
label_large = {
    '2LCZ1': 'LCZ1',
    '3LCZ3': 'LCZ3',
    '4LCZ4': 'LCZ4',
    '5LCZ6': 'LCZ6',
    '6LCZ8': 'LCZ8',
}

color_large = {
    '2LCZ1': 'red',
    '3LCZ3': 'orange',
    '4LCZ4': 'limegreen',
    '5LCZ6': 'dodgerblue',
    '6LCZ8': 'purple',
}
 

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
TKE_URBAN    = load_series(size_large, dir_w2,  cases_large, location2)
TKE_down    = load_series(size_large, dir_w2,  cases_large, location3) 

# ============================
# Multiple Linear Regression (numpy版)
# ============================

# 构造数据
TKEw_urban = np.array([np.nanmean(a) for a in TKE_URBAN])
TKEw_down  = np.array([np.nanmean(a) for a in TKE_down])
LWP_down   = np.array([np.nanmean(a) for a in LWP])

print("TKEw_urban:", TKEw_urban)
print("TKEw_down :", TKEw_down)
print("LWP_down  :", LWP_down)
# 设计矩阵 X（加常数项）
X = np.column_stack((TKEw_down, TKEw_urban, np.ones_like(TKEw_down)))
Y = LWP_down

# 最小二乘解
coef, *_ = np.linalg.lstsq(X, Y, rcond=None)

a = coef[0]
b = coef[1]
c = coef[2]

print("\nModel:")
print(f"LWP_down = {a:.3f} * TKEw_down + {b:.3f} * TKEw_urban + {c:.3f}")

# 预测
Y_pred = a*TKEw_down + b*TKEw_urban + c

# R2
ss_res = np.sum((Y - Y_pred)**2)
ss_tot = np.sum((Y - np.mean(Y))**2)
r2 = 1 - ss_res/ss_tot

print(f"R^2 = {r2:.3f}")





 
fig2, ax2 = plt.subplots(figsize=(7.3,5.5))
plt.subplots_adjust(left=0.14, bottom=0.18, right=0.95, top=0.95)


for i, ccase in enumerate(cases_large):
    ax2.scatter(Y[i], Y_pred[i],
                color=color_large[ccase],
                s=140,
                label=label_large[ccase])

# 1:1线
ymin = min(Y.min(), Y_pred.min())
ymax = max(Y.max(), Y_pred.max())
ax2.plot([ymin, ymax], [ymin, ymax], 'k--', linewidth=2)

# 标注公式
ax2.text(
    0.05, 0.95,
    rf"$\langle \overline{{\mathrm{{LWP}}}} \rangle_{{\mathrm{{down}}}}"
    rf" = {a:.2f}\langle \overline{{\mathrm{{TKE}}}} \rangle_{{\mathrm{{down}}}}"
    rf" {b:+.2f}\langle \overline{{\mathrm{{TKE}}}} \rangle_{{\mathrm{{urban}}}}"
    rf" {c:+.2f}$"
    + "\n" +
    rf"$R^2 = {r2:.2f}$",
    transform=ax2.transAxes,
    va='top',
    fontsize=16
)

ax2.set_xlabel(r'Simulated $\langle \overline{LWP}\rangle_{\mathrm{down}}\ \left(g\ m^{-2}\right)$')
ax2.set_ylabel(r'Predicted $\langle \overline{LWP}\rangle_{\mathrm{down}}\ \left(g\ m^{-2}\right)$')
ax2.legend(loc='upper left', bbox_to_anchor=(0.72, 0.5))
plt.savefig('./M100.png', dpi=300)

















