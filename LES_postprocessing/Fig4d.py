import os, re, glob
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt

import matplotlib
from matplotlib.colors import ListedColormap


y1 = 215
y2=385 


# ========== 字体 & LaTeX ==========
font = {'family':'Times New Roman','weight':'normal','size':24}
matplotlib.rc('font', **font)
plt.rc('text', usetex=True)

fig, ax  = plt.subplots(figsize=(10,5))
plt.subplots_adjust(left=0.12, right=0.86, bottom=0.16, top=0.96)

# ========== 小工具 ==========
from numpy import nanmean
def av(arr, axis):
    arr = np.isfinite(arr)*arr
    out = nanmean(arr, axis=axis)
    out = np.isfinite(out)*out
    return out

def centers_to_edges(c):
    """将中心坐标转为边界坐标，等间距/非等间距均可。"""
    c = np.asarray(c, float)
    dc = np.diff(c)
    first = c[0] - dc[0]/2
    last  = c[-1] + dc[-1]/2
    mid   = 0.5*(c[:-1] + c[1:])
    return np.concatenate(([first], mid, [last]))

def interp_1d_allow_nans(x, y, xi):
    """
    1D 线性插值：忽略 y 中的 NaN，仅在有效点之间插值；
    若有效点 < 2，返回全 NaN。
    """
    x  = np.asarray(x,  float)
    y  = np.asarray(y,  float)
    xi = np.asarray(xi, float)
    m = np.isfinite(y)
    if m.sum() < 2:
        return np.full_like(xi, np.nan, dtype=float)
    return np.interp(xi, x[m], y[m], left=np.nan, right=np.nan)

# ========== 基本路径与参数 ==========
DX = 15.0
vmin, vmax = -0.1, 0.1                # 保持你的固定色标
ZW_PATH = "../0grey/zw.npy"

# ========== 读取 z 边界并构造中心 ==========
zw = np.load(ZW_PATH).astype(float)   # (nz_edges,)
z_edges = zw
z_centers = 0.5*(zw[:-1] + zw[1:])    # (nz)

# ========== 读入时间平均场（你的预计算结果）==========
# 说明：wpqp 形状预期为 (nz?, ny, nx) 或 (nt, nz, nx)；你上一版给的是 (time-avg 后的) (nz?, nx)
# 这里沿用你现有的处理：先在 y=200:300 做平均，再乘 1000
wpqp = np.load("./1npy/wpqp.npy").astype(float)   # 期望 (nz?, y, x)
w_mean = av(wpqp[:, y1:y2, :], axis=1) * 1000.0 # -> (nz?, nx)
w_c = w_mean                                      # (nz_w, nx)

nz_w, nx = w_c.shape
x_edges = np.arange(nx+1, dtype=float) * DX
x_centers = 0.5*(x_edges[:-1] + x_edges[1:])      # (nx,)

# ========== 将 w_c 对齐到层中心 (若 w_c 在边界层上) ==========
nz_edges = z_edges.size
if nz_w == nz_edges:
    # 边界 -> 中心
    w_c = 0.5*(w_c[:-1, :] + w_c[1:, :])
    nz_w = w_c.shape[0]

# 现在期望 nz_w == len(z_centers)
if nz_w != len(z_centers):
    min_nz = min(nz_w, len(z_centers))
    w_c = w_c[:min_nz, :]
    z_centers = z_centers[:min_nz]
    z_edges = centers_to_edges(z_centers)  # 重新构造边界以匹配

# ========== 建筑遮罩（灰色） ==========
u1 =np.load('../0grey/ql.npy').astype(float)   # 预期 (t,z,y,x)
if u1.ndim != 4:
    raise ValueError("遮罩源 u1 期望 4 维 (t,z,y,x)")

mask_zyx = av(u1, 0)                 # (z,y,x) 时间平均
mask_band = mask_zyx[:, 218:219, :]  # (z,2,x) y 带
mask_zx = av(mask_band, 1)           # (z,x)

# 将遮罩对齐到层中心：若与 z_edges 等长，则转为中心；否则裁剪/一致化
if mask_zx.shape[0] == nz_edges:
    mask_zx = 0.5*(mask_zx[:-1, :] + mask_zx[1:, :])

# 对齐到 w_c 尺度
min_nz = min(mask_zx.shape[0], w_c.shape[0])
min_nx = min(mask_zx.shape[1], w_c.shape[1])
mask_zx = mask_zx[:min_nz, :min_nx]
w_c     = w_c[:min_nz, :min_nx]
z_centers = z_centers[:min_nz]
x_centers = x_centers[:min_nx]
x_edges   = centers_to_edges(x_centers)
z_edges   = centers_to_edges(z_centers)

# 建筑区域设为 NaN；遮罩判定：NaN 为建筑/无效
building_mask = np.isnan(mask_zx)         # True 表示建筑/灰色
data_with_nan = np.where(building_mask, np.nan, w_c)

# ========== 标注 ==========
xline = np.linspace(4000,4000,2)
yline = np.linspace(-2_000_000,200_000,2)
plt.plot(xline,yline,color='k',linestyle=':', linewidth=3, zorder=10)
plt.text(4250,1250,'Urban',    color='k',fontsize=24, zorder=11)
xline = np.linspace(6520,6520,2)
yline = np.linspace(-2_000_000,200_000,2)
plt.plot(xline,yline,color='k',linestyle=':', linewidth=3, zorder=10)
#plt.text(5050,1250,'Downwind', color='k',fontsize=24, zorder=11)
#plt.text(450,1250,'Upwind',    color='k',fontsize=24, zorder=11)


# ========== 上采样（仅线性插值，非模糊） ==========
fac_x, fac_z = 4, 4      # 可调：3~6 之间更平滑
nx = x_centers.size
nz = z_centers.size

x_hi = np.linspace(x_centers[0], x_centers[-1], nx*fac_x - (fac_x-1))
z_hi = np.linspace(z_centers[0], z_centers[-1], nz*fac_z - (fac_z-1))

# 1) 先沿 X 插值数据与遮罩
data_x = np.empty((nz, x_hi.size), dtype=float)
mask_x = np.empty((nz, x_hi.size), dtype=float)   # 遮罩用 float，后续阈值化

for k in range(nz):
    # 数据：忽略 NaN 插值
    data_x[k, :] = interp_1d_allow_nans(x_centers, data_with_nan[k, :], x_hi)
    # 遮罩：True->1, False->0，线性插值后再阈值
    mask_row = building_mask[k, :].astype(float)
    mask_x[k, :] = np.interp(x_hi, x_centers, mask_row)

# 2) 再沿 Z 插值数据与遮罩
data_hi = np.empty((z_hi.size, x_hi.size), dtype=float)
mask_hi = np.empty((z_hi.size, x_hi.size), dtype=float)

for j in range(x_hi.size):
    col_data = data_x[:, j]
    data_hi[:, j] = interp_1d_allow_nans(z_centers, col_data, z_hi)
    mask_col = np.interp(z_hi, z_centers, mask_x[:, j])
    mask_hi[:, j] = mask_col

# 3) 阈值化遮罩（>=0.5 视作建筑/无效）
mask_hi_bool = mask_hi >= 0.5
data_hi = np.ma.array(data_hi, mask=mask_hi_bool)

# 4) 高分辨中心 -> 边界
x_edges_hi = centers_to_edges(x_hi)
z_edges_hi = centers_to_edges(z_hi)

# ========== 颜色映射（保留灰色 mask） ==========
import copy
cmap = copy.deepcopy(plt.get_cmap('bwr'))
cmap.set_bad('gray', alpha=1.0)

# ========== 绘制（保持原 vmin/vmax，不改变色条范围） ==========
im = ax.pcolormesh(
    x_edges_hi, z_edges_hi[1:], data_hi[1:,:],
    cmap=cmap, vmin=vmin, vmax=vmax,
    shading='flat', antialiased=False
)

# 色标
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="3%", pad=0.05)
cbar = fig.colorbar(im, cax=cax)
cbar.set_label(r'$\langle \overline{w^{\prime} q^{\prime}} \rangle_y\ \mathrm{(g\ kg^{-1}\ m\ s^{-1})}$')


# 可选：来个风向箭头
plt.arrow(400, 1200, 800, 0, head_width=40, head_length=80, fc='blue', ec='black', zorder=12)
plt.text(900,1250,'$u$',color='k',fontsize=24, zorder=12)

# 轴设置
ax.set_xlabel("X (m)")
ax.set_ylabel("Z (m)")
ax.set_xlim(x_edges[0], x_edges[-1])
ax.set_ylim(10, 1500)

plt.savefig("./5plot.png", dpi=400)
print("[OK] saved ./5plot.png")

