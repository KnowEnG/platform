import sys

def log(msg):
    #when bash commands are run, even in series, they outputs
    #will be mixed together unless we flush every time.
    sys.stdout.flush()
    sys.stderr.flush()
    print(msg)
    sys.stdout.flush()

