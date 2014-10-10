from util import hook
from mpd import MPDClient

# truncate queue and search to avoid flooding
TRUNC = 5

@hook.command
def mpd(inp, bot=None, say=None, pm=None):
  try:
    h = str(bot.config['mpd_host'])
    p = str(bot.config['mpd_port'])
  except:
    return "MPD not configured."
  con = MPDClient()
  con.connect(h, p)
  if 'mpd_pass' in bot.config:
    a = str(bot.config['mpd_pass'])
    con.password(a)

  inp = inp.split(' ')
  cmd = inp[0]
  arg = inp[1:]

  def fmt(catg, s):
    try:
      return \
        { 'title'  : '%s - %s - %s' % (s['artist'], s['album'], s['title'])
        , 'album'  : '%s - %s' % (s['artist'], s['album'])
        , 'artist' : s['artist']
        }[catg]
    except KeyError:
      return 'Error: unknown catg "%s" for fmt' % catg
    except:
      return 'Error: bad tags in song passed to fmt'

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
    for s in q[i:i+TRUNC]:
      pm(s)

  def status():
    x = con.status()
    if x['state'] == 'play':
      s = con.playlistid(x['songid'])[0]
      say('Now Playing: %s' % fmt('title', s))
    else:
      say('Not playing.')

  def search(catg, x):
    res = con.search(catg, x)
    if catg == 'artist':
      res = [fmt('album', r) for r in res]
    else:
      res = [fmt(catg, r) for r in res]
    res = list(set(res)) # remove dups
    if res != []:
      pm('Results for %s "%s" (%d total):' % (catg, x, len(res)))
      for r in res[:TRUNC]:
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
    elif len(arg) == 2:
      try:
        con.delete('%s:%s' % (arg[0], arg[1]))
        say('Removed tracks %s to %s.' % (arg[0], arg[1]))
      except:
        say('Could not remove tracks %s to %s.' % (arg[0], arg[1]))
    else:
      say('Sorry, only "rm" only understands up to 2 arguments.')


  def clear():
    con.clear()
    say('Cleared playlist.')

  def up():
    con.update()
    say('Updated database.')

  def tog():
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

  def next():
    con.next()
    say('Skipped to next song.')

  def mv():
    if len(arg) == 2:
      try:
        con.move(arg[0], arg[1])
        say('Moved track(s) %s to position %s.' % (arg[0], arg[1]))
      except:
        say('Could not move track(s) %s to position %s.' % (arg[0], arg[1]))
    else:
      say('Sorry, move only understands 2 arguments. Use M:N for range in first arg')

  def help():
    cmds = [k[0] for k in sorted(cmd_tab.keys())]
    say('Available commands: %s' % ' '.join(cmds))

  def syns():
    if len(arg) == 1:
      ok = False
      for k in cmd_tab:
        if arg[0] in k:
          xs = ' '.join(['%s' % x for x in k])
          say('Synonyms for "%s": %s' % (arg[0], xs))
          ok = True
          break
      if not ok:
        say('Sorry, no idea what "%s" means.' % arg[0])
    else:
      say('Sorry, synonyms needs an argument.')

  # long name first for help
  cmd_tab = \
    { ('queue', 'q',):
        lambda x: queue()
    , ('status', '',):
        lambda x: status()
    , ('search-title', '?t', '?',):
        lambda x: search('title', ' '.join(arg))
    , ('search-album', '?a',):
        lambda x: search('album', ' '.join(arg))
    , ('search-artist', '?A',):
        lambda x: search('artist', ' '.join(arg))
    , ('add-title', '+t', '+',):
        lambda x: add(con.search, 'title', ' '.join(arg))
    , ('add-album', '+a',):
        lambda x: add(con.search, 'album', ' '.join(arg))
    , ('add-title-strict', '+t!', '+!',):
        lambda x: add(con.find, 'title', ' '.join(arg))
    , ('add-album-strict', '+a!',):
        lambda x: add(con.find, 'album', ' '.join(arg))
    , ('remove', 'rm', '-',):
        lambda x: rm()
    , ('clear',):
        lambda x: clear()
    , ('update-db', 'up',):
        lambda x: up()
    , ('toggle', 'tog',):
        lambda x: tog()
    , ('play', '|>',):
        lambda x: play()
    , ('pause', '||',):
        lambda x: pause()
    , ('next', '>>',):
        lambda x: next()
    , ('move', 'mv',):
        lambda x: mv()
    , ('help', 'h',):
        lambda x: help()
    , ('synonyms', 'syns',):
        lambda x: syns()
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
