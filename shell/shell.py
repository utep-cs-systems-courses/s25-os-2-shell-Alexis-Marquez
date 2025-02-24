import os
import sys, re, time
outputRedirect = False
inputRedirect = False
if os.environ['PS1']:
    PS1 = os.environ.get('PS1', '$')
else:
    PS1 = '$'
while 1:
    os.write(1, (PS1+'>').encode())
    buff = os.read(0,1000)
    command = buff.decode()
    if command.strip() == 'exit':
        sys.exit(0)
    if command.strip().startswith('cd'):
        parts = command.split()
        if len(parts) > 1:
            try:
                os.chdir(parts[1])
            except Exception as e:
                os.write(1, (str(e) + "\n").encode())
        else:
            os.write(1, "cd: missing argument\n".encode())

    if not command.startswith('\n'):
        rc = os.fork()
        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)

        elif rc == 0:# child
            string = command.strip()
            args = string.split(' ')
            for i in range(len(args)):
                if '>' in args:
                    idx = args.index('>')
                    try:
                        filename = args[idx + 1]
                        fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
                        os.dup2(fd, 1)
                        os.close(fd)
                        args = args[:idx]
                    except IndexError:
                        os.write(1, "Please provide a filename\n".encode())
                        sys.exit(1)

                if '<' in args:
                    idx = args.index('<')
                    try:
                        filename = args[idx + 1]
                        fd = os.open(filename, os.O_RDONLY)
                        os.dup2(fd, 0)
                        os.close(fd)
                        args = args[:idx]
                    except IndexError:
                        os.write(1, "Please provide a filename\n".encode())
                        sys.exit(1)
                    except FileNotFoundError:
                        os.write(1, "Input file not found\n".encode())
                        sys.exit(1)

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