import os
import sys, re, time
if os.environ['PS1']:
    PS1 = os.environ['PS1']
else:
    PS1 = '$'
while 1:
    os.write(1, (PS1+'>').encode())
    buff = os.read(0,1000)
    if buff.decode().strip() == 'exit':
        sys.exit(0)
    if not buff.decode().startswith('\n'):
        rc = os.fork()
        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)

        elif rc == 0:                   # child
            string = buff.decode().strip()
            args = string.split(' ')
            for dir in re.split(":", os.environ['PATH']): # try each directory in the path
                program = "%s/%s" % (dir, args[0])
                # os.write(1, ("Trying to exec %s\n" % program).encode())
                try:
                    os.execve(program, args, os.environ) # try to exec program
                except FileNotFoundError:
                    # os.write(1,("Command not found in %s\n" % program).encode())
                    pass

            os.write(2, ("Child:    Could not exec %s\n" % args[0]).encode())
            sys.exit(1)                 # terminate with error

        else:                           # parent (forked ok)
            childPidCode = os.wait()