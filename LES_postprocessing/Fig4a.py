import os, re, glob
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt

import matplotlib
font = {'family':'Times New Roman','weight':'normal','size':24}
matplotlib.rc('font', **font)
plt.rc('text', usetex=True)

fig, ax  = plt.subplots(figsize=(10,5))
plt.subplots_adjust(left=0.12, right=0.88, bottom=0.16, top=0.96)

from numpy import nanmean
def av(arr, axis):
    arr = np.isfinite(arr)*arr
    out = nanmean(arr, axis=axis)
    out = np.isfinite(out)*out
    return out


case = "2LCZ1"

y1 = 215
y2=385 




# ====== 基本路径与参数 ======
zw = np.load("../0grey/zw.npy").astype(float)     # z 边界 (nz_edges,)
z_edges = zw
nz_edges = z_edges.size
DX = 15.0
vmin, vmax = -0.5, 0.5

# ====== 读入时间平均场（你的预计算结果）======
w_mean_av = np.load("/media/huanhuan/Expansion/4av/" + case  + "/w_av.npy").astype(float)   # 期望 (nz?, nx)
u_mean_av = np.load("/media/huanhuan/Expansion/4av/" + case  +"/u_av.npy").astype(float)


w_mean = np.nanmean(w_mean_av[:,y1:y2,:], axis=1)
u_mean = np.nanmean(u_mean_av[:,y1:y2,:], axis=1)


# —— 将 u/w 统一到“层中心”坐标（若是 w 面就相邻平均一次）
def to_layer_center(arr, z_edges_len):
    if arr.ndim != 2:
        raise ValueError("期望二维 [z,x]")
    nz, nx = arr.shape
    if nz == z_edges_len:         # w 面 → 层中心
        return 0.5*(arr[:-1,:] + arr[1:,:])
    elif nz == z_edges_len - 1:   # 已经是层中心
        return arr
    else:
        raise ValueError(f"z 维长度 {nz} 与 zw 不匹配 (应为 {z_edges_len} 或 {z_edges_len-1})")

w_c = to_layer_center(w_mean, nz_edges)   # (nz_c, nx)
u_c = to_layer_center(u_mean, nz_edges)   # (nz_c, nx)

nz_c, nx = w_c.shape
# 水平边界与中心
x_edges = np.arange(nx+1, dtype=float) * DX
x_centers = 0.5*(x_edges[:-1] + x_edges[1:])
# 垂直中心
z_centers = 0.5*(z_edges[:-1] + z_edges[1:])   # (nz_c,)

# ====== 建筑遮罩：读入并统一到层中心，然后与数据对齐 ======
u1 = np.load('../0grey/ql.npy').astype(float)  # 预计 (t,z,y,x)
if u1.ndim != 4:
    raise ValueError("遮罩源 u1 期望 4 维 (t,z,y,x)")

mask_zyx = av(u1, 0)                 # (z,y,x) 时间平均
mask_band = mask_zyx[:,218:219, :]  # (z,2,x) y 带
mask_zx = av(mask_band, 1)           # (z,x)

mask_c = to_layer_center(mask_zx, nz_edges)   # → 层中心 (nz_c, nx_mask)
# 对齐到 (nz_c, nx)
nx_mask = mask_c.shape[1]
nx_min = min(nx, nx_mask)
if nx_min != nx:
    print(f"[WARN] 遮罩 nx={nx_mask} 与数据 nx={nx} 不一致，裁剪到 {nx_min}")
    w_c  = w_c[:, :nx_min]
    u_c  = u_c[:, :nx_min]
    x_edges = x_edges[:nx_min+1]
    x_centers = x_centers[:nx_min]
    mask_c = mask_c[:, :nx_min]
    nx = nx_min

building_mask = np.isnan(mask_c)
w_masked = np.ma.array(w_c, mask=building_mask)

xline = np.linspace(4000,4000)
yline = np.linspace(-2000000,200000)
#plt.plot(xline,yline,color='k',linestyle=':', linewidth=3)
#plt.text(2050,1250,'Urban',color='k',fontsize=24, rotation=0)
#xline = np.linspace(3000,3000)
#yline = np.linspace(-2000000,200000)
#plt.plot(xline,yline,color='k',linestyle=':', linewidth=3) 
 
#plt.text(5050,1250,'Downwind',color='k',fontsize=24, rotation=0)
#plt.text(450,1250,'Upwind',color='k',fontsize=24, rotation=0)
#plt.arrow(400, 2000, 500, 0, head_width=50, head_length=50, fc='blue', ec='black')
#plt.text(1000,1050,'$u$',color='k',fontsize=24, rotation=0)
 
 
# ====== 底图：pcolormesh（不平滑）=====
import copy
cmap = copy.deepcopy(plt.get_cmap('bwr'))
cmap.set_bad('gray', alpha=1.0)
 

im = ax.pcolormesh(
    x_edges, z_edges, w_masked,   # (nx+1,), (nz_edges,), (nz_c,nx)
    cmap=cmap, vmin=vmin, vmax=vmax,
    shading='flat'
)

# ====== 标注 ======
xline = np.linspace(4000,4000,2)
yline = np.linspace(-2_000_000,200_000,2)
plt.plot(xline,yline,color='k',linestyle=':', linewidth=3, zorder=10)
plt.text(4250,1250,'Urban',    color='k',fontsize=24, zorder=11)
xline = np.linspace(6520,6520,2)
yline = np.linspace(-2_000_000,200_000,2)
plt.plot(xline,yline,color='k',linestyle=':', linewidth=3, zorder=10)
 
# ====== streamplot：如 z_centers 非等间距，则沿 z 插值到等距网格 ======
dz = np.diff(z_centers)
if not np.allclose(dz, dz[0]):
    z_uniform = np.linspace(z_centers.min(), z_centers.max(), nz_c)
    u_uni = np.empty_like(u_c)
    w_uni = np.empty_like(w_c)
    for j in range(nx):
        u_uni[:, j] = np.interp(z_uniform, z_centers, u_c[:, j])
        w_uni[:, j] = np.interp(z_uniform, z_centers, w_c[:, j])
    z_for_stream = z_uniform
    u_for_stream = u_uni
    w_for_stream = w_uni
else:
    z_for_stream = z_centers
    u_for_stream = u_c
    w_for_stream = w_c

speed = np.hypot(u_for_stream, w_for_stream)
# 注意：streamplot 接受 1D x/y；这里用中心坐标
ax.streamplot(
    x_centers, z_for_stream, u_for_stream, w_for_stream,
    color='k', linewidth=0.8, density=2.0, arrowsize=1.0, zorder=6
)
# 如果想用颜色映射（速度大小）：
# ax.streamplot(x_centers, z_for_stream, u_for_stream, w_for_stream,
#               color=speed, cmap='jet', linewidth=0.8, density=2.0, arrowsize=1.0, zorder=6)

# ====== 侧边色标 ======
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="3%", pad=0.05)
cbar = fig.colorbar(im, cax=cax)
cbar.set_label(r'$\langle \overline{ w }\rangle_y\ \mathrm{(m\,s^{-1})}$')


ax.set_xlabel("X (m)")
ax.set_ylabel("Z (m)")
ax.set_xlim(0, 15000)
ax.set_ylim(0, 1500)

plt.savefig("./2plot.png", dpi=400)
print("[OK] saved ./1plot.png")

