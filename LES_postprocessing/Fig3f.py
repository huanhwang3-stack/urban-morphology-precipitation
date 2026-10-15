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

time_points = np.arange(0,15000,15)
y1 = 215
y2=385 


LCZ1S = np.load('../2LCZ1/3Fig3a/6npy/LWP.npy')
print("LCZ1S",np.shape(LCZ1S))
LCZ1S_y = av(LCZ1S[y1:y2,:],0)
l1, = ax.plot(time_points, LCZ1S_y,color='r', marker='o', linestyle=':')
np.save("./0npy/LCZ1.npy",LCZ1S_y)  
 


x_LCZ1 =   np.arange(0,15000,15)
x_upwind = 266 * 15
x_downwind = 434 * 15
x_down_end = 15000
LCZ1_peak = get_lwp_peak(LCZ1S_y)
LCZ1_urban = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_downwind)
LCZ1_down = get_lwp_mean(LCZ1S_y, x_LCZ1, x_downwind, x_down_end)
LCZ1_whole = get_lwp_mean(LCZ1S_y, x_LCZ1, x_upwind, x_down_end)
print("normal LCZ1_peak",LCZ1_peak)
print("normal LCZ1_urban",LCZ1_urban)
print("normal LCZ1_down",LCZ1_down)
print("normal LCZ1_whole",LCZ1_whole)





 
LCZ1S = np.load('../3LCZ3/3Fig3a/6npy/LWP.npy')
LCZ3S_y = av(LCZ1S[y1:y2,:],0)
l2, = ax.plot(time_points, LCZ3S_y,color='orange', marker='o', linestyle=':')
np.save("./0npy/LCZ3.npy",LCZ3S_y)   
 

LCZ3_peak = get_lwp_peak(LCZ3S_y)
LCZ3_urban = get_lwp_mean(LCZ3S_y, x_LCZ1, x_upwind, x_downwind)
LCZ3_down = get_lwp_mean(LCZ3S_y, x_LCZ1, x_downwind, x_down_end)
LCZ3_whole = get_lwp_mean(LCZ3S_y, x_LCZ1, x_upwind, x_down_end)

print("normal LCZ3_peak",LCZ3_peak)
print("normal LCZ3_urban",LCZ3_urban)
print("normal LCZ3_down",LCZ3_down)
print("normal LCZ3_whole",LCZ3_whole)





LCZ1S = np.load('../4LCZ4/3Fig3a/6npy/LWP.npy')
LCZ4S_y = av(LCZ1S[y1:y2,:],0)
l3, = ax.plot(time_points, LCZ4S_y,color='g', marker='o', linestyle=':')
np.save("./0npy/LCZ4.npy",LCZ4S_y)    


LCZ4_peak = get_lwp_peak(LCZ4S_y)
LCZ4_urban = get_lwp_mean(LCZ4S_y, x_LCZ1, x_upwind, x_downwind)
LCZ4_down = get_lwp_mean(LCZ4S_y, x_LCZ1, x_downwind, x_down_end)
LCZ4_whole = get_lwp_mean(LCZ4S_y, x_LCZ1, x_upwind, x_down_end)

print("normal LCZ4_peak",LCZ4_peak)
print("normal LCZ4_urban",LCZ4_urban)
print("normal LCZ4_down",LCZ4_down)
print("normal LCZ4_whole",LCZ4_whole)






LCZ1S = np.load('../5LCZ6/3Fig3a/6npy/LWP.npy')
LCZ6S_y = av(LCZ1S[y1:y2,:],0)
l4, = ax.plot(time_points, LCZ6S_y,color='b', marker='o', linestyle=':')
np.save("./0npy/LCZ6.npy",LCZ6S_y)     


LCZ6_peak = get_lwp_peak(LCZ6S_y)
LCZ6_urban = get_lwp_mean(LCZ6S_y, x_LCZ1, x_upwind, x_downwind)
LCZ6_down = get_lwp_mean(LCZ6S_y, x_LCZ1, x_downwind, x_down_end)
LCZ6_whole = get_lwp_mean(LCZ6S_y, x_LCZ1, x_upwind, x_down_end)

print("normal LCZ6_peak",LCZ6_peak)
print("normal LCZ6_urban",LCZ6_urban)
print("normal LCZ6_down",LCZ6_down)
print("normal LCZ6_whole",LCZ6_whole)






LCZ1S = np.load('../6LCZ8/3Fig3a/6npy/LWP.npy')
LCZ8S_y = av(LCZ1S[y1:y2,:],0)
l5, = ax.plot(time_points, LCZ8S_y,color='k', marker='o', linestyle=':')
np.save("./0npy/LCZ8.npy",LCZ8S_y)      

LCZ8_peak = get_lwp_peak(LCZ8S_y)
LCZ8_urban = get_lwp_mean(LCZ8S_y, x_LCZ1, x_upwind, x_downwind)
LCZ8_down = get_lwp_mean(LCZ8S_y, x_LCZ1, x_downwind, x_down_end)
LCZ8_whole = get_lwp_mean(LCZ8S_y, x_LCZ1, x_upwind, x_down_end)

print("normal LCZ8_peak",LCZ8_peak)
print("normal LCZ8_urban",LCZ8_urban)
print("normal LCZ8_down",LCZ8_down)
print("normal LCZ8_whole",LCZ8_whole)

x_upwind = 3990
x_downwind = 6510
plt.axvspan(x_upwind, x_downwind, color='gray', alpha=0.34)
ax.text(4100, 25, 'Urban', color='k')

plt.legend([ l1,l2,l3,l4 ,l5],[ 'LCZ1','LCZ3','LCZ4','LCZ6','LCZ8' ],fontsize=20,loc = 2,ncol = 1)

 
plt.xlabel("X (m)", fontsize=20)
plt.ylabel( r'$\langle \overline{\mathrm{LWP}} \rangle_y \ \mathrm{(g\,m^{-2})}$',fontsize=20)
#plt.grid(True, linestyle='--', alpha=0.7)

plt.ylim(0,100) 
plt.xlim(0,15000) 
plt.savefig('./100LWP.png')
 















