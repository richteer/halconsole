from halibot import HalAgent, Message
from .console import Console
from threading import Thread

# Implements overrides the .send() for wiring to Halibot core
class NewConsole(Console):

	def send(self, msg):
		super().send(msg)
		msg0 = Message(body=msg, author=self.agent.author)
		self.agent.dispatch(msg0)

class HalConsole(HalAgent):

	def init(self):
		self.con = NewConsole()
		self.con.agent = self
		self.author = self.config.get("author","user")
		self.thread = Thread(target=self._loop)
		self.thread.start()

	def receive(self, msg):
		self.con.chat.append("{}: {}".format(msg.origin, msg.body))

	def _loop(self):
		self.con.run()
		self._hal.shutdown()
