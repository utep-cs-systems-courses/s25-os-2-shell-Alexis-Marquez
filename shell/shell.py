import os
import sys, re, time
outputRedirect = False
inputRedirect = False

def execute_program(args):
    for dir in re.split(":", os.environ['PATH']):
        program = f"{dir}/{args[0]}"
        try:
            os.execve(program, args, os.environ)
        except FileNotFoundError:
            continue

    os.write(2, f"Command not found: {args[0]}\n".encode())
    sys.exit(1)



PS1 = os.environ.get('PS1')
if not PS1: PS1 = '$'
while 1:
    os.write(1, (PS1+'> ').encode())
    buff = os.read(0,1000)
    command = buff.decode()
    if command.startswith('\n'):
        continue
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
        continue

    bckg = command.endswith('&')
    if bckg:
        command = command[:-1].strip()

    if '|' in command:
        left, right = command.split('|')
        left_args = left.split()
        right_args = right.split()

        pipe = os.pipe()

        rc = os.fork()
        if rc < 0:
            os.write(2, ('fork failed, returning %d\n' % rc).encode())
            sys.exit(1)
        elif rc == 0:
            os.close(pipe[0])
            os.dup2(pipe[1], 1)
            os.close(pipe[1])

            execute_program(left_args)

        rc2 = os.fork()
        if rc2 < 0:
            os.write(2, ('fork failed, returning %d\n' % rc2).encode())
            sys.exit(1)
        elif rc2 == 0:
            os.close(pipe[1])
            os.dup2(pipe[0], 0)
            os.close(pipe[0])
            execute_program(right_args)

        os.close(pipe[1])
        os.close(pipe[0])
        os.wait()
        os.wait()

    else:
        rc = os.fork()
        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)

        elif rc == 0:# child
            string = command.strip()
            args = string.split(' ')
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
            execute_program(args)


        elif not bckg:
            os.wait()
        else:
            os.write(1, f"Started background process PID: {rc}\n".encode())