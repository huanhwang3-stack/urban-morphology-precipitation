import numpy as np
from numpy import ma
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.ticker as mtick
from scipy.interpolate import *
from matplotlib.pyplot import *
from scipy.stats import *
from numpy import nanmean
from numpy import nan
from mpl_toolkits.axes_grid1 import make_axes_locatable

 
def av (arr, axis):

        arr = np.isfinite(arr)*arr
        temp_arr = nanmean(arr,axis=axis)
        temp_arr = np.isfinite(temp_arr)*temp_arr
        return temp_arr

 
from numpy import nanmean
def av (arr, axis):

        arr = np.isfinite(arr)*arr
        temp_arr = nanmean(arr,axis=axis)
        temp_arr = np.isfinite(temp_arr)*temp_arr
        return temp_arr


def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
#---using Latex
font = {'family' : 'serif', 'size' : 20}
matplotlib.rc('font', **font)
plt.rc('legend', fontsize=20)
plt.rc('legend', frameon=False)
plt.rc('text',usetex=True)

fig, ax  = plt.subplots(figsize=(9,5))
plt.subplots_adjust(left=0.1, right=0.92, bottom=0.11, top=0.96)

x1=0
x2 = 1000
y1=0
y2 = 600

case = "2LCZ1"
 
ql = np.load("/media/huanhuan/Expansion/4av/" + case  + "/ql_av.npy").astype(float)   
zw=np.load("../0grey/zw.npy").astype(float)
 
 
dz = np.diff(zw)               
dz = np.append(dz, dz[-1])    


ql_1 = ql[:,y1:y2,x1:x2]

mask_av =av( ql_1[2:4,:,:],0)
mask  = np.isnan(mask_av)


rho_d =   1.0  

 
U_x_1 = np.nansum(ql_1[:, :, :] * dz[:, None, None] * rho_d, axis=0)*1000  # shape: (y, x)

print("np.max",np.max(U_x_1))
 

y11 = y1 * 15
y22 = y2 * 15

x11 = x1 * 15
x22 = x2 * 15
 
 
x_Votx =  av(U_x_1,0)  
z_Votx =  av(U_x_1,1)  
zz = np.linspace(y11,y22,len(z_Votx))
xx = np.linspace(x11,x22,len(x_Votx))
X,Z = np.meshgrid(xx,zz)
extent=[x11,x22,y11,y22]
cmap = matplotlib.cm.jet
cmap.set_bad('gray',alpha=0.75)
 
 

np.save('./6npy/LWP.npy',U_x_1)
 
vari = U_x_1.copy()
vari[mask] = np.nan

masked_analysis = np.ma.array(vari, mask=np.isnan(vari))

print("mask_av min/max:", np.min(mask_av), np.max(mask_av))
print("vari NaN count:", np.isnan(vari).sum())

cmap = plt.get_cmap('Reds')
cmap.set_bad('gray', alpha=0.2)
im = plt.pcolormesh(X,Z, masked_analysis,vmin=0, vmax=40, cmap=cmap, shading='gouraud', edgecolors='None', alpha=1.0)

 

plt.ylim([y11,y22])
plt.xlim([x11,x22])
plt.xlabel(r' X (m) ',fontdict=font,labelpad=-3)
plt.ylabel(r'Y (m) ',fontdict=font,labelpad=1.0)
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="3%", pad=0.05)
cbar=plt.colorbar(im,cax=cax, ticks= np.arange(0,50,10))
cbar_label =r'$\overline{LWP} \ \mathrm{(g m^{-2})}$'   
cbar.ax.set_ylabel(cbar_label,labelpad=3.0)






plt.savefig('./Fig2a.png')
 















