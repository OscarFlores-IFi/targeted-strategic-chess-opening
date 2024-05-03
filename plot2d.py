
import pickle
import numpy as np

import networkx as nx

from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from bokeh.colors import RGB

import time

import webbrowser

#%%
t1 = time.time()


filename = 'saved_variables.pkl'

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

# %%

# Create a graph object
G = nx.Graph()
# G = nx.DiGraph()


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
            <span style="font-size: 10px; color: #696;">White win Ratio: @win_ratio</span><br>
            <span style="font-size: 10px; color: #696;">lift: @lift</span>
        </div>
    </div>
"""


# Now, 'pos' is a dictionary where keys are node identifiers and values are (x, y) positions
# You can access positions for specific nodes like this:
x_pos = [pos[i][0] for i in G.nodes]
y_pos = [pos[i][1] for i in G.nodes]
description = [inverted_dict_of_common_fen_positions[i] for i in G.nodes]
image_location = ['assets/' + inverted_dict_of_common_fen_positions[i].replace('/','_') + '.png' for i in G.nodes]
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



# Optionally, you can open the HTML file in a web browser automatically
webbrowser.open(html_filename)

t2 = time.time()
print('time to execute plot2d.py: ' + str(np.round(t2-t1, 3)) + ' seconds')

#%%

