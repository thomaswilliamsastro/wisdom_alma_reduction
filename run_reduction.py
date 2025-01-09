#!/usr/bin/env python
#
# This script can be run in either Terminal or CASA.
#

import os
import sys

sys.path.append(os.getcwd())

from vars import pipeline_path, casa_au_path, \
    master_key, targets, line_products, interf_configs, feather_configs, no_cont, \
    do_singledish, do_staging, do_imaging, do_postprocess, do_derived, \
    do_convolve, do_noise, do_strictmask, do_broadmask, do_moments, do_secondary, \
    do_release, imaging_method
# from vars_ngc4526_dustcont import pipeline_path, casa_au_path, \
#     master_key, targets, line_products, interf_configs, feather_configs, no_cont, \
#     do_singledish, do_staging, do_imaging, do_postprocess, do_derived, \
#     do_convolve, do_noise, do_strictmask, do_broadmask, do_moments, do_secondary, \
#     do_release, imaging_method


def is_casa_installed():

    casa_enabled = False

    # CASA 5
    try:
        import taskinit
        casa_enabled = True
        return casa_enabled
    except (ImportError, ModuleNotFoundError):
        pass

    # CASA 6
    try:
        import casatools  # favour casatools instead of casatasks
        casa_enabled = True
    except (ImportError, ModuleNotFoundError):
        pass

    return casa_enabled


sys.path.append(pipeline_path)
sys.path.append(casa_au_path)

casa_enabled = is_casa_installed()

if not casa_enabled:

    import distutils.spawn

    casa_executable = distutils.spawn.find_executable('casa')
    if casa_executable is None:
        print('Error! No CASA found in PATH!')
        sys.exit(255)

    casa_bin_path = os.path.dirname(os.path.realpath(casa_executable))
    script_path = os.path.dirname(os.path.abspath(__file__))

    print('Running this script in CASA')
    command = 'export PATH=%s:${PATH}; export PYTHONPATH=%s:%s/phangsPipeline:%s' \
              ':${PYTHONPATH}; cd "%s"; casa --nogui --log2term -c "execfile(\\\"%s\\\")"' % \
              (casa_bin_path, script_path, pipeline_path, casa_au_path, os.getcwd(), __file__)
    os.system(command)

else:

    import phangsPipeline as ppl

    # Reloads for debugging -- NOT WITH PY3
    # reload(pl)
    # reload(kh)
    # reload(uvh)
    # reload(imh)

    # Setup logger
    ppl.phangsLogger.setup_logger(level='DEBUG', logfile=None)

    try:
        from casatasks import casalog
        casalog.filter('INFO')
        casalog.showconsole(True)
    except ImportError:
        pass

    # Initialize handlers and setup everything
    key_handler = ppl.KeyHandler(master_key=master_key)

    sd_handler = None
    uv_handler = None
    im_handler = None
    pp_handler = None
    derived_handler = None
    release_handler = None

    if do_singledish:
        sd_handler = ppl.SingleDishHandler(key_handler=key_handler)
        sd_handler.set_targets(only=targets)
        sd_handler.set_line_products(only=line_products)
        sd_handler.set_no_cont_products(no_cont)
    if do_staging:
        uv_handler = ppl.VisHandler(key_handler=key_handler)
        uv_handler.set_targets(only=targets)
        uv_handler.set_interf_configs(only=interf_configs)
        uv_handler.set_line_products(only=line_products)
        uv_handler.set_no_cont_products(False)
    if do_imaging:
        im_handler = ppl.ImagingHandler(key_handler=key_handler)
        im_handler.set_targets(only=targets)
        im_handler.set_interf_configs(only=interf_configs)
        im_handler.set_line_products(only=line_products)
        im_handler.set_no_cont_products(no_cont)
    if do_postprocess:
        pp_handler = ppl.PostProcessHandler(key_handler=key_handler)
        pp_handler.set_targets(only=targets)
        pp_handler.set_interf_configs(only=interf_configs)
        pp_handler.set_line_products(only=line_products)
        pp_handler.set_feather_configs(only=feather_configs)
        pp_handler.set_no_cont_products(no_cont)
    if do_derived:
        derived_handler = ppl.DerivedHandler(key_handler=key_handler)
        derived_handler.set_targets(only=targets)
        derived_handler.set_interf_configs(only=interf_configs)
        derived_handler.set_feather_configs(only=feather_configs)
        derived_handler.set_line_products(only=line_products)
        derived_handler.set_no_cont_products(no_cont)
    if do_release:
        release_handler = ppl.ReleaseHandler(key_handler=key_handler)
        release_handler.set_targets(only=targets)
        release_handler.set_interf_configs(only=interf_configs)
        release_handler.set_feather_configs(only=feather_configs)
        release_handler.set_line_products(only=line_products)
        release_handler.set_no_cont_products(no_cont)

    # Run things

    key_handler.make_missing_directories(imaging=do_staging, postprocess=do_postprocess, derived=False, release=False)

    if do_singledish:
        sd_handler.loop_singledish(do_all=True)
    if do_staging:
        uv_handler.loop_stage_uvdata(do_copy=True,
                                     do_contsub=True,
                                     do_extract_line=False,
                                     do_extract_cont=False,
                                     require_full_line_coverage=True,
                                     do_remove_staging=False,
                                     overwrite=False,
                                     )

        uv_handler.loop_stage_uvdata(do_copy=False,
                                     do_contsub=False,
                                     do_extract_line=True,
                                     do_extract_cont=False,
                                     require_full_line_coverage=True,
                                     do_remove_staging=False,
                                     # overwrite=False,
                                     overwrite=True,
                                     )

        uv_handler.loop_stage_uvdata(do_copy=False,
                                     do_contsub=False,
                                     do_extract_line=False,
                                     do_extract_cont=True,
                                     require_full_line_coverage=True,
                                     do_remove_staging=False,
                                     # overwrite=False,
                                     overwrite=True,
                                     )

        uv_handler.loop_stage_uvdata(do_copy=False,
                                     do_contsub=False,
                                     do_extract_line=False,
                                     do_extract_cont=False,
                                     require_full_line_coverage=True,
                                     do_remove_staging=True,
                                     # overwrite=False,
                                     overwrite=True,
                                     )
    if do_imaging:

        high_snr = 2.0
        low_snr = 1.0
        absolute = True

        convergence_fracflux = 0.001
        singlescale_threshold_value = 1

        im_handler.loop_imaging(imaging_method=imaging_method,
                                do_dirty_image=True,
                                do_revert_to_dirty=True,
                                do_read_clean_mask=True,
                                do_multiscale_clean=True,
                                do_revert_to_multiscale=True,
                                do_singlescale_mask=True,
                                singlescale_mask_absolute=absolute,
                                singlescale_mask_high_snr=high_snr,
                                singlescale_mask_low_snr=low_snr,
                                do_singlescale_clean=True,
                                do_revert_to_singlescale=True,
                                convergence_fracflux=convergence_fracflux,
                                singlescale_threshold_value=singlescale_threshold_value,
                                do_export_to_fits=True,
                                export_dirty=False,
                                export_multiscale=False,
                                overwrite=False,
                                )

    if do_postprocess:
        pp_handler.loop_postprocess(do_prep=True,
                                    do_feather=True,
                                    feather_before_mosaic=True,
                                    do_mosaic=True,
                                    do_cleanup=True,
                                    imaging_method=imaging_method,
                                    )

    if do_derived:

        derived_handler.loop_derive_products(do_convolve=do_convolve,
                                             do_noise=do_noise,
                                             do_strictmask=do_strictmask,
                                             do_broadmask=do_broadmask,
                                             do_moments=do_moments,
                                             do_secondary=do_secondary,
                                             overwrite=False,
                                             )

    if do_release:
        release_handler.loop_build_release()
