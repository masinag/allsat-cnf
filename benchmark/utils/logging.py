def log_header(filename, i, input_files):
    return "Problem {:3d}/{:3d}: {}".format(i + 1, len(input_files), filename)


def log(msg, filename, i, input_files, *args):
    msg = "{} {}".format(
        log_header(filename, i, input_files),
        msg.format(*args))
    print("{}{: <100}".format("\r" * 100, msg), end="")
