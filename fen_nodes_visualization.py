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

min_number_of_games = 150

# get the most common chess positions
list_of_most_common_fen_positions = BigDF['moves'].value_counts()[BigDF['moves'].value_counts() > min_number_of_games].index
dict_of_common_fen_positions = {i:j for (i,j) in zip(list_of_most_common_fen_positions, 1 + np.arange(len(list_of_most_common_fen_positions)))}

# get rid of the uncommons positions
BigDF = BigDF[BigDF['moves'].isin(list_of_most_common_fen_positions)]
BigDF['moves_id'] = BigDF['moves'].map(dict_of_common_fen_positions)

subset = BigDF[['index', 'id', 'moves_id']].reset_index(drop = True)

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

import networkx as nx
import plotly.graph_objects as go

# Create a graph object
G = nx.Graph()

# Add edges from the dictionary including weights
for edge, weight in connections_dict.items():
    G.add_edge(edge[0], edge[1], weight=weight)

# Get positions for the nodes (random layout in this case)
pos = nx.spring_layout(G)

# Create nodes trace
node_trace = go.Scatter(
    x=[],
    y=[],
    text=[],
    mode='markers',
    hoverinfo='text',
    marker=dict(
        color='skyblue',
        size=20,
        line_width=2))

# Create edges trace
edge_trace = go.Scatter(
    x=[],
    y=[],
    mode='lines',
    line=dict(color='#888'),
    hoverinfo='none')

# Add nodes and edges to the traces
for node in G.nodes():
    x, y = pos[node]
    node_trace['x'] += tuple([x])
    node_trace['y'] += tuple([y])
    node_trace['text'] += tuple([f'Node: {node}<br>Position: ({list_of_most_common_fen_positions[node-1]})'])

for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_trace['x'] += tuple([x0, x1, None])
    edge_trace['y'] += tuple([y0, y1, None])
    

# Create figure
fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='Network Visualization',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    annotations=[dict(
                        text="",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002)],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))


# Show the figure
fig.show(renderer='browser')
