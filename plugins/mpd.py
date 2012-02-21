from util import hook
from mpd import MPDClient

## TODO
##   move
##   help

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

  def fmt(catg, s):
    try:
      if catg == 'title':
        return '%s - %s - %s' % (s['artist'], s['album'], s['title'])
      elif catg == 'album':
        return '%s - %s' % (s['artist'], s['album'])
      elif catg == 'artist':
        return '%s' % (s['artist'])
      else:
        return 'Error: unknown catg for fmt'
    except:
      return 'Error: bad artist, album, or title'

  def queue():
    q = con.playlistinfo()
    for i in range(len(q)):
      q[i] = '  %02d %s' % (i, fmt('title', q[i]))
    # get offset
    try:
      i = int(arg[0])
      if i < 0:
        i = len(q) + i
      if i < 0:
        i = 0
    except:
      i = 0
    pm('Queue (%d total):' % len(q))
    for s in q[i:i+5]:
      pm(s)

  def playing():
    x = con.status()
    if x['state'] == 'play':
      s = con.playlistid(x['songid'])[0]
      say('Now Playing: %s' % fmt('title', s))
    else:
      say('Not playing.')

  def search(catg, x):
    res = con.search(catg, x)
    res = [fmt(catg, r) for r in res]
    res = list(set(res)) # remove dups
    if res != []:
      pm('Results for %s "%s" (%d total):' % (catg, x, len(res)))
      for r in res[:5]:
        pm('  %s' % r)
    else:
      say('Sorry, no results for %s "%s"' % (catg, x))

  def add(search, catg, x):
    res = search(catg, x)
    if res != []:
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

  def toggle_play():
    x = con.status()
    if x['state'] == 'play':
      con.pause('1')
      say('Paused.')
    else:
      con.pause('0')
      say('Playing.')

  def pause():
    con.pause('1')
    say('Paused.')

  def play():
    if len(arg) == 0:
      con.play('0')
      say('Playing.')
    else:
      con.play(arg[0])
      say('Playing %s.' % arg[0])

  cmd_tab = \
    { ('q', 'queue',):
        lambda x: queue()
    , ('', 'n', 'now', 'playing',):
        lambda x: playing()
    , ('?', '?t', 'search',):
        lambda x: search('title', ' '.join(arg))
    , ('?a', 'search-album',):
        lambda x: search('album', ' '.join(arg))
    , ('?A', 'search-artist',):
        lambda x: search('artist', ' '.join(arg))
    , ('+', '+t', 'add',):
        lambda x: add(con.search, 'title', ' '.join(arg))
    , ('+a', 'add-album',):
        lambda x: add(con.search, 'album', ' '.join(arg))
    , ('+!', '+t!', 'add!',):
        lambda x: add(con.find, 'title', ' '.join(arg))
    , ('+a!', 'add-album!',):
        lambda x: add(con.find, 'album', ' '.join(arg))
    , ('-', 'rm', 'remove',):
        lambda x: rm()
    , ('clear',):
        lambda x: clear()
    , ('u', 'up',):
        lambda x: up()
    , ('p',):
        lambda x: toggle_play()
    , ('play',):
        lambda x: play()
    , ('pause',):
        lambda x: pause()
    }

  ok = False
  for k in cmd_tab:
    if cmd in k:
      cmd_tab[k](0)
      ok = True
      break
  if not ok:
    say('Sorry, too dumb to "%s".' % cmd)

  con.disconnect()
