
import time
import pickle
import numpy as np
import networkx as nx

import plotly.graph_objects as go
import plotly.io as pio
from dash import Dash, dcc, html, Input, Output, no_update, callback


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

#%% Load variables
t1 = time.time()

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
image_location = ['assets/' + inverted_dict_of_common_fen_positions[i].replace('/','_') + '.png' for i in G.nodes]
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
        opacity=0.95,
        line=dict(color='rgb(50,50,50)', width=0.5)  # Node border
    ),
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
    width=1920,
    height=1080,
)

# Combine traces and layout into a figure
fig = go.Figure(data=edge_traces + [node_trace], layout=layout)

fig.update_traces(hoverinfo="none", hovertemplate=None)


app = Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id="graph-basic-2", figure=fig, clear_on_unhover=True),
    dcc.Tooltip(id="graph-tooltip"),
])



@callback(
    Output("graph-tooltip", "show"),
    Output("graph-tooltip", "bbox"),
    Output("graph-tooltip", "children"),
    Input("graph-basic-2", "hoverData"),
)
def display_hover(hoverData):
    if hoverData is None:
        return False, no_update, no_update

    # demo only shows the first point, but other points may also be available
    pt = hoverData["points"][0]
    bbox = pt["bbox"]
    num = pt["pointNumber"]
        
    children = [
        html.Div([
            html.Img(src=image_location[num],  style={'width': '80%', 'height': '80%'}),
            html.H2(f"Ranking by frequency: {num}"),
            html.P(f"Count games: {counts_fen[num]}"),
            html.P(f"Won games: {won_positions[num]}"),
            html.P(f"Win ratio: {win_ratio[num]}"),
            html.P(f"Lift: {lift[num]}"),
        ], style={'width': '200px', 'white-space': 'normal'})
    ]

    return True, bbox, children


if __name__ == "__main__":
    app.run(debug=True)
    t2 = time.time()
    print('time to execute plot3d.py: ' + str(np.round(t2-t1, 3)) + ' seconds')
    
    # python C:/Users/52331/Documents/GitHub/targeted-strategic-chess-opening/plot3d.py