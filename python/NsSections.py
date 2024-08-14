# source ~/venvs/butewind/bin/activate
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import xmitgcm
import sys, os

"""
Plot plan view of the numerical setup, largescale
"""

runname = sys.argv[1]
iternum = np.arange(24*3600, 16*24*3600, 24*3600)
iternum = (np.arange(11 * 24) + 23) *3600

iternum = np.arange(0, 24*24, 3) * 3600


try:
    os.mkdir(f'../results/{runname}/slices/')
except:
    pass

newiter = []
notthere = []
for nn in iternum:
    if os.path.isfile(f'../results/{runname}/input/spinup.{nn:010d}.data'):
        newiter += [nn]
    else:
        notthere += [nn]


if notthere:
    print('Warning, not doing ', notthere)

if True:
    with xmitgcm.open_mdsdataset(f'../results/{runname}/input/',
                                 endian='<', iters=newiter,
                                 prefix=['spinup', 'spinup2d']) as ds0:
        ds = ds0.sel(XC=25e3, XG=25e3, method='nearest')
        ds.to_netcdf(f'../results/{runname}/slices/NsSecCoarse{runname}.nc')

os.system(f"ssh pender.seos.uvic.ca 'mkdir Dropbox/ButeWinds/{runname}/'")
os.system(f"rsync -av ../results/{runname}/slices/*.nc pender.seos.uvic.ca:Dropbox/ButeWinds/{runname}/")
