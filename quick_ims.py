import matplotlib.pyplot as plt
# from matplotlib.patches import Ellipse
import numpy as np
import os
from astropy.io import fits
from matplotlib.ticker import AutoMinorLocator
import matplotlib

matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'
matplotlib.rcParams['font.size'] = 18

os.chdir("/Users/thomaswilliams/Documents/wisdom/alma/ngc4526")

files = [
    "ngc4526_7m_band7_cont.fits",
    "ngc4526_7m_co32_2p5kms_strict_mom0.fits",
]

for f in files:
    with fits.open(f) as hdu:
        data = hdu[0].data
        # TODO: Pull beam info
        # print(hdu[0].header)

    ii, jj = np.indices(data.shape)
    valid_idx = np.where(~np.isnan(data))
    i_min, i_max = np.min(ii[valid_idx]), np.max(ii[valid_idx])
    j_min, j_max = np.min(jj[valid_idx]), np.max(jj[valid_idx])

    data = data[i_min:i_max, j_min:j_max]

    data[data == 0] = np.nan
    vmin, vmax = np.nanpercentile(data, [1, 99])

    plt.figure(figsize=(5, 3))
    ax = plt.subplot(111)

    plt.imshow(data,
               cmap="inferno",
               origin='lower',
               vmin=vmin,
               vmax=vmax,
               )

    ax.set_facecolor('black')
    ax.tick_params(axis="both", which="both", direction="in", labelleft=False, labelbottom=False, color="white")
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    # ellipse = Ellipse(xy=(157.18, 68.4705), width=0.036, height=0.012,
    #                   edgecolor='r', fc='None', lw=2)
    # ax.add_patch(ellipse)

    im_type = {
        "ngc4526_7m_band7_cont.fits": "Dust",
        "ngc4526_7m_co32_2p5kms_strict_mom0.fits": "CO(3-2)",
    }

    plt.text(0.05, 0.95,
             f"{im_type[f]}",
             ha="left", va="top",
             color="white", fontweight="bold",
             transform=ax.transAxes,
             )

    plot_name = os.path.join("/Users/thomaswilliams/Documents/proposals/alma_cy11/ngc4526_dust_cont",
                             f"{im_type[f]}")

    plt.savefig(f"{plot_name}.png", bbox_inches="tight")
    plt.savefig(f"{plot_name}.pdf", bbox_inches="tight")

    plt.close()

print("Complete!")
