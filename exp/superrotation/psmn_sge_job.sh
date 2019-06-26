#!/bin/bash
### SGE variables:
## job shell:
#$ -S /bin/bash
## job name:
#$ -N isca_test
## queue:
###$ -q h48-E5-2667v2deb128
#$ -q M6142deb384C
## parallel environment & cpu nb:
#$ -pe mpi32_debian 32
## SGE user environment:
#$ -cwd
## Error/output files:
#$ -o $JOB_NAME-$JOB_ID.out
#$ -e $JOB_NAME-$JOB_ID.err
## Export environment variables:
#$ -V

HOSTFILE="${TMPDIR}/machines"
# change the working directory (default is home directory)
cd "${SGE_O_WORKDIR}"

echo "Running on host $(hostname)"
echo "Time is $(date)"
echo "Directory is $(pwd)"

# Load the conda environment BEFORE loading modules (it defines GFDL_BASE for instance)
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate isca_env

source /usr/share/lmod/lmod/init/bash
module purge
source "$GFDL_BASE/src/extra/env/enslyon"

python "$GFDL_BASE/exp/superrotation/superrotation_nzforcing.py"
