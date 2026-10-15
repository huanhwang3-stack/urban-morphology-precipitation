import os, re, glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib
from numpy import nanmean
def av(arr, axis):
    arr = np.isfinite(arr)*arr
    out = nanmean(arr, axis=axis)
    out = np.isfinite(out)*out
    return out

# ================= 字体 & LaTeX =================
font = {'family': 'Times New Roman','weight': 'normal','size': 24}
matplotlib.rc('font', **font)
plt.rc('text', usetex=True)

fig, ax  = plt.subplots(figsize=(10,5))
plt.subplots_adjust(left=0.12, right=0.90, bottom=0.16, top=0.96)


# ================== 小工具 ==================
def centers_to_edges(c):
    c = np.asarray(c, float)
    dc = np.diff(c)
    first = c[0] - dc[0]/2
    last  = c[-1] + dc[-1]/2
    mid   = 0.5*(c[:-1] + c[1:])
    return np.concatenate(([first], mid, [last]))

def nanmean_masked(arr, axis):
    arr = np.isfinite(arr)*arr
    out = np.nanmean(arr, axis=axis)
    out = np.isfinite(out)*out
    return out

def interp_1d_allow_nans(x, y, xi):
    """仅在有效点之间线性插值；端点外/有效点<2处返回 NaN。"""
    x  = np.asarray(x,  float)
    y  = np.asarray(y,  float)
    xi = np.asarray(xi, float)
    m = np.isfinite(y)
    if m.sum() < 2:
        return np.full_like(xi, np.nan, dtype=float)
    return np.interp(xi, x[m], y[m], left=np.nan, right=np.nan)

# ====== 基本路径与参数 ======
ROOT   = "./0npy"            # *_ql.npy 所在目录（二维 [z,x]）
ZW_PATH = "../0grey/zw.npy"
 
DX = 15.0
VMIN, VMAX = 0.0, 0.02       # 颜色条范围（单位：g kg^-1）
SAVE = "./4plot.png"  # 输出文件名（改成你想要的）

# ====== 读取 zw 并构造层中心 ======
zw = np.load(ZW_PATH).astype(float)   # (nz_edges,)
nz_edges = zw.size
z_edges = zw
z_centers = 0.5*(zw[:-1] + zw[1:])    # (nz)

case = "5LCZ6"
y1 = 215
y2=385 
 
ql_stack = np.load("/media/huanhuan/Expansion/4av/" + case  +"/ql_av.npy").astype(float)
ql_mean = np.nanmean(ql_stack[:,y1:y2,:], axis=1) *1000
 
nz, nx   = ql_mean.shape

# ====== 水平边界坐标 ======
x_edges   = np.arange(nx + 1, dtype=float) * DX
x_centers = 0.5*(x_edges[:-1] + x_edges[1:])

# =========================================================
# ==============   建筑遮罩 (来自第二段思路)   =============
# =========================================================
# 期望 u1 为 (t,z,y,x)。我们对 (t) 做时间平均，再在 y 上取一个很窄的带平均，
# 以得到 (z,x) 的遮罩源；其中 NaN 表示建筑/无效。
# ⚠️ 请把这个路径换成你自己的：
u1 = np.load('../0grey/ql.npy').astype(float)  # 预计 (t,z,y,x)
if u1.ndim != 4:
    raise ValueError("遮罩源 u1 期望 4 维 (t,z,y,x)")

mask_zyx = av(u1, 0)                 # (z,y,x) 时间平均
mask_band = mask_zyx[:,218:219, :]  # (z,2,x) y 带
mask_zx = av(mask_band, 1)  

# z 维对齐：若与 z_edges 等长，则转为层中心
if mask_zx.shape[0] == nz_edges:
    mask_zx = 0.5*(mask_zx[:-1, :] + mask_zx[1:, :])

# 与 ql_mean 对齐（裁剪到相同形状）
min_nz = min(mask_zx.shape[0], ql_mean.shape[0])
min_nx = min(mask_zx.shape[1], ql_mean.shape[1])
mask_zx  = mask_zx[:min_nz, :min_nx]
ql_mean  = ql_mean[:min_nz, :min_nx]
z_centers = z_centers[:min_nz]
x_centers = x_centers[:min_nx]
x_edges   = centers_to_edges(x_centers)
z_edges   = centers_to_edges(z_centers)

# ====== 标注 ======
xline = np.linspace(4000,4000,2)
yline = np.linspace(-2_000_000,200_000,2)
plt.plot(xline,yline,color='k',linestyle=':', linewidth=3, zorder=10)
plt.text(4250,2500,'Urban',    color='k',fontsize=24, zorder=11)
xline = np.linspace(6520,6520,2)
yline = np.linspace(-2_000_000,200_000,2)
plt.plot(xline,yline,color='k',linestyle=':', linewidth=3, zorder=10)
 

# 以 NaN 作为“建筑/无效”标志：True 表示需要遮罩
building_mask = np.isnan(mask_zx)

# 把 ql 的建筑处置为 NaN，便于后续插值与 set_bad 灰色显示
data_with_nan = np.where(building_mask, np.nan, ql_mean)

# =========================================================
# ==============   上采样 + 遮罩随插值传递   ===============
# =========================================================
fac_x, fac_z = 4, 4
nx = x_centers.size
nz = z_centers.size

x_hi = np.linspace(x_centers[0], x_centers[-1], nx*fac_x - (fac_x-1))
z_hi = np.linspace(z_centers[0], z_centers[-1], nz*fac_z - (fac_z-1))

# 先沿 X 插值：数据忽略 NaN；遮罩 True/False 转成 1/0 再阈值化
data_x = np.empty((nz, x_hi.size), dtype=float)
mask_x = np.empty((nz, x_hi.size), dtype=float)

for k in range(nz):
    data_x[k, :] = interp_1d_allow_nans(x_centers, data_with_nan[k, :], x_hi)
    mask_row = building_mask[k, :].astype(float)
    mask_x[k, :] = np.interp(x_hi, x_centers, mask_row)

# 再沿 Z 插值（同理）
data_hi = np.empty((z_hi.size, x_hi.size), dtype=float)
mask_hi = np.empty((z_hi.size, x_hi.size), dtype=float)

for j in range(x_hi.size):
    data_hi[:, j] = interp_1d_allow_nans(z_centers, data_x[:, j], z_hi)
    mask_hi[:, j] = np.interp(z_hi, z_centers, mask_x[:, j])

# 阈值：>=0.5 判为建筑；用灰色显示（set_bad）
mask_hi_bool = mask_hi >= 0.5
data_hi = np.ma.array(data_hi, mask=mask_hi_bool)

x_edges_hi = centers_to_edges(x_hi)
z_edges_hi = centers_to_edges(z_hi)

# ========== 颜色映射（前 25 个颜色白色，且对 NaN 用灰色）==========
jet = plt.cm.get_cmap('jet', 256)
newcolors = jet(np.linspace(0, 1, 256))
white = np.ones((25, 4))
newcolors[:25, :] = white
newcmp = ListedColormap(newcolors)
newcmp.set_bad('gray', alpha=1.0)   # 关键：遮罩部分灰色

# ========== 绘图 ==========
mesh = ax.pcolormesh(
    x_edges_hi, z_edges_hi, data_hi,    # (nz_hi, nx_hi)
    cmap=newcmp, vmin=VMIN, vmax=VMAX,
    shading='flat', antialiased=False
)

# 独立色标（不被遮罩范围影响）
divider = make_axes_locatable(ax)
 
cbar = plt.colorbar(mesh, ax=ax, pad=0.02, fraction=0.06, aspect=25)
cbar.set_label(r"$\langle \overline{q_l} \rangle_y$ (g kg$^{-1}$)", fontsize=24)




plt.arrow(400, 2000, 1000, 0, head_width=50, head_length=50, fc='blue', ec='black', zorder=12)
plt.text(1000,2050,'$u$',color='k',fontsize=24, zorder=12)

ax.set_xlabel("X (m)")
ax.set_ylabel("Z (m)")
ax.set_xlim(x_edges[0], x_edges[-1])
ax.set_ylim(z_edges[0], 3000)

plt.savefig(SAVE, dpi=400)
print(f"[OK] saved {SAVE}")

