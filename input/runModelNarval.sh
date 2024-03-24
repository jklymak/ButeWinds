#!/bin/bash
#SBATCH --account=def-jklymak
#SBATCH --mail-user=jklymak@gmail.com
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=64
#SBATCH --time=0-24:10
#SBATCH --mem=0

# sbatch --job-name={todo} runModelNarval.sh
# run from runAll.sh  start and stop come from -v arguments.

# module swap mpt compiler/intelmpi

# module load netcdf-fortran-mpi/4.5.2
# module load python/3.9.6
start=0
stop=432100
dt=6

cd ${SLURM_SUBMIT_DIR}

printf "workdir? ${SLURM_SUBMIT_DIR}\n"
pwd

top=${SLURM_JOB_NAME}
printf "top: $top\n"
results=${SLURM_SUBMIT_DIR}/../results/
outdir=$results$top

cd $outdir/input
pwd
ls -al ../build/mitgcmuv

source ~/venvs/butewind/bin/activate
python moddata.py --startTime=$start --endTime=$stop --deltaT=$dt

printf "Starting: $outdir\n"
module list
which srun
srun ../build/mitgcmuv > mit.out