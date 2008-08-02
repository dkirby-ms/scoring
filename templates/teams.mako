<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<%
   import crawl_utils, loaddb, query
   c = attributes['cursor']
%>
<html>
  <head>
    <title>Teams</title>
    <link rel="stylesheet" type="text/css" href="tourney-score.css"/>
  </head>
  <body>
    <table class="bordered">
      <tr>
        <th>Teamname</th>
        <th>Captain</th>
        <th>Members</th>
      </tr>
      <%
        players = query.query_rows(c, '''SELECT teams.owner, teams.name, players.name FROM players, teams WHERE players.team_captain = teams.owner''')
        teamnames = {}
        teammembers = {}
        for row in players:
          teamnames[row[0]] = row[1]
          teammembers.setdefault(row[0], []).append(row[2])
      %>
      % for captain in teamnames.iterkeys():
      <tr>
        <td>${teamnames[captain]}</td>
        <td><a href="${crawl_utils.player_link(query.canonicalize_player_name(c, captain))}">${query.canonicalize_player_name(c, captain)}</a></td>
        <td><a href="${crawl_utils.player_link(teammembers[captain][0])}">${teammembers[captain][0]}</a>
        % for name in teammembers[captain][1:]:
        , <a href="${crawl_utils.player_link(name)}">${name}</a>
        % endfor    	
        </td>
      </tr>
      % endfor
    </table>
  </body>
</html>