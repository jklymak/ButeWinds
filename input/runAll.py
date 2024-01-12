import os
import subprocess

timest='19:20:00'
### SBATCH --time=38:20:00

runModelName = 'runModelCedar.sh'

for todo in [f'Bute3d{runno}' for runno in range(90, 91)]:
    outstr = f"{todo} queued "
    res = subprocess.check_output(["sbatch", f"--job-name={todo}",
                                   f"--time={timest}",
                                   f"{runModelName}"])
    job0 = res.decode('utf8').split()[-1]
    outstr += f"{job0} "
    res = subprocess.check_output(["sbatch", f"--job-name={todo}",
                        f"--dependency=afterok:{job0}",
                        f"../python/runGetDens.sh"])
    job = res.decode('utf8').split()[-1]
    outstr += f"{job} "
    res = subprocess.check_output(["sbatch", f"--job-name={todo}",
                        f"--dependency=afterok:{job0}",
                        f"../python/runCrossSections.sh"])
    job = res.decode('utf8').split()[-1]
    outstr += f"{job} "
    # store info in a file
    print(outstr)
    with open(".joblog", "a") as joblog:
        joblog.write(outstr+"\n")
