#!/usr/bin/env python

pipeline_path = '/data/beegfs/astro-storage/groups/schinnerer/williams/phangs_imaging_scripts'
casa_au_path = '/data/beegfs/astro-storage/groups/schinnerer/williams/analysis_scripts'
master_key = 'keys/master_key_band6.txt'
# master_key = 'keys/master_key_band7.txt'

imaging_method = 'tclean'

targets = ['ngc1574']
line_products = ['co21_2p5kms']
interf_configs = ['7m', '12m+7m']  # ['12m', '7m', '12m+7m']
feather_configs = ['7m+tp', '12m+7m+tp']

# CASA pipeline

no_cont = True
do_singledish = False
do_staging = False
do_imaging = False
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
