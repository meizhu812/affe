import numpy as np
from math import log
from scipy.special import gamma
from res.functions import func_phi_m, func_phi_c, func_psi_m, const_kar


footprint_grid = np.zeros((100, 100))
n_x = n_y = 0
x_max = y_max = f_max = 0


def read_grd_data(grd_path):
    with open(grd_path, 'r') as f:
        heads = []  # first 5 lines of grd file
        for n in range(5):
            heads.append(f.readline())
        nx, ny = map(int, heads[1].split())
        data_fracs = []
        while True:
            line = f.readline()
            if not line:  # end of file
                break
            data_fracs.append(np.fromstring(line, sep=' ', dtype='f4'))
    return np.concatenate(data_fracs).reshape(nx, ny)

class FPCalculator:
    def calc_fp(self, z_m, z_0, date_time, wind_dir, wind_spd, sigma_v, u_star, L, h_s, rho_air):
        if abs(L) < z_0:
            L = (z_0 + 0.5) * np.sign(L)

        u = max(u_star / const_kar * (log(z_m / z_0)
                                - func_psi_m(z_m / L)
                                + func_psi_m(z_0 / L)),
                u_star)

        m = u_star / const_kar * func_phi_m(z_m / L) / u

        n = 1 / (1 + 5 * z_m / L) if L > 0 else (1 - 24 * z_m / L) / (1 - 16 * z_m / L)

        u_const = u / (z_m ** m)

        k_const = const_kar * u_star / func_phi_c(z_m / L) * (z_m ** (1 - n))

        r = 2 + m - n

        mu = (1 + m) / r


        A = r * gamma(2 / r) / gamma(1 / r) ** 2
        B =gamma(2 / r) / gamma(1 / r)
        z_bar_cof = B * (r ** 2 * const_kar / u_const) ** (1 / r)
        z_bar_exp = 1 / r
        u_bar_cof = gamma(mu) / gamma(1 / r) * (r ** 2 * k_const / u_const) ** (m / r) * u_const
        u_bar_exp = m / r

    def z_bar(x, B, r, k, U):
        return B * (x ** (1 / r))


def output_fp_grd(grd_conf, output_path):
    with open(output_path, mode='w') as output_file:
        output_file.write('DSAA\n'
                          f'{grd_conf.n_x} {grd_conf.n_y}\n'
                          f'0 {grd_conf.x_max}\n'
                          f'0 {grd_conf.y_max}\n'
                          f'0 {grd_conf.f_max}\n')


def read_met_data(met_data_path):
    with open(met_data_path, mode='r') as met_data_file:
        met_data = met_data_file.readlines()
        for met_datum in met_data[1:]:  # skip first line
            date_time, wind_dir, wind_spd, sigma_v, u_star, obukhov_l, h_s, rho_air, key = met_datum.split()


def read_site_conf(site_param_path, site_locs_path):
    with open(site_param_path, mode='r') as site_param_file:
        z_m, z_0 = site_param_file.readline().split(',')[:2]
        x_max, y_max, dx = site_param_file.readline().split(',')[:3]
    with open(site_locs_path) as site_locs_file:
        site_locs = [site_loc.split(',') for site_loc in site_locs_file.readlines()]
    return z_m, z_0, x_max, y_max, dx, site_locs



    if __name__ == '__main__':
        read_met_data(
            r'D:\Truman\Desktop\present_work\01_ammonia\00_general\03_tools\footprint\footprint\01\02metdata.dat')
        read_site_conf('01paras.dat', '')
