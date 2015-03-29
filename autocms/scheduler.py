"""Scheduler classes to handle job submission and queue status."""

import os
import subprocess
import time

class UnknownScheduler(Exception):
    """Exception for scheduler type not implemented."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Scheduler(object):
    """Base class for schedulers."""
     
    @staticmethod
    def factory(type):
        """Return a scheduler object of the specified type."""
        if type == 'slurm':
            return SlurmScheduler()
        elif type == 'local':
            return LocalScheduler()
        else:
            raise UknownScheduler("Scheduler type '" +
                                  type +
                                  "' is not implemented.")

    def get_completed_jobs(self, config):
        """Return a list of recently completed jobs."""
        pass

    def enqueued_job_count(self, config):
        """Count the number of jobs that user has on the queue."""
        pass

    def submit_job(self, counter, config):
        """Submit a new job to the queue.

        Returns a tuple with a timestamp, return code, and list of 
        lines from the standard output and error of the submission
        executable."""
        pass

    def jobid_logfilename(self, jobid, testname):
        """Retun the filename of the job standard output."""
        pass


class SlurmScheduler(Scheduler):
    """Interface to slurm scheduler."""

    def get_completed_jobs(self, config):
        cmd = ('/usr/scheduler/slurm/bin/sacct --state=CA,CD,F,NF,TO '
               '-S $(date +%%Y-%%m-%%d -d @$(( $(date +%%s) - 172800 )) ) '
               '--accounts=%s --user=%s -n -o "jobid" | grep -e "^[0-9]* "' 
               % (config['AUTOCMS_GNAME'], config['AUTOCMS_UNAME'] ))
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        lines = result.stdout.readlines()
        return  map(str.strip,lines)

    def submit_job(self, counter, testname, config):
        slurm_script = os.path.join(
                config['AUTOCMS_BASEDIR'],
                testname,
                testname + '.slurm')
        config_path = os.path.join( config['AUTOCMS_BASEDIR'], 'autocms.cfg')
        cmd = ('export AUTOCMS_COUNTER=%d; export AUTOCMS_CONFIGFILE=%s; '
               '/usr/scheduler/slurm/bin/sbatch --account=%s %s '
               '--export=AUTOCMS_COUNTER,AUTOCMS_CONFIGFILE  2>&1'
               % (counter, 
                  config_path, 
                  config['AUTOCMS_GNAME'],
                  slurm_script))
        result = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE)
        result.wait()
        submit_stdout = result.stdout.readlines()
        timestamp = int(time.time())
        return (timestamp, result.returncode, submit_stdout)

    def jobid_logfilename(self, jobid, testname):
        return testname + '.' + 'slurm' + '.o' + jobid