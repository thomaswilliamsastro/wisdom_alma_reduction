#!/usr/bin/env python

band = '3'

pipeline_path = '/data/beegfs/astro-storage/groups/schinnerer/williams/phangs_imaging_scripts'
casa_au_path = '/data/beegfs/astro-storage/groups/schinnerer/williams/analysis_scripts'
master_key = f'keys/master_key_band{band}.txt'

imaging_method = 'tclean'

targets = [
    # 'ngc3489',
    # 'ngc3599',
    # 'ngc3626',
    # 'ngc4596',
    # 'ngc4694',
    # 'ngc7743',
    "ngc3628",
]
line_products = [
    # 'co21_2p5kms',
    "co10_25kms",
]
interf_configs = [
    '12m',
    '7m',
    '12m+7m',
]
feather_configs = [
    '7m+tp',
    '12m+7m+tp',
]

# CASA pipeline

no_cont = True
do_singledish = True
do_staging = True
do_imaging = True
do_postprocess = True
do_derived = True
do_release = False

# Derive pipeline

do_convolve = True
do_noise = True
do_strictmask = True
do_broadmask = False
do_moments = True
do_secondary = False
