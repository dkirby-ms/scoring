<%

   import loaddb, query, crawl_utils, html, combos
   c = attributes['cursor']

   all_combo_scores = query.get_combo_scores(c)

   text = html.ext_games_table(all_combo_scores,
                               excluding=['race', 'class'],
                               including=[(1, ('charabbrev', 'Combo'))])
   count = len(all_combo_scores)

   played = set( [ g['charabbrev'] for g in all_combo_scores ] )

   unplayed = [ c for c in combos.VALID_COMBOS if c not in played ]
%>

<html>
  <head>
    <title>Combo Scoreboard</title>
    <link rel="stylesheet" type="text/css" href="tourney-score.css">
  </head>

  <body class="page_back">
    <div class="page">
      <%include file="toplink.mako"/>

      <div class="page_content">

        <h2>Combo Scoreboard</h2>
        <div class="fineprint">
          Highest scoring game for each species-class combination played
          in the tournament.
        </div>

        ${text}

        <div class="inset">
          <div>
          <bold>${len(unplayed)} combos have not been played:</bold>
          </div>
          ${", ".join(unplayed)}
        </div>
      </div>
    </div>

    ${html.update_time()}
  </body>
</html>