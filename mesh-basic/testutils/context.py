# Copyright 2022 Jeffrey LeBlanc

import asyncio
import pprint
from os import get_terminal_size


class TestContext:

    def __init__(self):
        self.load_terminal_size()
        self.pp = pprint.PrettyPrinter(indent=4)

    async def async_sleep(self, seconds):
        print(f"\x1b[35msleeping for {seconds}sec...\x1b[0m")
        await asyncio.sleep(seconds)
        print("\x1b[35m...done sleeping\x1b[0m")

    def load_terminal_size(self):
        s = get_terminal_size()
        self.col = s.columns
        self.row = s.lines

    def H1(self, text):
        line = self._header2(text)
        print(f"\n\x1b[33m{line}\x1b[0m\n")

    def H2(self, text):
        line = self._header2(text)
        print(f"\n\x1b[93m{line}\x1b[0m\n")

    def HR(self):
        line = self._hr()
        print(f"\x1b[38;5;239m{line}\x1b[0m")

    def P(self, *args):
        print(*args)

    def PP(self, object):
        self.pp.pprint(object)

    def _hr(self, sep='-'):
        return sep*self.col

    def _header2(self, text, sep='-'):
        self.load_terminal_size()
        width = self.col
        tl = len(text)
        if tl > width:
            text = text[:width]
        elif tl+4 > width:
            pass
        else:
            n = width - tl - 2
            text =  f"{sep*int(2)} {text} {sep*int(n-2)}"
        return text
