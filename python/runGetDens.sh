#!/bin/bash
#SBATCH --account=def-jklymak
#SBATCH --mail-user=jklymak@gmail.com
#SBATCH --mail-type=ALL
#SBATCH --ntasks-per-node=1
#SBATCH --time=0-01:00
#SBATCH --mem=64G

cd ${SLURM_SUBMIT_DIR}

printf "workdir? ${SLURM_SUBMIT_DIR}\n"
pwd

top=${SLURM_JOB_NAME}

# source /home/jklymak/venvs/butewind/bin/activate
source /home/jklymak/venvs/bute_venv_narval/bin/activate

printf "done activate"
echo `which python`
python ../python/getSurfaceDensity.py ${top}

