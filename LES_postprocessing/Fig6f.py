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
def get_lwp_peak(profile, smooth_window=15):
    """Return smoothed peak LWP."""
    profile = np.asarray(profile, dtype=float)
    smooth = np.convolve(profile, np.ones(smooth_window)/smooth_window, mode='same')
    return np.nanmax(smooth)

def get_lwp_mean(profile, x, x1, x2):
    """Return spatial mean LWP over x1-x2."""
    mask = (x >= x1) & (x <= x2)
    return np.nanmean(profile[mask])
 
 
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

fig, ax  = plt.subplots(figsize=(7,5))
plt.subplots_adjust(left=0.14, right=0.94, bottom=0.14, top=0.98)

 

time_points = np.arange(0,7500,15)  
y1 = 108
y2=192 

 
LCZ1S = np.load('../2LCZ1S/3Fig3a/6npy/LWP.npy')
print("LCZ1S",np.shape(LCZ1S))
LCZ1S_y = av(LCZ1S[y1:y2,:],0) 
l1, = ax.plot(time_points, LCZ1S_y,color='b', marker='*', linestyle=':')
  
x_LCZ1 =   np.arange(0,7500,15)
x_upwind = 133  * 15
x_downwind = 217  * 15
x_down_end = 7500 
LCZ1S_peak = get_lwp_peak(LCZ1S_y)
LCZ1S_urban = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_downwind)
LCZ1S_down = get_lwp_mean(LCZ1S_y, x_LCZ1, x_downwind, x_down_end)
LCZ1S_whole = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_down_end)

print("LCZ1S_peak normal",LCZ1S_peak)
print("LCZ1S_urban",LCZ1S_urban)
print("LCZ1S_down",LCZ1S_down)
print("LCZ1S_whole",LCZ1S_whole)


 
 
LCZ1S = np.load('../2LCZ1SU0/3Fig3a/6npy/LWP.npy')
print("LCZ1S",np.shape(LCZ1S))
LCZ1S_y = av(LCZ1S[y1:y2,:],0) 
l2, = ax.plot(time_points, LCZ1S_y,color='green', marker='*', linestyle=':')
  



LCZ1S_peak = get_lwp_peak(LCZ1S_y)
LCZ1S_urban = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_downwind)
LCZ1S_down = get_lwp_mean(LCZ1S_y, x_LCZ1, x_downwind, x_down_end)
LCZ1S_whole = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_down_end)

print("LCZ1S_peak 0.1",LCZ1S_peak)
print("LCZ1S_urban",LCZ1S_urban)
print("LCZ1S_down",LCZ1S_down)
print("LCZ1S_whole",LCZ1S_whole)


 


LCZ1S = np.load('../2LCZ1SU5/3Fig3a/6npy/LWP.npy')
print("LCZ1S",np.shape(LCZ1S))
LCZ1S_y = av(LCZ1S[y1:y2,:],0) 
l3, = ax.plot(time_points, LCZ1S_y,color='k', marker='*', linestyle=':')
  

LCZ1S_peak = get_lwp_peak(LCZ1S_y)
LCZ1S_urban = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_downwind)
LCZ1S_down = get_lwp_mean(LCZ1S_y, x_LCZ1, x_downwind, x_down_end)
LCZ1S_whole = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_down_end)

print("LCZ1S_peak 5",LCZ1S_peak)
print("LCZ1S_urban",LCZ1S_urban)
print("LCZ1S_down",LCZ1S_down)
print("LCZ1S_whole",LCZ1S_whole)









x_upwind = 133*15
x_downwind =217*15

plt.axvspan(x_upwind, x_downwind, color='gray', alpha=0.34)

ax.text(2200, 40, 'Urban', color='k')



plt.legend([ l1,l2,l3 ],[ 'LCZ1SU1','LCZ1SU0.1','LCZ1SU5', ],fontsize=20,loc = 1,ncol = 1)

 
plt.xlabel("X (m)", fontsize=20)
plt.ylabel( r'$\langle \overline{\mathrm{LWP}} \rangle_y \ \mathrm{(g\,m^{-2})}$',fontsize=20)
#plt.grid(True, linestyle='--', alpha=0.7)

plt.ylim(0,300) 
plt.xlim(0,7500) 
plt.savefig('./4U.png')
 














