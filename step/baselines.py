# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/source/03_baselines.ipynb.

# %% auto 0
__all__ = ['tamsd', 'diffusion_coefficient_tamsd', 'anomalous_exponent_tamsd', 'hull_diameter', 'convex_hull_cp', 'ruptures_cp']

# %% ../nbs/source/03_baselines.ipynb 2
import numpy as np
import ruptures as rpt
from fastcore.all import *
from scipy.spatial import ConvexHull
from fastai.torch_core import Tensor, tensor

# %% ../nbs/source/03_baselines.ipynb 4
def tamsd(
    x:Tensor,  # Input trajectory of shape [length, dim]
    dt:int=1   # t-lag: time interval to compute displacements
    )-> float:
    "Time-averaged mean squared displacement of a trajectory `x` in `dt` intervals."
    return (x[dt:] - x[:-dt]).pow(2).sum(-1).mean()


# %% ../nbs/source/03_baselines.ipynb 6
def diffusion_coefficient_tamsd(
    x:Tensor,                # Input trajectory of shape [length, dim]  
    t_lag:Iterable=[2, 3, 4] # t-lags to consider for the fit
    )->float:                # Diffusion coefficient
    "Estimates the diffusion coefficient fitting the `tmsd` for different `dt`."
    tmsds = [tamsd(x, dt) for dt in t_lag]
    D = np.polyfit(t_lag, tmsds, 1)[0]
    return D/(2*x.shape[-1])

def anomalous_exponent_tamsd(
    x:Tensor,         # Input trajectory of shape [length, dim]
    t_lag:Iterable=[] # t-lags to consider. Defautls to [2,...,max(5, 10% length)]
    )->float:         # Anomalous exponent
    "Estimates the anomalous exponent fitting the `tmsd` in log-log scale for different t-lags."
    if len(t_lag) == 0: t_lag = np.arange(2, max(5, int(0.1*x.shape[0])))
    tmsds = [tamsd(x, dt) for dt in t_lag]
    return np.polyfit(np.log(t_lag), np.log(tmsds), 1)[0]

# %% ../nbs/source/03_baselines.ipynb 17
def hull_diameter(hull):
    "Diameter of the local convex hull."
    max_diff = hull.max_bound - hull.min_bound
    return np.sqrt(np.dot(max_diff, max_diff))

# %% ../nbs/source/03_baselines.ipynb 18
def convex_hull_cp(
    traj:np.ndarray,    # Trajectory to study
    tau:int=10,         # Size of the sliding window
    method:str="volume" # Property of interest: "volume" or "diameter"
    )->np.ndarray:      # Changepoints along the trajectory
    "Detect the changepoints in `traj` with the local convex hull method."
    if (method != "volume") and (method != "diameter"):
        raise ValueError(f"Invalid method {method}, it should be either 'volume' or 'diameter'.")
    max_t = traj.shape[0] - 2*tau
    S = np.zeros(max_t)
    hull_prop = hull_diameter if method == "diameter" else lambda x: x.volume
    for t in range(max_t):   
        hull = ConvexHull(traj[t:(t+2*tau)])
        S[t] = hull_prop(hull)
    S -= S.mean()
    return np.argwhere(S[1:]*S[:-1] < 0)
    

# %% ../nbs/source/03_baselines.ipynb 32
@delegates(rpt.KernelCPD)
def ruptures_cp(
    x:np.ndarray,  # Input signal with shape [length, dim]
    pen:float=1.,  # Penalty for the changepoint prediction
    **kwargs
    )->np.ndarray: # Changepoints along the trajectory
    "Returns the change points of signal `x`, excluding the initial and final times."
    alg = rpt.KernelCPD(**kwargs).fit(x)
    return alg.predict(pen=pen)[:-1]
