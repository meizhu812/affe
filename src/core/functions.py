from math import log, atan, pi
from scipy.special import gamma

const_kar = 0.4


def func_phi_m(z_div_L):
    if z_div_L > 0:
        return 1 + 5 * z_div_L
    else:
        return (1 - 16 * z_div_L) ** (-1 / 4)


def func_phi_c(z_div_L):
    if z_div_L > 0:
        return 1 + 5 * z_div_L
    else:
        return (1 - 16 * z_div_L) ** (-1 / 2)


def func_xi(z_div_L):
    return (1 - 16 * z_div_L) ** (1 / 4)


def func_psi_m(z_div_L):
    if z_div_L > 0:
        return -5 * z_div_L

    else:
        return 2 * log((1 + func_xi(z_div_L)) / 2) + log((1 + func_xi(z_div_L) ** 2) / 2) - 2 * atan(func_xi(z_div_L)) + pi / 2

def kormaanf(u_star, L, z_m, x_range, z_0):
    kar = 0.35
    #k0=k
	#zm=zmm
    u=u_star













