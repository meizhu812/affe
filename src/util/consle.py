class Console:
    P_HEAD = '>>>'
    P_FOOT = '###'
    P_FIX = [P_HEAD, P_FOOT]
    A_HEAD = '{:0>2d}>'
    A_FOOT = '{:0>2d}#'

    @staticmethod
    def output(msg: str, end='\n'):
        print(msg, flush=True, end=end)
        return msg

    @staticmethod
    def warning_msg(msg: str):
        w_msg = '\n' + '[ WARNING: {0} ]'.format(msg)
        Console.output(w_msg)

    @staticmethod
    def cl():
        Console.output('\r{}\r'.format(80 * ' '), end='')

    @staticmethod
    def blk(lines):
        Console.output(lines * '\n', end='')


console = Console()
