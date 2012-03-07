"""Provide shell subprocess functions for ebmeta."""

import logging
import os
import subprocess

log = logging.getLogger('html')

def run(args, shell=False):
    """Run args[0] with arguments args[1:]."""

    log.debug("run(): %s", args)
    #p = subprocess.Popen(args, shell = True)
    p = subprocess.Popen(args, shell=shell)
    os.waitpid(p.pid, 0)

def pipe(args, input="", shell=False):
    """Run args[0] with arguments args[1:] and return standard output."""

    log.debug("pipe(): %s", args)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=shell)
    return p.communicate(input)[0].strip()

def pipe_with_exitcode(args, input):
    """Run args[0] with arguments args[1:] and return (standard output, exit code)."""

    log.debug("pipe(): %s", args)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    output = p.communicate(input)[0].strip()
    return (output, p.returncode)

def save_output(args, output_file):
    """Run args[0] with arguments args[1:] and save standard output to output_file."""

    with file(output_file, 'w') as f:
        p = subprocess.Popen(args, stdout=f)
        os.waitpid(p.pid, 0)
