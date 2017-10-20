# halconsole
A curses-based agent for testing Halibot modules and view the logs simultaneously. It even sort of works!

## Keybinds
 - `F1`: Toggle the chat window
 - `F2`: Toggle the log window
 - `END`: Close and shutdown (don't ask)

## Usage
Just type away and press enter and your messages will be dispatched to your configured modules.
Currently there are no options or ways to configure the bot or UI, but that's probably on the way.
It is recommended to add `"log-level":"DEBUG"` and `"log-file":"output.log"` to your `config.json`.
Setting `DEBUG` allows more messages to show up and be useful in the second pane (or just disable it with `F2`).
Setting a log file will keep the messages that are printed before the agent can spin up from mucking up the view.
Eventually, commands like `/redraw` or something will be implemented to maybe fix that.

**Semi-important note**: Do not combine this with the `cli` agent, it probably won't like that.
