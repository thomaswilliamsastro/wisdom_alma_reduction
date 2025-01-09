import os
import glob

os.chdir("/data/beegfs/astro-storage/groups/schinnerer/williams/wisdom_new_reduction/dl_scripts/ngc3628/2015.1.01140.S/science_goal.uid___A001_X2fa_X20/group.uid___A001_X2fa_X21/member.uid___A001_X2fa_X24/calibration")

flagversions = glob.glob(os.path.join("*.flagversions.tgz"))
caltables = glob.glob(os.path.join("*.caltables.tgz"))

for f in flagversions + caltables:
    os.system("cp " + f + " " + f.replace(".tgz", ".tar.gz"))
