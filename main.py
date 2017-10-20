#!/usr/bin/env python3
import curses
import curses.textpad
import threading
import time
import textwrap
import collections
import logging

logging.basicConfig(filename="output.log", level=logging.DEBUG)

class ConsoleWindow():

	def __init__(self, name):
		self.logger = logging.getLogger(name)
		self.name = name
		self.win = None
		self.pos = -1
		self.num = -1

	def refresh(self):
		self.win.box()
		self.win.addstr(0, 2, self.name)
		self.logger.info('gerp')
		self.win.refresh()

	def setpos(self, pos, num):
		self.pos = pos
		self.num = num

	def redraw(self):
		if self.win:
			del self.win
			self.win = None
		start = self.get_win_start()
		size = self.get_win_size()
		self.win = gblscr.subwin(*size, *start)
		self.refresh()

	def get_win_start(self):
		return (0, (self.pos * ((curses.COLS-1) // self.num)))

	def get_win_size(self):
		return (curses.LINES - 2, ((curses.COLS-1) // self.num) - 1)

	def get_draw_start(self):
		# Increment start pos by one to account for the box
		return tuple(map(lambda x: x+1, self.get_win_start()))

	def get_draw_size(self):
		return tuple(map(lambda x: x-2, self.get_win_size()))


class LogWindow(ConsoleWindow):

	def __init__(self, name):
		super().__init__(name)
		self.buffer = []

	def append(self, msg):
		self.buffer.insert(0, self.name + " " + msg) # TODO: optimize this
		self.refresh()

	def refresh(self):
		if not self.win:
			return

		if not self.buffer:
			super().refresh()
			return

		max_outbuflen = self.get_draw_size()[0] # How many lines can we show
		max_linelen = self.get_draw_size()[1]   # How many characters per line

		# Buffer of everything to be printed to screen
		outbuf = []
		count = 0
		for i in self.buffer:
			tw = textwrap.wrap(i, max_linelen)[::-1]
			d = len(tw) + count - max_outbuflen
			# This should be non-negative if we exceed max_outbuflen (how much we exceed by)
			if d > 0:
				tw = tw[:-d] # Truncate wrap list

			outbuf += tw
			count += len(tw)

			# We went over, bail
			if d > 0:
				break

		y = len(outbuf)
		x = 1
		for o in outbuf:
			self.win.addstr(y, x, " " * max_linelen) # TODO: fix this line clear hack
			self.win.addstr(y, x, o)
			y -= 1

		super().refresh()

# Custom input handler because textbox kind of sucks
class ConsoleInput():

	def __init__(self, con):
		self.con = con
		self.win = gblscr.subwin(1, curses.COLS-1, curses.LINES - 2, 0)
		self.buffer = []
		self.history = []
		self.cur = 0
		self.histcur = -1

	def handle(self, c):
		# Remove one charater at current location
		if c in (curses.KEY_BACKSPACE, 127):
			if self.cur == 0: # Bail if at beginning
				return
			self.cur -= 1
			self.buffer.pop(self.cur)
			self.win.addstr(0, 0, "".join(self.buffer) + " ")
			self.win.move(0, len(self.buffer))

		# Send out the line
		elif c in (curses.KEY_ENTER, 10):
			if len(self.buffer) == 0:
				return # don't need to do anything if nothing was typed
			self.history.append("".join(self.buffer))
			self.con.send("".join(self.buffer))
			self.buffer = []
			self.win.addstr(0,0, " " * (self.win.getmaxyx()[1]-1))
			self.cur = 0
			self.histcur = -1

		elif c == curses.KEY_LEFT:
			self.cur = max(self.cur - 1, 0)

		elif c == curses.KEY_RIGHT:
			self.cur = min(self.cur + 1, len(self.buffer))

		elif c == curses.KEY_UP:
			if len(self.history) == 0:
				return
			tmp = len(self.buffer)
			self.buffer = list(self.history[self.histcur])
			self.histcur -= 1 if self.histcur > (-(len(self.history))) else 0
			self.win.addstr(0, 0, ("".join(self.buffer)).ljust(tmp))
			self.cur = len(self.buffer)

		elif c == curses.KEY_DOWN:
			# Clear input if down is pressed at the bottom
			if self.histcur == -1:
				self.win.addstr(0,0, " " * len(self.buffer))
				self.buffer = []
				self.cur = 0
			else:
				tmp = len(self.buffer)
				self.buffer = list(self.history[self.histcur])
				self.histcur += 1
				self.win.addstr(0, 0, ("".join(self.buffer)).ljust(tmp))
				self.cur = len(self.buffer)

		else:
			self.cur += 1
			self.buffer.insert(self.cur-1, chr(c))
			self.win.addstr(0, 0, "".join(self.buffer))

		self.win.move(0, self.cur)
		self.win.refresh()

class Console():

	def __init__(self):
		self.logger = logging.getLogger("Console")
		self.chat = LogWindow("Chat")
		self.log = LogWindow("Log")
		self.inp = ConsoleInput(self)
		# Don't use .enable() for this, no point
		self.enabled = [self.chat, self.log]

	def toggle(self, wincls):

		if wincls in self.enabled:
			# Disallow disabling all windows
			if len(self.enabled) == 1:
				return
			self.disable(wincls)
		else:
			self.enable(wincls)

	def enable(self, wincls):
		self.enabled.append(wincls)
		self.redraw()

	def disable(self, wincls):
		self.enabled.remove(wincls)
		self.redraw()

	# This should only be called when either resizing the whole window or a window is toggled
	def redraw(self):
		for i in range(len(self.enabled)):
			self.enabled[i].setpos(i, len(self.enabled))
			self.enabled[i].redraw()

	# Deliver message to chat from user
	def send(self, msg):
		self.chat.append("user: " + msg)

	# TODO: implement this for CLI
	def recv(self, msg):
		pass

	def handle_input(self):
		self.stop = False
		while not self.stop:
			self.input(gblscr.getch())

	def input(self, c):
		if c == curses.KEY_RESIZE:
			curses.update_lines_cols()
			self.con.redraw()
		elif c == curses.KEY_END:
			self.stop = True
		elif c == curses.KEY_F1:
			self.toggle(self.chat)
		elif c == curses.KEY_F2:
			self.toggle(self.log)
		else:
			self.inp.handle(c)



def foo(func):
	i = 0
	time.sleep(1)
	try:
		while not stop:
			func("this is a really long line ran " + str(i))
			i += 1
			time.sleep(1)
	except Exception as e:
		logging.error("Fatal error in main loop", exc_info=True)


stop = False
gblscr = None

def main(stdscr):
	global gblscr

	gblscr = stdscr
	gblscr.clear()
	gblscr.refresh()

	con = Console()
	con.redraw()

	t1 = threading.Thread(target=foo, args=(con.chat.append,))
	t2 = threading.Thread(target=foo, args=(con.log.append,))

	#t1.start()
	#t2.start()

	con.handle_input()

	#t1.join()
	#t2.join()

curses.wrapper(main)
