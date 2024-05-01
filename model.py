
import pickle
import numpy as np
import pandas as pd

from fentoimage.board import BoardImage

import time

import os

#%% Get dataset of filtered positions.

def model(parquet_filename, PLAYER_PIECES = None, PLAYER_NAME = None):
    """
    Get the necessary information for the analysis.

    This function receives a parquet file with the positions of the chess 
    games, calculates the information we consider important and then save 
    the values into a pkl file. 

    Parameters
    ----------
    parquet_filename : Path
        A parquet file with the chess positions.
    PLAYER_PIECES : str
        'white' or 'black' or None. will filter the data only where the 
        player was playing either black or white pieces. In any case, the
        analysis would turn into a targeted chess opening. We could find
        training opportunities by analyzing the positions in which we are 
        statistically underperforming. 

    Returns
    -------
    saved_variables.pkl
        The important variables will be stored under a pkl file.
    """
    
    # t1 = time.time()
    
    BigFilteredDF = pd.read_parquet(parquet_filename) # this dataset considers only repeated moves
    BigFilteredDF = BigFilteredDF[BigFilteredDF.index < 30] # Only repeated moves in the opening, we do not care about repeated moves in endgame.
    
    min_number_of_games = np.ceil(BigFilteredDF.shape[0]*0.0005) # 1 out of 2000 games had at least those positions
    
    if PLAYER_PIECES == 'white':
        BigFilteredDF = BigFilteredDF[BigFilteredDF['player_white'] == 1]
    if PLAYER_PIECES == 'black':
        BigFilteredDF = BigFilteredDF[BigFilteredDF['player_white'] == 0]
    
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
    
    # t2 = time.time()
    # print('Time to get chess positions: ' + str(t2 - t1))
    
    #%% Generate Images
        # Directory to store images
    images_folder = "assets/"
    
    # Iterate over ranking and fen_position pairs
    new_images = 0
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
            new_images += 1
    
    # t3 = time.time()
    # print('Time to draw ' + str(new_images) + ' chess positions: ' + str(t3 - t2))

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
