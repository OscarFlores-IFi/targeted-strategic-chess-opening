
import pickle
import numpy as np
import pandas as pd

from fentoimage.board import BoardImage

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


#%% Get dataset of filtered positions.
t1 = time.time()

BigFilteredDF = pd.read_parquet('chess_games_large_elite_players.parquet') # this dataset considers only repeated moves
BigFilteredDF = BigFilteredDF[BigFilteredDF.index < 30] # Only repeated moves in the opening, we do not care about repeated moves in endgame.

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
images_folder = "assets/"

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

t2 = time.time()

print('time to execute model.py: ' + str(np.round(t2-t1, 3)) + ' seconds')