

import numpy as np
import pandas as pd
import chess.pgn
from mlxtend.frequent_patterns import apriori,  association_rules
import networkx as nx
import chess

from concurrent.futures import ProcessPoolExecutor, as_completed

from fentoimage.board import BoardImage

from bokeh.io import output_file, show, save
from bokeh.io import output_notebook, show, save
from bokeh.models import Range1d, Circle, ColumnDataSource, MultiLine, HoverTool
from bokeh.plotting import figure, from_networkx
from bokeh.palettes import Blues8, Reds8, Purples8, Oranges8, Viridis8, Spectral8, inferno
from bokeh.transform import linear_cmap
from bokeh.colors import RGB

import multiprocessing
from functools import partial

import pgn_processor
import time

import os
import webbrowser

#%% Pre-processing

# # Directory containing PGN files of elite players
# directory = 'LichessEliteDatabase'

# # Get all files in the directory
# files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

# # Filter files to include only those with .pgn extension
# list_of_parquet_files = [f for f in files if f.endswith('.parquet')]

# for filename in list_of_parquet_files:
#     BigDF = pd.read_parquet(filename)

#     filtered_df = BigDF[BigDF.duplicated(['moves'], keep=False)]
#     filtered_df.to_parquet('Filtered' + filename)


#%% Get dataset of filtered positions.
t1 = time.time()

BigFilteredDF = pd.read_parquet('chess_games_large_elite_players.parquet') # this dataset considers only repeated moves
BigFilteredDF = BigFilteredDF[BigFilteredDF.index < 30] # Only repeated moves in the opening, we do not care about repeated moves in endgame.

min_number_of_games = np.ceil(BigFilteredDF.shape[0]*0.00005) # 1 out of 2000 games had at least those positions

# BigFilteredDF = BigDF[BigDF['player_white'] == 0]

tmp = BigFilteredDF['moves'].value_counts()
# get the most common chess positions
list_of_most_common_fen_positions = tmp[tmp.values > min_number_of_games].index
dict_of_common_fen_positions = {i:j for (i,j) in zip(list_of_most_common_fen_positions, 1 + np.arange(len(list_of_most_common_fen_positions)))}
dict_of_common_fen_positions['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'] = 0

# Invert key-value pairs using dictionary comprehension
inverted_dict_of_common_fen_positions = {value: key for key, value in dict_of_common_fen_positions.items()}

# get rid of the uncommons positions
BigFilteredDF = BigFilteredDF[BigFilteredDF['moves'].isin(list_of_most_common_fen_positions)]
BigFilteredDF['moves_id'] = BigFilteredDF['moves'].map(dict_of_common_fen_positions)

subset = BigFilteredDF[['id', 'result', 'moves_id']].reset_index()



#%% Generate Images
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

#%% Values shown in dashboard. 
counts_of_fen_positions = subset.value_counts('moves_id').to_dict()
counts_of_fen_positions[0] = subset[subset['index'] == 0]['id'].count()

wins_per_fen_position = subset[subset['result'] == '1-0'].value_counts('moves_id').to_dict()
wins_per_fen_position[0] = subset[(subset['result'] == '1-0') & (subset['index'] == 0)]['id'].count()

win_ratio_per_fen_position = {i:wins_per_fen_position[i]/counts_of_fen_positions[i] for i in wins_per_fen_position.keys()}

lift_per_fen_position = {i:j/win_ratio_per_fen_position[0] for i,j in win_ratio_per_fen_position.items()}

# Create network connections
subset2 = pd.concat([subset.iloc[:-1,[1,3]].reset_index(drop=True), subset.iloc[1:,[1,3]].reset_index(drop=True)], axis=1)
subset2.columns = ['id1', 'moves_id1', 'id2', 'moves_id2']
subset2.loc[subset2['id1'] != subset2['id2'], 'moves_id1'] = 0
connections_dict = subset2.groupby(['moves_id1', 'moves_id2']).count().max(axis=1).to_dict()
#%%

import pickle

# Variables to be saved
variables_to_save = {
    'list_of_most_common_fen_positions': list_of_most_common_fen_positions,
    'dict_of_common_fen_positions': dict_of_common_fen_positions,
    'inverted_dict_of_common_fen_positions': inverted_dict_of_common_fen_positions,
    'counts_of_fen_positions': counts_of_fen_positions,
    'wins_per_fen_position': wins_per_fen_position,
    'win_ratio_per_fen_position': win_ratio_per_fen_position,
    'lift_per_fen_position': lift_per_fen_position,
    'connections_dict': connections_dict
}

# # Define the filename to save the variables
filename = 'saved_variables.pkl'

# Pickle the variables and save them to a file
with open(filename, 'wb') as file:
    pickle.dump(variables_to_save, file)

# To load the variables back into the environment later:
# Load the variables from the file
with open(filename, 'rb') as file:
    loaded_variables = pickle.load(file)

# Now you can access the variables from the loaded dictionary
list_of_most_common_fen_positions = loaded_variables['list_of_most_common_fen_positions']
dict_of_common_fen_positions = loaded_variables['dict_of_common_fen_positions']
inverted_dict_of_common_fen_positions = loaded_variables['inverted_dict_of_common_fen_positions']
counts_of_fen_positions = loaded_variables['counts_of_fen_positions']
wins_per_fen_position = loaded_variables['wins_per_fen_position']
win_ratio_per_fen_position = loaded_variables['win_ratio_per_fen_position']
lift_per_fen_position = loaded_variables['lift_per_fen_position']
connections_dict = loaded_variables['connections_dict']
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

#%%
from bokeh.io import output_file, show

from bokeh.plotting import figure, show

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
log_counts_fen = [np.log(counts_of_fen_positions[i]) for i in G.nodes]
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

html_filename = "elite_players.html"
output_file(html_filename)
show(p)

t2 = time.time()
print(t2-t1)

# Optionally, you can open the HTML file in a web browser automatically
webbrowser.open(html_filename)
#%%

