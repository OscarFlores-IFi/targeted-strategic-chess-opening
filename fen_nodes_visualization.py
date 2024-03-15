# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 13:32:17 2024

@author: 52331
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 17:19:45 2024

@author: 52331
"""
import re
import numpy as np
import pandas as pd
import chess.pgn
from mlxtend.frequent_patterns import apriori,  association_rules
import networkx as nx


#%%
# # path_to_file = 'lichess_db_standard_rated_2024-01.pgn'
# path_to_file = 'lichess_DrNykterstein_2024-03-10.pgn'
# # path_to_file = 'lichess_oscarmex45_2024-03-06.pgn'

# PLAYER_NAME = 'DrNykterstein'

# # Open PGN file for reading
# pgn_file = open(path_to_file, encoding="utf8")

# big_table = []
# counter = 0
# # Iterate through each game in the PGN file
# while True:
# # for _ in range(10):
#     # Read next game from the PGN file
#     game = chess.pgn.read_game(pgn_file)
    
#     # Check if game exists
#     if game is None:
#         break
    
#     if game.headers['White'] == PLAYER_NAME:
#         player_white = 1
#     elif game.headers['Black'] == PLAYER_NAME:
#         player_white = 0 
        
#     # Extract player Elo ratings
#     try:
#         white_elo = int(game.headers["WhiteElo"])
#     except ValueError:
#         white_elo = 0
   
#     try: 
#         black_elo = int(game.headers["BlackElo"])
#     except ValueError:
#         black_elo = 0
    
#     # Extract game result
#     result = game.headers["Result"]
#     if result != '*':
    
#         # Extract first 5 moves
#         moves = game.mainline_moves()
        
#         board = game.board()
#         first_n_moves = []
                 
#         for move in moves:
#             board.push(move)
#             first_n_moves.append(board.fen().split()[0]) # position, not move
        
#         tmp = pd.DataFrame({'id': counter,
#                             'white_elo': white_elo, 
#                             'black_elo': black_elo, 
#                             'player_white': player_white, 
#                             'result': result, 
#                             'moves': first_n_moves})
        

#         tmp['value'] = True
        
#         big_table.append(tmp)
        
#         if counter % 50 == 0:
#             print(counter)
#         counter += 1

# # Close PGN file
# pgn_file.close()    

# #%% 
# BigDF = pd.concat(big_table).reset_index()

# BigDF.to_parquet('chess_games_large_fen_carlsen.parquet')

#%% Pre-processing
BigDF = pd.read_parquet('chess_games_large_fen_carlsen.parquet')

min_number_of_games = 20


tmp = BigDF['moves'].value_counts()
# get the most common chess positions
list_of_most_common_fen_positions = tmp[tmp.values > min_number_of_games].index
dict_of_common_fen_positions = {i:j for (i,j) in zip(list_of_most_common_fen_positions, 1 + np.arange(len(list_of_most_common_fen_positions)))}

# get rid of the uncommons positions
BigDF = BigDF[BigDF['moves'].isin(list_of_most_common_fen_positions)]
BigDF['moves_id'] = BigDF['moves'].map(dict_of_common_fen_positions)

subset = BigDF[['index', 'id', 'moves_id']].reset_index(drop = True)

counts_of_fen_positions = subset.value_counts('moves_id').to_dict()
counts_of_fen_positions[0] = subset['id'].nunique()

#%% Create network connections

connections_dict = {}
for i in range(subset.shape[0]-1):
    if subset.loc[i]['id'] == subset.loc[i+1]['id']:
        try:
            connections_dict[(subset.loc[i]['moves_id'], subset.loc[i+1]['moves_id'])] += 1        
        except KeyError:
            connections_dict[(subset.loc[i]['moves_id'], subset.loc[i+1]['moves_id'])] = 1 
    else:      
        try:
            connections_dict[(0, subset.loc[i+1]['moves_id'])] += 1        
        except KeyError:
            connections_dict[(0, subset.loc[i+1]['moves_id'])] = 1 

#%%
# Create a graph object
G = nx.Graph()

# Add edges from the dictionary including weights
for edge, weight in connections_dict.items():
    G.add_edge(edge[0], edge[1], weight=weight)

#%%
from bokeh.io import output_file, show, save
from bokeh.io import output_notebook, show, save
from bokeh.models import Range1d, Circle, ColumnDataSource, MultiLine
from bokeh.plotting import figure
from bokeh.plotting import from_networkx
from bokeh.palettes import Blues8, Reds8, Purples8, Oranges8, Viridis8, Spectral8
from bokeh.transform import linear_cmap

#Choose a title!
title = 'Chess Openings Network'

output_file(filename="custom_filename.html", title=title)
nx.set_node_attributes(G, name='count_of_positions', values=counts_of_fen_positions)
nx.set_node_attributes(G, name='log_counts', values = {i:np.log(j)*3 for i,j in counts_of_fen_positions.items()})

#Establish which categories will appear when hovering over each node
HOVER_TOOLTIPS = [("Character", "@index"),
                  ("Count of positions", "@count_of_positions")]

#Pick a color palette — Blues8, Reds8, Purples8, Oranges8, Viridis8
color_palette = Blues8

#Create a plot — set dimensions, toolbar, and title
plot = figure(tooltips = HOVER_TOOLTIPS,
              tools="pan,wheel_zoom,save,reset", active_scroll='wheel_zoom',
            x_range=Range1d(-10.1, 10.1), y_range=Range1d(-10.1, 10.1), title=title, width= 1980, height=1080)

#Create a network graph object with spring layout
network_graph = from_networkx(G, nx.spring_layout, scale=10, center=(0, 0))

#Set node sizes and colors according to node degree (color as spectrum of color palette)
minimum_value_color = min(network_graph.node_renderer.data_source.data["count_of_positions"])
maximum_value_color = max(network_graph.node_renderer.data_source.data["count_of_positions"])
network_graph.node_renderer.glyph = Circle(size="log_counts", fill_color=linear_cmap("count_of_positions", color_palette, minimum_value_color, maximum_value_color))



#Set edge opacity and width
# network_graph.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)


#Add network graph to the plot
plot.renderers.append(network_graph)

show(plot)
#save(plot, filename=f"{title}.html")

#%%

