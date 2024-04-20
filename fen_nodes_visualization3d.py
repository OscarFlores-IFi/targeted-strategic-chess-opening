
import pickle
import numpy as np
import pandas as pd
import networkx as nx

from fentoimage.board import BoardImage

import plotly.graph_objects as go
import plotly.io as pio

import time

import os

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

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

#%% Get dataset of filtered positions.
t1 = time.time()

BigFilteredDF = pd.read_parquet('chess_games_large_elite_players.parquet') # this dataset considers only repeated moves
BigFilteredDF = BigFilteredDF[BigFilteredDF.index < 15] # Only repeated moves in the opening, we do not care about repeated moves in endgame.

min_number_of_games = np.ceil(BigFilteredDF.shape[0]*0.0005) # 1 out of 2000 games had at least those positions

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
#%% Save variables
filename = 'saved_variables.pkl'

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

# Pickle the variables and save them to a file
with open(filename, 'wb') as file:
    pickle.dump(variables_to_save, file)


#%% Load variables
filename = 'saved_variables.pkl'

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

#%% Create a sample graph
G = nx.Graph()

# Add edges from the dictionary including weights
for edge, weight in connections_dict.items():
    G.add_edge(edge[0], edge[1], weight=np.sqrt(np.log(weight)/np.log(connections_dict[(0,1)])))
    
# Extract node positions
pos = nx.spring_layout(G, dim=3)

# Create edge traces
edge_traces = []
for edge in G.edges(data=True):
    x0, y0, z0 = pos[edge[0]]
    x1, y1, z1 = pos[edge[1]]
    edge_trace = go.Scatter3d(
        x=[x0, x1],
        y=[y0, y1],
        z=[z0, z1],
        mode='lines',
        line=dict(color='rgba(100, 100, 100, 0.5)', 
                  width=1),
        opacity=edge[2]['weight'],  # Adjust edge thickness and color
        hoverinfo='none'
    )
    edge_traces.append(edge_trace)

#% aestetic details. 

description = [inverted_dict_of_common_fen_positions[i] for i in G.nodes]
image_location = ['images/' + inverted_dict_of_common_fen_positions[i].replace('/','_') + '.png' for i in G.nodes]
idx = [i for i in G.nodes]
counts_fen = [counts_of_fen_positions[i] for i in G.nodes]
log_counts_fen = [np.log(counts_of_fen_positions[i]) for i in G.nodes]
won_positions = [wins_per_fen_position[i] for i in G.nodes]
win_ratio = [win_ratio_per_fen_position[i] for i in G.nodes]
lift = [lift_per_fen_position[i] for i in G.nodes]
color_mapper_func = lambda x: min(max(x-0.5,0),1.5)
mapped_color = [color_mapper_func(x) for x in lift]

# Create node trace
node_trace = go.Scatter3d(
    x=[pos[node][0] for node in G.nodes()],
    y=[pos[node][1] for node in G.nodes()],
    z=[pos[node][2] for node in G.nodes()],
    mode='markers',
    marker=dict(
        size=log_counts_fen,  # Size based on variable1
        color=mapped_color,  # Color based on variable2
        colorscale='RdYlGn',  # Choose a colorscale
        colorbar=dict(title='Lift'),  # Add colorbar label
        opacity=0.95,
        line=dict(color='rgb(50,50,50)', width=0.5)  # Node border
    ),
    text=[f'Ranking by frequency: {node}<br>Won Positions: {human_format(won_positions[i])} <br>Win Ratio: {np.round(win_ratio[i],3)} <br>Lift: {np.round(lift[i],3)}' for i, node in enumerate(G.nodes())],  # Tooltip
    hoverinfo='text',
    showlegend=False  # Hide legend
)


# Create layout
layout = go.Layout(
    title='3D Network Plot',
    scene=dict(
        xaxis=dict(title='X', showbackground=False, showgrid=False),
        yaxis=dict(title='Y', showbackground=False, showgrid=False),
        zaxis=dict(title='Z', showbackground=False, showgrid=False),
        bgcolor='rgba(0,0,0,1)',  # Adjust background color and opacity
    ),
    margin=dict(l=0, r=0, b=0, t=40),  # Adjust margin
    showlegend=False,  # Hide legend
)

# Combine traces and layout into a figure
fig = go.Figure(data=edge_traces + [node_trace], layout=layout)

# Export the figure to an HTML file
pio.write_html(fig, 'network_plot.html', include_plotlyjs='cdn', auto_open=True)
