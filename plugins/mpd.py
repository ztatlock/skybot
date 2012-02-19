from util import hook
from mpd import MPDClient

@hook.command
def mpd(inp, bot=None, say=None, pm=None):
  try:
    h = str(bot.config['mpd_host'])
    p = str(bot.config['mpd_port'])
  except:
    return "MPD not configured."
  con = MPDClient()
  con.connect(h, p)

  inp = inp.split(' ')
  cmd = inp[0]
  arg = inp[1:]

  def queue():
    # fetch and format queue
    q = con.playlistinfo()
    for i in range(len(q)):
      q[i] = '  %02d %s - %s - %s' % \
          (i, q[i]['artist'], q[i]['album'], q[i]['title'])
    # get offset
    try:
      i = int(arg[0])
    except:
      i = 0
    # say first few results (avoid flooding)
    say('Queue:')
    for s in q[i:i+5]:
      say(s)

  def playing():
    x = con.status()
    if x['state'] == 'play':
      s = con.playlistid(x['songid'])[0]
      say('Now Playing: %s - %s - %s' %
          (s['artist'], s['album'], s['title']))
    else:
      say('Not playing.')

  def add(search, catg, x):
    res = search(catg, x)
    if res !=[]:
      for s in res:
        con.add(s['file'])
      say('Added %s "%s" (%d).' % (catg, x, len(res)))
    else:
      say('Sorry, could not find %s "%s".' % (catg, x))

  def rm():
    if len(arg) == 0:
      try:
        con.delete('0')
        say('Removed current track.')
      except:
        say('Could not remove current track.')
    elif len(arg) == 1:
      try:
        con.delete(arg[0])
        say('Removed track %s.' % arg[0])
      except:
        say('Could not remove track %s.' % arg[0])
    else:
      try:
        con.delete('%s:%s' % (arg[0], arg[1]))
        say('Removed tracks %s to %s.' % (arg[0], arg[1]))
      except:
        say('Could not remove tracks %s to %s.' % (arg[0], arg[1]))

  def clear():
    con.clear()
    say('Cleared playlist.')

  def up():
    con.update()
    say('Updated database.')

  try:
    { 'q'     : lambda x: queue()
    , '?'     : lambda x: playing()
    , '+t'    : lambda x: add(con.search, 'title', ' '.join(arg))
    , '+a'    : lambda x: add(con.search, 'album', ' '.join(arg))
    , '+t!'   : lambda x: add(con.find, 'title', ' '.join(arg))
    , '+a!'   : lambda x: add(con.find, 'album', ' '.join(arg))
    , '-'     : lambda x: rm()
    , 'clear' : lambda x: clear()
    , 'up'    : lambda x: up()
    }[cmd](0)
  except:
    say('Sorry, too dumb to "%s".' % cmd)

  con.disconnect()
