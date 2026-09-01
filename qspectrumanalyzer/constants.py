"""Numbers two parts of the program have to agree on

Nothing is imported here on purpose. The one constant that started this
module lives at the boundary between the scope's recording and a backend
that has to check a setting against it, and every module that could
plausibly have owned it - the plots, the utilities, the data store - pulls
in Qt. A backend that imports the widget stack cannot be run headless, so
the number was copied instead, with a comment in each place asking the next
person to keep them in step. This is that comment made unnecessary.
"""

#: Readings the oscilloscope's high-rate tap keeps. It sets how far back a
#: zero span view reaches - a million readings is 10 s at a 10 us step and
#: 0.8 s at the finest - which is a setting worth checking against how often
#: the thing being hunted comes round.
TAP_CAPACITY = 1000000
