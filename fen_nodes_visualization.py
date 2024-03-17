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
import chess

from fentoimage.board import BoardImage

from bokeh.io import output_file, show, save
from bokeh.io import output_notebook, show, save
from bokeh.models import Range1d, Circle, ColumnDataSource, MultiLine, HoverTool
from bokeh.plotting import figure, from_networkx
from bokeh.palettes import Blues8, Reds8, Purples8, Oranges8, Viridis8, Spectral8, inferno
from bokeh.transform import linear_cmap
from bokeh.colors import RGB
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
BigDF = pd.read_parquet('chess_games_large_fen_oscarmex45.parquet')

min_number_of_games = 30

BigDF = BigDF[BigDF['player_white'] == 0]

tmp = BigDF['moves'].value_counts()
# get the most common chess positions
list_of_most_common_fen_positions = tmp[tmp.values > min_number_of_games].index
dict_of_common_fen_positions = {i:j for (i,j) in zip(list_of_most_common_fen_positions, 1 + np.arange(len(list_of_most_common_fen_positions)))}
dict_of_common_fen_positions['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'] = 0

# Invert key-value pairs using dictionary comprehension
inverted_dict_of_common_fen_positions = {value: key for key, value in dict_of_common_fen_positions.items()}

# get rid of the uncommons positions
BigDF = BigDF[BigDF['moves'].isin(list_of_most_common_fen_positions)]
BigDF['moves_id'] = BigDF['moves'].map(dict_of_common_fen_positions)

subset = BigDF[['index', 'id', 'result', 'moves_id']].reset_index(drop = True)

counts_of_fen_positions = subset.value_counts('moves_id').to_dict()
counts_of_fen_positions[0] = subset['id'].nunique()

wins_per_fen_position = subset[subset['result'] == '1-0'].value_counts('moves_id').to_dict()
wins_per_fen_position[0] = subset[subset['result'] == '1-0']['id'].nunique()

win_ratio_per_fen_position = {i:wins_per_fen_position[i]/counts_of_fen_positions[i] for i in wins_per_fen_position.keys()}

lift_per_fen_position = {i:j/win_ratio_per_fen_position[0] for i,j in win_ratio_per_fen_position.items()}

#%%    
import os
    # Directory to store images
images_folder = "images/"

# Iterate over ranking and fen_position pairs
for ranking, fen_position in inverted_dict_of_common_fen_positions.items():
    # Define the filename for the image
    image_filename = os.path.join(images_folder, fen_position.replace('/', '_') + ".png")
    
    # Check if the image file already exists
    if not os.path.exists(image_filename):
        print(f'rendering fen {ranking}')
        # Create the BoardImage object and render the image
        renderer = BoardImage(fen_position)
        image = renderer.render()
        
        # Save the image
        image.save(image_filename)
#%% Create network connections

connections_dict = {}
for i in range(subset.shape[0]-1):
    if subset.loc[i]['id'] == subset.loc[i+1]['id']:
        if subset.loc[i]['index'] + 1 == subset.loc[i + 1]['index']:
            try:
                connections_dict[(subset.loc[i]['moves_id'], subset.loc[i+1]['moves_id'])] += 1        
            except KeyError:
                connections_dict[(subset.loc[i]['moves_id'], subset.loc[i+1]['moves_id'])] = 1 
    else:
        if subset.loc[i+1]['index'] == 0:
            try:
                connections_dict[(0, subset.loc[i+1]['moves_id'])] += 1        
            except KeyError:
                connections_dict[(0, subset.loc[i+1]['moves_id'])] = 1 

#%%


# Define custom palette with intermediate colors
red = RGB(255, 0, 0)
yellow = RGB(255, 255, 0)
green = RGB(0, 255, 0)
white = RGB(255, 255, 255)

# Interpolate additional colors between red and yellow
orange = RGB(255, 165, 0)  # Example of an intermediate color
intermediate_colors1 = [RGB(int((1 - i) * red.r + i * orange.r), 
                            int((1 - i) * red.g + i * orange.g), 
                            int((1 - i) * red.b + i * orange.b))
                        for i in [0.2, 0.4, 0.6, 0.8]]

# Interpolate additional colors between yellow and green
lime = RGB(0, 255, 0)  # Example of an intermediate color
intermediate_colors2 = [RGB(int((1 - i) * yellow.r + i * lime.r), 
                            int((1 - i) * yellow.g + i * lime.g), 
                            int((1 - i) * yellow.b + i * lime.b))
                        for i in [0.2, 0.4, 0.6, 0.8]]

# Create custom palette with all colors
custom_palette = [red] + intermediate_colors1 + [yellow] + intermediate_colors2 + [green]
# custom_palette = [red] + [yellow] + [green]

# Create color mapper with custom palette

#%%from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool


# Create a graph object
# G = nx.Graph()
G = nx.DiGraph()


# Add edges from the dictionary including weights
for edge, weight in connections_dict.items():
    G.add_edge(edge[0], edge[1], weight=weight)
    
# Calculate node positions using a layout algorithm
pos = nx.spring_layout(G)


# Define tooltips with image and additional information for nodes
TOOLTIPS_NODES = """
    <div>
        <div>
            <img src="@image" height="150" alt="@image" width="150" style="float: center; margin: 0px 0px 0px 0px;" border="2"></img>
        </div>
        <div>
            <span style="font-size: 10px; color: #696;">Ranking by frequency: @index</span><br>
            <span style="font-size: 10px; color: #696;">Count of positions: @count_of_positions</span><br>
            <span style="font-size: 10px; color: #696;">Count of won games: @won_positions</span><br>
            <span style="font-size: 10px; color: #696;">Win Ratio: @win_ratio</span><br>
            <span style="font-size: 10px; color: #696;">lift: @lift</span>
        </div>
    </div>
"""


# Now, 'pos' is a dictionary where keys are node identifiers and values are (x, y) positions
# You can access positions for specific nodes like this:
x_pos = [pos[i][0] for i in G.nodes]
y_pos = [pos[i][1] for i in G.nodes]
description = [inverted_dict_of_common_fen_positions[i] for i in G.nodes]
image_location = ['images/' + inverted_dict_of_common_fen_positions[i].replace('/','_') + '.png' for i in G.nodes]
idx = [i for i in G.nodes]
counts_fen = [counts_of_fen_positions[i] for i in G.nodes]
log_counts_fen = [np.log(counts_of_fen_positions[i])*3 for i in G.nodes]
won_positions = [wins_per_fen_position[i] for i in G.nodes]
win_ratio = [win_ratio_per_fen_position[i] for i in G.nodes]
lift = [lift_per_fen_position[i] for i in G.nodes]

# Calculate line coordinates for edges
lines_x = []
lines_y = []
lines_weight = []
for edge in G.edges():
    start = pos[edge[0]]
    end = pos[edge[1]]
    lines_x.append([start[0], end[0]])
    lines_y.append([start[1], end[1]])
    try:
        lines_weight.append(np.ceil(np.log(connections_dict[edge]*20))*10)
    except KeyError:
        lines_weight.append(np.ceil(np.log(connections_dict[(edge[1], edge[0])]*20))*10)

# Create a sample ColumnDataSource with data and image URLs for nodes
data_nodes = {
    'x': x_pos,
    'y': y_pos,
    'desc': description,
    'image': image_location,
    'index': idx,
    'count_of_positions': counts_fen,
    'log_count_of_positions': log_counts_fen,
    'won_positions': won_positions,
    'win_ratio': win_ratio,
    'lift': lift
}
source_nodes = ColumnDataSource(data_nodes)

# Create a Bokeh figure
p = figure(width=1980, height=1080, active_scroll='wheel_zoom')

# Plot the lines for edges
p.multi_line(lines_x, lines_y, line_color=lines_weight, line_width=1)

# Color by count of positions
# minimum_value_color = min(counts_fen)
# maximum_value_color = max(counts_fen)
# color_mapper = linear_cmap(field_name='count_of_positions', palette=Blues8, low=minimum_value_color, high=maximum_value_color)

minimum_value_color = max(min(lift),0.5)
maximum_value_color = min(max(lift),1.5)
color_mapper = linear_cmap(field_name='lift', palette=custom_palette, low=minimum_value_color, high=maximum_value_color)

# Plot the points with images for nodes
circle = p.circle('x', 'y', size='log_count_of_positions', source=source_nodes, fill_color=color_mapper, line_color='black')

# Define hover tool for circles (nodes)
hover_tool_nodes = HoverTool(renderers=[circle], tooltips=TOOLTIPS_NODES)
p.add_tools(hover_tool_nodes)


# Show the plot
show(p)
