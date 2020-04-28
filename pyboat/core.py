###########################################################################
# Tools for time-frequency analysis with Morlet Wavelets
# Inspired by 'A Practical Guide to Wavelet Analysis' from Torrence
# and Compo 1998
# and 'Identification of Chirps with Continuous Wavelet Transform'
# from Carmona,Hwang and Torresani 1995
#
# Version 0.7 March 2020, Gregor Moenke (gregor.moenke@embl.de)
###########################################################################

import numpy as np
from numpy.fft import rfft, rfftfreq, fft
from numpy.random import uniform, randn, randint, choice
from numpy import pi
from scipy.signal import savgol_filter
import pandas as pd

# global variables
# -----------------------------------------------------------
omega0 = 2 * pi  # central frequency of the mother wavelet
xi2_95 = 5.99
xi2_99 = 9.21

# clip Wavelets at 1/peak_fraction envelope
peak_fraction = 1e6
clip_support = True
# -----------------------------------------------------------


def compute_spectrum(signal, dt, periods):

    """

        Computes the Wavelet spectrum for a given *signal* for the given *periods*
        
        signal  : a sequence
        the time-series to be analyzed, detrend beforehand!
        dt      : the sampling interval scaled to desired time units
        periods : the list of periods to compute the Wavelet spectrum for, 
              must have same units as dt!


        returns:

        modulus : the Wavelet power spectrum normalized by signal variance
        wlet : the Wavelet transform with dimensions len(periods) x len(signal) 
        
        """

    if periods[0] < 2 * dt:
        print()
        print(f"Warning, Nyquist limit is {2*dt:.2f}!!")
        print()

    # -- subtract the mean --
    signal = np.array(signal) - np.mean(signal)

    periods = np.array(periods)
    dt = float(dt)
    sfreq = 1 / dt  # the sampling frequency

    Nt = len(signal)  # number of time points

    # --------------------------------------------
    scales = scales_from_periods(periods, sfreq, omega0)
    # --------------------------------------------

    # mx_per = 4*len(signal)/((omega0+sqrt(2+omega0**2))*sfreq)
    mx_per = dt * len(signal)
    if max(periods) > mx_per:

        print()
        print("Warning: Very large periods chosen!")
        print("Max. period should be <", np.rint(mx_per))
        print("proceeding anyways...")

    Morlet = mk_Morlet(omega0)
    wlet = CWT(signal, Morlet, scales)  # complex wavelet transform
    sig2 = np.var(signal)  # white noise has then mean power of one
    modulus = np.abs(wlet) ** 2 / sig2  # normalize with variance of signal

    return modulus, wlet


def get_maxRidge(modulus):

    """

        returns: 

        ridge_y  : the y-coordinates of the ridge

        """
    Nt = modulus.shape[1]  # number of time points

    # ================ridge detection============================================

    # just pick the consecutive modulus (squared complex wavelet transform)
    # maxima as the ridge

    ridge_y = np.array([np.argmax(modulus[:, t]) for t in np.arange(Nt)], dtype=int)

    return ridge_y


def eval_ridge(ridge_y, wlet, signal, periods, tvec, power_thresh=0, smoothing_wsize=None):

    """
    
    Given the ridge y-coordinates, evaluates the spectrum along  
    the time axis and returns a DataFrame containing:

    Returns
    -------

    time      : the t-values of the ridge, can have gaps if thresholding!
    periods   : the instantaneous periods 
    frequencies : the instantaneous frequencies 
    phases    : the arg(z) values
    power     : the Wavelet Power normalized to white noise (<P(WN)> = 1)
    amplitude : the estimated amplitudes of the signal
    (z        : the (complex) z-values of the Wavelet along the ridge) 
                not attached as redundant

    smoothing_wsize: optional, Savitkzy-Golay smoothing of the ridge

    """


    
    sigma2 = np.var(signal)
    modulus = np.abs(wlet) ** 2 / sigma2  # normalize with variance of signal

    # calculate here to minimize arguments needed
    dt = tvec[1] - tvec[0]

    Nt = modulus.shape[1]  # number of time points

    ridge_per = periods[ridge_y]
    ridge_z = wlet[ridge_y, np.arange(Nt)]  # picking the right t-y values !

    ridge_power = modulus[ridge_y, np.arange(Nt)]

    inds = (
        ridge_power > power_thresh
    )  # boolean array of positions exceeding power threshold
    sign_per = ridge_per[inds]  # periods which cross the power threshold
    ridge_t = tvec[inds]
    ridge_phi = np.angle(ridge_z)[inds] % (2 * pi)  # map to [0,2pi]
    sign_power = ridge_power[inds]
    sign_amplitudes = power_to_amplitude(sign_per, sign_power, np.sqrt(sigma2), dt)

    # sign_z = ridge_z[inds] # not needed

    if smoothing_wsize is not None:
        Ntt = len(ridge_per)
        
        # sanitize ridge smoothing window size
        if Ntt < smoothing_wsize:
            # need an odd window size
            smoothing = Ntt if Ntt % 2 == 1 else Ntt - 1

        # smoothed maximum estimate of the whole ridge..
        sign_per = savgol_filter(ridge_per, smoothing_wsize, polyorder = 3)[inds]


    # set index as time!    
    ridge_data = pd.DataFrame(
        columns=['time', 'periods', 'phase', 'amplitude', 'power', 'frequencies'],
    )

    ridge_data['time'] = ridge_t    
    ridge_data['phase'] = ridge_phi
    ridge_data['power'] = sign_power
    ridge_data['amplitude'] = sign_amplitudes
    ridge_data['periods'] = sign_per
    ridge_data['frequencies'] = 1 / sign_per


    MaxPowerPer = ridge_per[np.nanargmax(ridge_power)]  # period of highest power on ridge

    return ridge_data


def find_COI_crossing(rd):

    '''
    checks for last/first time point
    which is outside the COI on the
    left/right boundary of the spectrum.

    Parameters
    ----------

    rd : pandas.DataFrame
        the ridge data from eval_ridge()
    '''

    coi_left = Morlet_COI() * rd.time
    # last time point outside left COI
    t_left = rd.index[~(coi_left > rd.periods)][-1]

    # use array to avoid inversed indexing
    coi_right = Morlet_COI() * rd.time.array[::-1]
    # first time point outside right COI
    t_right = rd.index[(coi_right < rd.periods)][0]
    
    return t_left, t_right


# ============ Snake Annealing =====================================


def find_ridge_anneal(landscape, y0, T_ini, Nsteps, mx_jump=2, curve_pen=0):

    """ 
    Taking an initial straight line guess at *y0* finds a ridge in *landscape* which 
    minimizes the cost_func_anneal by the simulated annealing method.

    landscape - time x scales signal representation (modulus of Wavelet transform)
    y0        - initial ridge guess is straight line at scale landscape[y0] 
                -> best to set it close to a peak in the Wavelet modulus (*landscape*)
    T_ini     - initial value of the temperature for the annealing method
    Nsteps    - Max. number of steps for the algorithm
    mx_jump   - Max. distance in scale direction covered by the random steps
    curve_pen - Penalty weight for the 2nd derivative of the ridge to estimate -> 
                high values lead to  less curvy ridges

    """

    print()
    print("started annealing..")

    incr = np.arange(-mx_jump, mx_jump + 1)  # possible jumps in scale direction
    incr = incr[incr != 0]  # remove middle zero

    Nt = landscape.shape[-1]  # number of time points
    Ns = landscape.shape[0]  # number of scales
    t_inds = np.arange(Nt)
    ys = y0 * np.ones(
        Nt, dtype=int
    )  # initial ridge guess is straight line at scale landscape[y0]

    Nrej = 0

    tfac = 0.01  # still arbitrary :/
    T_ini = T_ini * tfac
    curve_pen = curve_pen * tfac

    T_k = T_ini  # for more natural units ->  0 < T_ini < 100 should be ok

    for k in range(Nsteps):

        F = cost_func_anneal(ys, t_inds, landscape, 0, curve_pen)

        pos = randint(
            0, len(ys), size=1
        )  # choose time position to make random scale jump

        # dealing with the scale domain boundaries
        if ys[pos] >= Ns - mx_jump - 1:
            eps = -1

        elif ys[pos] < mx_jump:
            eps = +1

        # jump!
        else:
            eps = choice(incr, size=1)

        ys[pos] = ys[pos] + eps  # the candidate

        F_c = cost_func_anneal(ys, t_inds, landscape, 0, curve_pen)

        accept = True

        # a locally non-optimal move occured
        if F_c > F:
            u = uniform()

            # reject bad move? exp(-(F_c - F)/T_k) is (Boltzmann) probability for bad move to be accepted
            if u > np.exp(-(F_c - F) / T_k):
                accept = False

        if not accept:
            ys[pos] = ys[pos] - eps  # revert the wiggle
            Nrej += 1

        if accept:
            Nrej = 0

        print(T_k)
        T_k = T_ini / np.log(2 + k)  # update temperature

    print()
    print("annealing done!")
    print("final cost:", F_c)
    print("number of final still steps:", Nrej)
    print("final temperature:", T_k * tfac)
    return ys, F_c


def cost_func_anneal(ys, t_inds, landscape, l, m):

    """
    Evaluates ridge candidate *ys* on *landscape* plus penalizing terms
    for 1st (*l*) and 2nd (*m*) derivative of the ridge curve.
    """

    N = len(ys)
    D = -sum(landscape[ys, t_inds])
    S1 = l * sum(abs(np.diff(ys, 1)))
    S2 = m * sum(abs(np.diff(ys, 2)))

    # print D,S1,S2,D + S1 + S2

    return (D + S1 + S2) / N


# =============== Filters +  Detrending =================================


def smooth(x, window_len=11, window="flat", data=None):
    """
    smooth the data using a window with requested size.

    input:
    x: the input signal
    window_len: the dimension of the smoothing window; should be an odd integer
    window: the type of window from 'flat' or 'extern'

    flat window will produce a moving average smoothing.
    data: if not None, will be used as evaluated window!

    """

    x = np.array(x)

    # use externally derieved window evaluation
    if data is not None:
        window_len = len(data)
        window = "extern"

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len < 3:
        raise ValueError("window must not be shorter than 3")

    if window_len % 2 is 0:
        raise ValueError("window_len should be odd")

    if not window in [
        "flat",
        "extern"
    ]:
        raise ValueError(
            "Window is none of 'flat' or 'extern'"
        )

    s = np.r_[x[window_len - 1 : 0 : -1], x, x[-1:-window_len:-1]]
    # print(len(s))
    if window == "flat":  # moving average
        w = np.ones(window_len, "d")

    elif window == "extern":
        w = data

    else:
        w = eval(window + "(window_len)")

    y = np.convolve(w / w.sum(), s, mode="valid")

    return y[int((window_len - 1) / 2) : len(y) - int((window_len - 1) / 2)]


def sinc_filter(M, f_c=0.2):

    """ 
    Cutoff frequency f_c in sampling frequency unit, max 0.5!
    M is blackman window length and must be even, output length will be M+1.

    """

    # not very effective, but should be get called only once per convolution

    assert M % 2 == 0, "M must be even!"
    res = []

    for x in np.arange(0, M + 1):

        if x == M / 2:
            res.append(2 * pi * f_c)
            continue

        r = np.sin(2 * pi * f_c * (x - M / 2)) / (
            x - M / 2
        )  # the sinc filter unwindowed
        r = r * (
            0.42 - 0.5 * np.cos(2 * pi * x / M) + 0.08 * np.cos(4 * pi * x / M)
        )  # blackman window
        res.append(r)

    res = np.array(res)
    res = res / np.sum(res)

    return res


def sinc_smooth(raw_signal, T_c, dt, M=None):

    '''
    Convolve the signal with a sinc filter
    of cut-off period *T_c*.

    Length of the filter controlled by
    M, defaults to length of the raw_signal
    '''

    signal = np.array(raw_signal)
    dt = float(dt)

    # relative cut_off frequency
    f_c = dt / T_c

    if M is None:

        M = len(signal) - 1  # max for sharp roll-off

        # M needs to be even
        if M % 2 != 0:
            M = M - 1

    w = sinc_filter(M, f_c)  # the evaluated windowed sinc filter
    sinc_smoothed = smooth(signal, data=w)

    return sinc_smoothed

def sliding_window_amplitude(signal, window_size, SGsmooth = True):

    '''
    Max - Min sliding window operation
    to estimate amplitude envelope.

    free boundaries -> half the window_size + 1
    at 1st and last entry

    optional:
    Savitzky-Golay smoothing of the
    envelope with the same window size
    '''

    # get the underlying array
    vector = np.array(signal)
    
    # has to be odd
    if window_size % 2 != 1:
        window_size = window_size + 1

    # rolling matrix
    # Stack Overflow move
    shape = vector.shape[:-1] + (vector.shape[-1] - window_size + 1, window_size)
    strides = vector.strides + (vector.strides[-1],)
    aa = np.lib.stride_tricks.as_strided(vector, shape=shape, strides=strides)

    # treat the boundaries, fill with NaNs 
    b_size = window_size // 2
    b_left = np.zeros((b_size, aa.shape[1]), dtype=float) * np.nan
    b_right = np.zeros((b_size, aa.shape[1]), dtype=float) * np.nan

    for i in range(b_size):
        b_left[i, :b_size + i + 1] = vector[:b_size + 1 + i]
        b_right[-(i + 1), -(b_size + 1 + i):] = vector[-(b_size + 1 + i):]

    rm = np.vstack([b_left, aa, b_right])

    # max-min/2 in sliding window
    amplitudes = (np.nanmax(rm, axis=1) - np.nanmin(rm, axis=1)) / 2

    if SGsmooth:
        amplitudes = savgol_filter(amplitudes,
                                   window_length = window_size,
                                   polyorder = 3)
    
    return amplitudes

def normalize_with_envelope(dsignal, window_size):

    '''
    Best to use detrending beforehand!

    Mean subtraction is still always performed.

    Does NOT check for zero-divide errors,
    arrising in cases where the signal is constant.
    '''

    # mean subtraction
    signal = dsignal - dsignal.mean()
    
    # ampl. normalization
    env = sliding_window_amplitude(signal, window_size )
    ANsignal = 1/env * dsignal

    return ANsignal



# =============WAVELETS=====================================================


def scales_from_periods(periods, sfreq, omega0=2 * pi):
    # conversion from periods to morlet scales
    # strictly admissable version from Torrence-Compo
    scales = (omega0 + np.sqrt(2 + omega0 ** 2)) * periods * sfreq / (4 * pi)
    return scales

def scales_from_periodsNA(periods, sfreq, omega0=2 * pi):
    # conversion from periods to morlet scales
    # fits the non-admissable Morlet definition!
    scales = omega0 * periods * sfreq / (2 * pi)
    return scales


# is normed to have unit energy on all scales! ..to be used with CWT underneath
def mk_Morlet(omega0):
    def Morlet(t, scale):
        res = (
            pi ** (-0.25)
            * np.exp(omega0 * 1j * t / scale)
            * np.exp(-0.5 * (t / scale) ** 2)
        )
        return 1 / np.sqrt(scale) * res

    return Morlet


def gauss_envelope(t, scale):

    """
    The gaussian envelope of the Morlet Wavelet
    """

    return 1 / np.sqrt(scale) * pi ** (-0.25) * np.exp(-0.5 * (t / scale) ** 2)


def inverse_gauss(y, scale):

    """
    Invert the right Gaussian branch to
    determine Morlet support cut off 
    """

    a = pi ** (-0.25) * 1 / np.sqrt(scale)
    return scale * np.sqrt(-2 * np.log(y / a))


# allows for complex wavelets, needs scales scaled with sampling freq!
def CWT(signal, wavelet, scales, clip_support=clip_support):

    # test for complexity
    if np.iscomplexobj(wavelet(10, 1)):
        output = np.zeros([len(scales), len(signal)], dtype=complex)
    else:
        output = np.zeros([len(scales), len(signal)])

    # we want to take always the maximum support available
    # .. no we don't -> performance, otherwise convolutions scale with N * N!!
    # vec = np.arange(-len(signal)/2, len(signal)/2) # old default

    for ind, scale in enumerate(scales):

        # Morlet main peak value:
        y0 = gauss_envelope(0, scale)

        if clip_support:
            # support cut off at 1/peak_fraction of Morlet peak
            x_max = int(inverse_gauss(y0 / peak_fraction, scale))
        else:
            x_max = len(signal) / 2

        # print(ind, scale, 2*x_max)

        # max support is length of signal
        if 2 * x_max > len(signal):
            vec = np.arange(-len(signal) / 2, len(signal) / 2)

        else:
            vec = np.arange(-x_max, x_max)

        wavelet_data = wavelet(vec, scale)
        output[ind, :] = np.convolve(signal, wavelet_data, mode="same")
    return output


def Morlet_COI(omega0=omega0):
    # slope of Morlet e-folding time in tau-periods (spectral) view
    m = 4 * pi / (np.sqrt(2) * (omega0 + np.sqrt(2 + omega0 ** 2)))
    return m


def power_to_amplitude(periods, powers, signal_std, dt):

    """
    Rescale Morlet wavelet powers according to the
    definition of 

    "On the Analytic Wavelet Transform",
    Jonathan M. Lilly 2010

    to get an amplitude estimate.
    """

    scales = scales_from_periods(periods, 1 / dt)
    
    kappa = 1 / np.sqrt(scales) * pi**-0.25
    kappa = kappa * signal_std * np.sqrt(2)

    return np.sqrt(powers) * kappa


# ===== Fourier FFT Spectrum ================================================


def compute_fourier(signal, dt):

    N = len(signal)

    df = 1.0 / (N * dt)  # frequency bins

    rf = rfft(signal, norm="ortho")  # positive frequencies
    # use numpy routine for sampling frequencies
    fft_freqs = rfftfreq(len(signal), d=dt)

    # print(N,dt,df)
    # print(len(fft_freqs),len(rf))

    fpower = np.abs(rf) ** 2 / np.var(signal)

    return fft_freqs, fpower


# ============== AR1 spectrum and simulation =============


def ar1_powerspec(alpha, periods, dt):
    res = (1 - alpha ** 2) / (1 + alpha ** 2 - 2 * alpha * np.cos(2 * pi * dt / periods))

    return res


def ar1_sim(alpha, N, sigma = 1, x0=None):

    N = int(N)
    sol = np.zeros(N)

    if x0 is None:
        x0 = randn()

    sol[0] = x0

    for i in range(1, N):
        sol[i] = alpha * sol[i - 1] + sigma * randn()

    return sol
