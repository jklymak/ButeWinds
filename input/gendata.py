# on narval `source ~/venvs/bute_venv_narval/bin/activate`
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# from pylab import *
from shutil import copy
from os import mkdir
import shutil,os,glob
#import scipy.signal as scisig
from maketopo import getTopo2D
import logging
import pandas as pd
from replace_data import replace_data
from local_utils import o2sat
# import sys
import argparse

def gendata(runnumber, NsqFac=1.0, wind=20.0, windL=60e3, fjordL=180e3, fjordW=3e3, fjordD=200, endTime=1036800,
            NsqConstant=True, NsqScale=None):

  logging.basicConfig(level=logging.INFO)

  _log = logging.getLogger(__name__)

  duration = 17
  initial = False
  # wind = wind  # m/s *3.6 to get km/h, wind**2 / 1000 to get stress
  uw = wind
  lat = 45
  f0 = 1e-4 * np.sin(lat * np.pi / 180) / np.sin(45 * np.pi / 180)
  wavey = False
  Nsq0 = 3.44e-4
  NsqConstant = NsqConstant
  NsqScale = NsqScale
  if NsqScale is not None:
    NsqConstant = False
    NsqExp = True
  else:
    NsqExp = False
  tAlpha = 2.0e-4
  sBeta = 7.4e-4

  # Note this still works
  Nsq0 = Nsq0 * NsqFac

  runname = f'Bute3d{runnumber}'
  comments = f"""
  As run 43.  Tau={wind**2*1e-3} N/m^2 ({wind} m/s)
  Lat = {lat}; f={f0:1.3e}
  Variable Nsq; steady forcing....
  advschemes = 77 for both salt and temp
  Variable Nsq, Temperature passive, but set to something that will
  have reasonable flux.  Can't vary in space!  8.9 degrees C about right.

  """

  outdir0='../results/'+runname+'/'

  indir =outdir0+'/indata/'

  dx0=50.
  dy0=50.

  # model size
  nx = 24 * 80
  ny = 4 * 60
  nz = 66

  _log.info('nx %d ny %d', nx, ny)

  def lininc(n,Dx,dx0):
      a=(Dx-n*dx0)*2./n/(n+1)
      dx = dx0+arange(1.,n+1.,1.)*a
      return dx


  #### Set up the output directory
  backupmodel = True
  if backupmodel:
    try:
      mkdir(outdir0)
    except:
      import datetime
      import time
      ts = time.time()
      st=datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
      shutil.move(outdir0[:-1],outdir0[:-1]+'.bak'+st)
      mkdir(outdir0)

      _log.info(outdir0+' Exists')

    outdir=outdir0
    try:
      mkdir(outdir)
    except:
      _log.info(outdir+' Exists')
    outdir=outdir+'input/'
    try:
      mkdir(outdir)
    except:
      _log.info(outdir+' Exists')
    try:
        mkdir(outdir+'/figs/')
    except:
      pass

    copy('gendata.py',outdir)
  else:
    outdir=outdir+'input/'

  ## Copy some other files
  _log.info( "Copying files")

  try:
    shutil.rmtree(outdir+'/../code/')
  except:
    _log.info("code is not there anyhow")
  shutil.copytree('../code', outdir+'/../code/')
  shutil.copytree('../python', outdir+'/../python/')

  try:
    shutil.rmtree(outdir+'/../build/')
  except:
    _log.info("build is not there anyhow")
  _log.info(outdir+'/../build/')
  mkdir(outdir+'/../build/')

  # copy any data that is in the local indata
  shutil.copytree('../indata/', outdir+'/../indata/')
  try:
    shutil.copy('../build/mitgcmuv', outdir+'/../build/mitgcmuv')
    shutil.copy('../build/Makefile', outdir+'/../build/Makefile')
  except:
    pass
  replace_data('data', 'f0', f'{f0:1.3e}')
  replace_data('data', 'tAlpha', f'{tAlpha:1.3e}')
  replace_data('data', 'sBlpha', f'{sBeta:1.3e}')
  replace_data('data', 'endTime', f'{endTime:d}')

  shutil.copy('data', outdir+'/data')
  shutil.copy('eedata', outdir)
  shutil.copy('data.kl10', outdir)
  shutil.copy('moddata.py', outdir)
  try:
    shutil.copy('data.kpp', outdir)
  except:
    pass

  try:
      shutil.copy('data.obcs', outdir)
  except:
      pass
  try:
    shutil.copy('data.diagnostics', outdir)
  except:
    pass
  try:
    shutil.copy('data.pkg', outdir+'/data.pkg')
  except:
    pass
  try:
    shutil.copy('data.ptracers', outdir+'/data.ptracers')
  except:
    pass
  try:
    shutil.copy('data.rbcs', outdir+'/data.rbcs')
  except:
    pass

  _log.info("Done copying files")

  ####### Make the grids #########

  # Make grids:

  ##### Dx ######

  dx = np.zeros(nx) + dx0
  for i in range(nx-250, nx):
      dx[i] = dx[i-1] * 1.025


  # dx = zeros(nx)+100.
  x=np.cumsum(dx)
  x=x-x[0]
  maxx=np.max(x)
  _log.info('XCoffset=%1.4f'%x[0])

  ##### Dy ######

  dy = np.ones(ny) * dy0
  for i in range(int(ny/2) + 20, ny):
    dy[i] = dy[i-1] * 1.045
  for i in range(int(ny/2) - 20, 0, -1):
    dy[i] = dy[i+1] * 1.045
  y=np.cumsum(dy)
  y = y - y[int(ny/2)]

  # save dx and dy
  with open(indir+"/delX.bin", "wb") as f:
    dx.tofile(f)
  f.close()
  with open(indir+"/delY.bin", "wb") as f:
    dy.tofile(f)
  f.close()

  # some plots
  fig, ax = plt.subplots(2,1)
  ax[0].plot(x/1000.,dx)
  ax[1].plot(y/1000.,dy)
  #xlim([-50,50])
  fig.savefig(outdir+'/figs/dx.png')

  ######## Bathy ############
  # get the topo:
  xd = np.array([0, 3, 300, 10000])
  dd = np.array([0, fjordD, fjordD, 200])
  d = np.zeros((ny,nx))
  d0 = np.interp(x, xd*1000, -dd)
  d = d + d0



  np.random.seed(20220610)
  nwave = 100000
  xwave = np.linspace(0, x[-1]+1000, nwave)
  wavybot = np.cumsum(np.random.randn(nwave))
  wavybot = np.interp(x, xwave, wavybot)
  for xr in np.arange(0, x[-1], 100e3):
    ind = np.nonzero((x>=xr) & (x<xr+100e3))
    if xr <= 230e3:
      wavybot[ind] -= np.min(wavybot[ind])
      wavybot[ind] = wavybot[ind] / np.max(wavybot[ind]) * 0
    else:
      wavybot[ind] -= np.min(wavybot[ind])
      wavybot[ind] = wavybot[ind] / np.max(wavybot[ind]) * 20


  wavytop = np.cumsum(np.random.randn(nwave))
  wavytop = np.interp(x, xwave, wavytop)
  for xr in np.arange(0, x[-1], 100e3):
    ind = np.nonzero((x>=xr) & (x<xr+100e3))
    if xr <= 230e3:
      wavytop[ind] -= np.min(wavytop[ind])
      wavytop[ind] = wavytop[ind] / np.max(wavytop[ind]) * 0
    else:
      wavytop[ind] -= np.min(wavytop[ind])
      wavytop[ind] = wavytop[ind] / np.max(wavytop[ind]) * 20

  #if not wavey:
  #  wavytop = 0 * wavytop
  #  wavybot = 0 * wavytop

  for ind in range(nx):
    topshape = [fjordW/2 / 1e3, fjordW/2 / 1e3, y[-1]/1000, y[-1]/1000]  # in km
    xtop = [0, fjordL, fjordL+40e3, 10000e3]
    top = np.interp(x[ind], xtop, topshape)

    yd = np.array([-top + wavybot[ind], -top + wavybot[ind]+0.5,
                  top-0.5 - wavybot[ind], top - wavybot[ind]])
    dd = np.array([0, 1, 1, 0])
    y0 = np.interp(y, yd*1000, dd)
    d[:, ind] = d[:, ind] * y0

  print(np.shape(x))
  indx = np.nonzero(x > fjordL+50e3)[0]
  print(np.shape(indx))
  d[:, indx] += np.random.rand(ny, len(indx)) * 20
  d[d>0] = 0

  d[:, -1] = 0
  # wall West side:
  d[:, 0] = 0
  # put a N/S wall...
  d[0, :] = 0

  print(np.nonzero(~np.isfinite(d)))
  print(d[~np.isfinite(d)])

  with open(indir+"/topog.bin", "wb") as f:
    d.tofile(f)
  f.close()


  _log.info(np.shape(d))

  fig, ax = plt.subplots(2,1)
  _log.info('%s %s', np.shape(x), np.shape(d))
  print(y)
  ax[0].plot(x/1.e3,d[int(ny/2),:].T)
  pcm=ax[1].pcolormesh(x/1.e3,y/1.e3,d,rasterized=True)
  #ax[1].set_xlim([0, 200])
  #ax[1].set_ylim([0, 4])
  fig.colorbar(pcm,ax=ax[1])
  fig.savefig(outdir+'/figs/topo.png')

  ##################
  # dz:
  # dz is from the surface down (right?).  Its saved as positive.

  dz = np.ones(nz) * 2.5
  maxz = 0
  a = 1.04
  z=np.cumsum(dz)

  while z[-1] < 200:
    a = a + 0.01
    for ind in range(48, nz):
      dz[ind] = dz[ind-1] * a
    z=np.cumsum(dz)
  dz[-1] -= z[-1] - 200
  print(dz)
  z=np.cumsum(dz)

  # for i in range(115, nz):
  #    dz[i] = dz[i-1] * 1.03

  with open(indir+"/delZ.bin", "wb") as f:
    dz.tofile(f)
  f.close()
  print(z)
  fig, ax = plt.subplots()
  ax.plot(z, dz)
  fig.savefig(outdir+'/figs/dz.png')

  ####################
  # temperature profile...
  #
  # temperature goes on the zc grid:
  df = pd.read_csv('TempSal.csv')
  T0 = 8 + np.ones(nz)
  zs = np.array([0, 5, 20, 50, 100, 200, 500, 600])
  ts = np.array([7.4, 7.4, 7.4, 7.9, 8.0, 8.3, 8.06, 8.06])
  T0 = np.interp(z, zs, ts)

  T0[z<220] = np.interp(z[z<220], df.Depth, df.Temperature)
  try:
    T0[z>=220] = T0[z<220][-1]
  except IndexError:
    pass

  if NsqConstant or NsqExp:
    T0 = T0 * 0 + 8.9

  with open(indir+"/TRef.bin", "wb") as f:
    T0.tofile(f)
  print(T0)

  #plot
  plt.clf()
  plt.plot(T0,z)
  plt.savefig(outdir+'/figs/TO.png')

  Temp = np.broadcast_to(T0[:, np.newaxis, np.newaxis], (nz, ny, nx ))


  if NsqConstant or NsqExp:
    if False:

      inx = x<100e3
      T0 = T0 * 0 + 20.0
      T0[:, :, inx] = 10.0
    else:
      # constant
      T0 = 0 * T0 + 8.9
      Temp = 0 * Temp + 8.9


  print(np.shape(Temp))
  with open(indir+"/TInit.bin", "wb") as f:
    Temp.tofile(f)
  f.close()



  #########################
  # salinity profile...
  #
  # FRom
  if (not NsqConstant) and (not NsqExp) :
    s = np.array([15, 15, 29.1, 29.6, 30.1, 30.6, 30.66, 30.66])
    S0 =  30.6 - 15*np.exp(-z / 20)

    S0 = np.interp(z, zs, s)

    S0[z<220] = np.interp(z[z<220], df.Depth, df.Salinity)
    try:
      S0[z>=220] = S0[z>=220] - S0[z>=220][0] + S0[z<220][-1]
    except IndexError:
      pass
  elif NsqExp:
    print(z)
    Nsq = np.exp((-z)/ NsqScale)
    Nsq = Nsq * fjordD / NsqScale / (1 - np.exp(-fjordD / NsqScale)) * Nsq0
    print('Total: ', np.sum(Nsq*dz) / np.sum(dz))
    S0 = 20 + np.cumsum(Nsq / sBeta / 9.81 * dz)
  else:
    # constant Nsq case
    S0 = 20 + z * Nsq0 / sBeta / 9.81
    # make gradient larger if Nsqfac....
    S0 = S0[0] + (S0 - S0[0])


  with open(indir+"/SRef.bin", "wb") as f:
    S0.tofile(f)
  print(S0)

  plt.clf()
  plt.plot(S0, z)

  plt.savefig(outdir+'/figs/SO.png')

  S = np.broadcast_to(S0[:, np.newaxis, np.newaxis], (nz, ny, nx ))

  with open(indir+"/SInit.bin", "wb") as f:
    S.tofile(f)

  ############################
  # external wind stress
  nt = 24  # days
  Cd = 1e-3
  taumax = Cd * uw**2  # N/m^2
  t = np.arange(nt*1.0)  # days
  taut = 0 * t

  if initial:
    taut[t<=24] = np.arange(25) * taumax
    taut[(t>24) & (t<((duration + 1)*24))] = taumax
    taut[(t>=(duration + 1)*24) & (t<(duration + 2)*24)] = np.arange(23, -1, -1) / 24 * taumax
  else:
    taut = taut * 0 + taumax

  taux = np.exp(-x/30000)
  taux = 0.5 - np.tanh((x-windL)/(windL / 2))/2

  taux = np.broadcast_to(taux[np.newaxis, :], (ny, nx))
  tt = taux.copy()
  # set tau =0 outside width of fjord (to stop whole basin from getting a wind.)
  for yind in range(ny):
    if np.abs(y[yind])>fjordW+2000:
      tt[yind, :] = 0.0
  # zero outside of fjordL:
  for xind in range(nx):
    if np.abs(x[xind])>fjordL+2000:
      tt[:, xind] = 0.0


  if True:
    print(taux)
    tau = taut[:, np.newaxis, np.newaxis] * tt[np.newaxis, ...]
    print(np.shape(tau))
    fig, ax = plt.subplots(2, 1)
    pc = ax[0].pcolormesh(x, t,  tau[:, 2, :], rasterized=True, vmin=-taumax, vmax=taumax, cmap='RdBu_r')
    ax[1].pcolormesh(x, y,  tau[2, :, :], rasterized=True, vmin=-taumax, vmax=taumax, cmap='RdBu_r')
    fig.colorbar(pc, ax=ax)
    fig.savefig(outdir+'/figs/Tau.png')
  else:
    tau = taux * taumax
    fig, ax = plt.subplots(2, 1)
    # pc = ax[0].pcolormesh(x, t,  tau[:, :], rasterized=True, vmin=-taumax, vmax=taumax, cmap='RdBu_r')
    pc = ax[1].pcolormesh(x, y, tau[:, :], rasterized=True, vmin=-taumax, vmax=taumax, cmap='RdBu_r')
    fig.colorbar(pc, ax=ax)
    fig.savefig(outdir+'/figs/Tau.png')



  with open(indir+'taux.bin', 'wb') as f:
      tau.tofile(f)

  if False:
    ################################
    # external heat flux
    Qnetmax = 500
    Q = tau / taumax * Qnetmax

    with open(indir+'Qnet.bin', 'wb') as f:
        Q.T.tofile(f)

  ###################################
  # RBCS sponge
  if False:
    weight = np.zeros((nz, ny, nx))
    weight[..., -100:] = np.linspace(0, 1, 100)**1.5
    # print(weight)
    with open(indir+'spongeweight.bin', 'wb') as f:
        weight.tofile(f)

    # force to zero velocity to prevent reflections.
    # note that we also force T and S to Tinit and Sinit
    weight = np.zeros((nz, ny, nx))
    with open(indir+'Uforce.bin', 'wb') as f:
        weight.tofile(f)

    weight = np.zeros((nz, ny, nx))
    with open(indir+'Vforce.bin', 'wb') as f:
        weight.tofile(f)

  #### Initial O2
  O2 = np.zeros((nz, ny, nx))

  if not NsqConstant:
    O2 = np.zeros((nz, ny, nx))

    O2z = np.interp(z, [0, 25, 120, 150, 1000], [7, 5, 2, 2.7, 2.7]) / 22.4 * 1e3  # umol/kg
    O2 = O2 + O2z[:, np.newaxis, np.newaxis]
  else:
    O2Sat = o2sat(T0, S0)
    satprofile = [100, 50, 50]
    satprofile = [50, 50, 50]
    zsat = [0, 30, 500]
    O2z = np.interp(z, zsat, satprofile) * O2Sat / 100
    O2 = O2 * 0 + O2z[:, np.newaxis, np.newaxis]

  with open(indir+'O2.bin', 'wb') as f:
    O2.tofile(f)
  with open(indir+'O2n.bin', 'wb') as f:
    O2.tofile(f)



  fig, ax = plt.subplots()
  ax.plot(O2z, z)
  fig.savefig(outdir+'/figs/O2.png')

  ### Initial passive tracer
  inx = x<100e3
  O2 = O2 * 0 + 20.0
  O2[:, :, inx]= 10.0

  with open(indir+'Passive.bin', 'wb') as f:
      O2.tofile(f)


  _log.info('All Done!')

  _log.info('Archiving to home directory')

  try:
      shutil.rmtree('../archive/'+runname)
  except:
      pass

  shutil.copytree(outdir0+'/input/', '../archive/'+runname+'/input')
  shutil.copytree(outdir0+'/python/', '../archive/'+runname+'/python')
  shutil.copytree(outdir0+'/code', '../archive/'+runname+'/code')

  _log.info('doing this via git!!')

  os.system(f'git commit -a -m "gendata for {runname}: {comments}"')
  os.system('git push origin main')
  os.system(f'git checkout -B {runname}')
  os.system(f'git push origin {runname}')
  os.system('git checkout main')


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument('--NsqFac', nargs='?', const=1.0, type=float)
  parser.add_argument('--wind', nargs='?', const=20.0, type=float)
  parser.add_argument('--runnumber', type=int)
  parser.add_argument('--windL', nargs='?', const=60.0e3, type=float)
  parser.add_argument('--fjordL', nargs='?', const=180.0e3, type=float)
  parser.add_argument('--fjordD', nargs='?', const=200, type=float)
  parser.add_argument('--endTime', nargs='?', const=1_036_800, type=float)
  parser.add_argument('--NsqScale', nargs='?', const=None, type=float)

  args = parser.parse_args()

  if not args.runnumber:
    raise RuntimeError('must specify a runnumber')

  gendata(args.runnumber, NsqFac=args.NsqFac, wind=args.wind,
          windL=args.windL, fjordL=args.fjordL, fjordD=args.fjordD,
          NsqScale=args.NsqScale)

