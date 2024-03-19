# source ~/venvs/butewind/bin/activate
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import xmitgcm
import sys
import os, glob, os.path


runname = sys.argv[1]
# get the last one:
d = glob.glob(f'../results/{runname}/input/spinup.*.data')
d.sort()
parts = d[-1].split('.')
print(parts)
lasttime = int(parts[3])

print('lasttime', lasttime)

taumax = 0.225  # N/m^2
t = np.arange(1000*1.0)  # hours
taut = 0 * t
taut[t<=24] = np.arange(25) / 24 * taumax
taut[(t>24) & (t<(5*24))] = taumax
taut[(t>=5*24) & (t<6*24)] = np.arange(23, -1, -1) / 24 * taumax

iters = np.arange(0, lasttime, 3600, dtype='int')

with xmitgcm.open_mdsdataset(f'../results/{runname}/input/', endian='<',
                             iters=iters, prefix=['spinup', 'spinup2d']) as ds:
    ds['pden'] = ds.THETA * -0.2 + ds.SALT * 0.75

    pden0 = ds.pden.isel(time=0, XC=100, YC=120)
    z = pden0.Z.values
    z = z[pden0>0]
    pden0 = pden0[pden0>0].values
    print(pden0)
    ts = xr.Dataset(coords={'time':ds.time})
    ts['maxden'] = ('time', ds.pden.sel(Z=-3.75, XC=slice(0, 50e3)).max(dim=['YC', 'XC']).data)
    dendepth = np. interp(ts.maxden.values, pden0, z)
    ts['dendepth'] = ('time', dendepth)
    ts.to_netcdf(f'MaxDen{runname}.nc')
