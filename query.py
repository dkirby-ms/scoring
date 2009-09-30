# Library to query the database and update scoring information. Raw data entry
# from logfile and milestones is done in loaddb.py, this is for queries and
# post-processing.

import logging
from logging import debug, info, warn, error

import loaddb
from loaddb import Query, query_do, query_first, query_row, query_rows
from loaddb import query_first_col, query_first_def

import crawl
import crawl_utils
from crawl_utils import DBMemoizer
import uniq
import os.path
import re
from datetime import datetime
import time

# Number of unique uniques
MAX_UNIQUES = 43
MAX_RUNES = 15

def _cursor():
  """Easy retrieve of cursor to make interactive testing easier."""
  d = loaddb.connect_db()
  return d.cursor()

def _filter_invalid_where(d):
  if loaddb.is_not_tourney(d):
    return None
  status = d['status']
  if status in [ 'quit', 'won', 'bailed out', 'dead' ]:
    return None
  else:
    d['status'] = status.title() or 'Active'
    return d

def time_from_str(when):
  if isinstance(when, datetime):
    return when
  if when.endswith('D') or when.endswith('S'):
    when = when[:-1]
  return datetime(*(time.strptime(when, '%Y%m%d%H%M%S')[0:6]))

def canonical_where_name(name):
  test = '%s/%s' % (crawl_utils.RAWDATA_PATH, name)
  if os.path.exists(test):
    return name
  names = os.listdir(crawl_utils.RAWDATA_PATH)
  names = [ x for x in names if x.lower() == name.lower() ]
  if names:
    return names[0]
  else:
    return None

def whereis_player(name):
  name = canonical_where_name(name)
  if name is None:
    return name

  where_path = '%s/%s/%s.where' % (crawl_utils.RAWDATA_PATH, name, name)
  if not os.path.exists(where_path):
    return None

  try:
    f = open(where_path)
    try:
      line = f.readline()
      d = loaddb.apply_dbtypes( loaddb.xlog_dict(line) )
      return _filter_invalid_where(d)
    finally:
      f.close()
  except:
    return None

def row_to_xdict(row):
  return dict( zip(loaddb.LOG_DB_COLUMNS, row) )

@DBMemoizer
def canonicalize_player_name(c, player):
  row = query_row(c, '''SELECT name FROM players WHERE name = %s''',
                  player)
  if row:
    return row[0]
  return None

def find_games(c, table, sort_min=None, sort_max=None,
               limit=None, **dictionary):
  """Finds all games matching the supplied criteria, all criteria ANDed
  together."""

  if sort_min is None and sort_max is None:
    sort_min = 'end_time'

  query = Query('SELECT ' + loaddb.LOG_DB_SCOLUMNS + (' FROM %s' % table))
  where = []
  values = []

  def append_where(where, clause, *newvalues):
    where.append(clause)
    for v in newvalues:
      values.append(v)

  for key, value in dictionary.items():
    if key == 'before':
      append_where(where, "end_time < %s", value)
    else:
      append_where(where, key + " = %s", value)

  order_by = ''
  if sort_min:
    order_by += ' ORDER BY ' + sort_min
  elif sort_max:
    order_by += ' ORDER BY ' + sort_max + ' DESC'

  if where:
    query.append(' WHERE ' + ' AND '.join(where), *values)

  if order_by:
    query.append(order_by)

  if limit:
    query.append(' LIMIT %d' % limit)

  return [ row_to_xdict(x) for x in query.rows(c) ]

def calc_perc(num, den):
  if den <= 0:
    return 0.0
  else:
    return num * 100.0 / den

def calc_perc_pretty(num, den):
  return "%.2f" % calc_perc(num, den)

def find_place(rows, player):
  """Given a list of one-tuple rows, returns the index at which the given
  player name occurs in the one-tuples, or -1 if the player name is not
  present in the list."""
  if rows is None:
    return -1
  p = [r[0] for r in rows]
  if player in p:
    return p.index(player)
  else:
    return -1

def do_place_numeric(rows, callfn):
  index = -1
  last_num = None
  for r in rows:
    if last_num != r[1]:
      index += 1
    last_num = r[1]
    if not callfn(r, index):
      break

def find_place_numeric(rows, player):
  """Given a list of two-tuple rows, returns the index at which the given
  player name occurs in the two-tuples, or -1 if the player name is not
  present in the list. The second element of each tuple is considered to be
  a score. If any element has the same score as a preceding element, it is
  treated as being at the same index."""
  index = -1
  last_num = None
  for r in rows:
    if last_num != r[1]:
      index += 1
    last_num = r[1]
    if r[0] == player:
      return index
  return -1

def best_players_by_total_score(c):
  rows = query_rows(c, '''SELECT name, games_played, games_won,
                                 total_score, best_score,
                                 first_game_start, last_game_end
                            FROM players
                          ORDER BY total_score DESC''')
  res = []
  for r in rows:
    win_perc = calc_perc_pretty(r[2], r[1])
    res.append([r[3]] + list(r[0:3]) + [win_perc] + list(r[4:]))
  return res
