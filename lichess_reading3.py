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
import pandas as pd
import chess.pgn
from mlxtend.frequent_patterns import apriori,  association_rules


#%%
# path_to_file = 'lichess_db_standard_rated_2024-01.pgn'
path_to_file = 'lichess_DrNykterstein_2024-03-10.pgn'
# path_to_file = 'lichess_oscarmex45_2024-03-06.pgn'

PLAYER_NAME = 'DrNykterstein'

# Open PGN file for reading
pgn_file = open(path_to_file, encoding="utf8")

big_table = []
counter = 0
# Iterate through each game in the PGN file
while True:
# for _ in range(10):
    # Read next game from the PGN file
    game = chess.pgn.read_game(pgn_file)
    
    # Check if game exists
    if game is None:
        break
    
    if game.headers['White'] == PLAYER_NAME:
        player_white = 1
    elif game.headers['Black'] == PLAYER_NAME:
        player_white = 0 
        
    # Extract player Elo ratings
    try:
        white_elo = int(game.headers["WhiteElo"])
    except ValueError:
        white_elo = 0
   
    try: 
        black_elo = int(game.headers["BlackElo"])
    except ValueError:
        black_elo = 0
    
    # Extract game result
    result = game.headers["Result"]
    if result != '*':
    
        # Extract first 5 moves
        moves = game.mainline_moves()
        
        board = game.board()
        first_n_moves = []
                 
        for move in moves:
            board.push(move)
            first_n_moves.append(board.fen().split()[0]) # position, not move
        
        tmp = pd.DataFrame({'id': counter,
                            'white_elo': white_elo, 
                            'black_elo': black_elo, 
                            'player_white': player_white, 
                            'result': result, 
                            'moves': first_n_moves})
        

        tmp['value'] = True
        
        big_table.append(tmp)
        
        if counter % 50 == 0:
            print(counter)
        counter += 1

# Close PGN file
pgn_file.close()    

#%% 
BigDF = pd.concat(big_table).reset_index()

BigDF.to_parquet('chess_games_large_fen_carlsen.parquet')

#%% Pre-processing
BigDF = pd.read_parquet('chess_games_large_fen_carlsen.parquet')

min_number_of_games = 20

# get the most common chess positions
list_of_most_common_fen_positions = BigDF['moves'].value_counts()[BigDF['moves'].value_counts() > min_number_of_games].index

# get rid of the uncommons positions
BigDF = BigDF[BigDF['moves'].isin(list_of_most_common_fen_positions)]

BigDF = BigDF.pivot(index =['id',
                            'white_elo', 
                            'black_elo', 
                            'player_white',
                            'result'], columns = ['moves'], values = ['value']).reset_index()

#%% Shape dataset into market basket analysis similar. 
# FIRST FOR WHITE!

mba = BigDF[BigDF['player_white'] == 1]

result_dummies = pd.get_dummies(mba['result'])

mba = mba.fillna(False).drop(columns=[
    'id',
    'white_elo',
    'black_elo',
    'result'
    ])
mba.columns = [i[1] if i[1] != '' else i[0] for i in mba.columns]
mba = pd.concat([result_dummies, mba], axis=1)# 
mba = mba.astype(bool)

#%% Get rules!!!
min_support = 30/mba.shape[0] 
frequent_itemsets = apriori(mba, min_support = min_support , use_colnames=True)

#get association rules. 
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.1)

# Moves where I am consistently loosing. 
mask1 = rules['consequents'].apply(lambda x: True if (('0-1') in str(x) or ('1-0') in str(x)) else False) # Higher probabilities of loosing.
mask2 = rules['consequents'].apply(lambda x: len(x)) == 1 # Only one result
mask3 = rules['antecedents'].apply(lambda x: len(x)) == 1 # Only one position
filtered_rules = rules[mask1 & mask2 & mask3]

filtered_rules.to_csv('reglas_blanco_carlsen.csv')


#%% Shape dataset into market basket analysis similar. 
# SAME BUT FOR BLACK!

mba = BigDF[BigDF['player_white'] == 0]

result_dummies = pd.get_dummies(mba['result'])

mba = mba.fillna(False).drop(columns=[
    'id',
    'white_elo',
    'black_elo',
    'result'
    ])
mba.columns = [i[1] if i[1] != '' else i[0] for i in mba.columns]
mba = pd.concat([result_dummies, mba], axis=1)# 
mba = mba.astype(bool)

#%% Get rules!!!
min_support = 30/mba.shape[0] 
frequent_itemsets = apriori(mba, min_support = min_support , use_colnames=True)

#get association rules. 
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.1)

# Moves where I am consistently loosing. 
mask1 = rules['consequents'].apply(lambda x: True if (('0-1') in str(x) or ('1-0') in str(x)) else False) # Higher probabilities of loosing.
mask2 = rules['consequents'].apply(lambda x: len(x)) == 1 # Only one result
mask3 = rules['antecedents'].apply(lambda x: len(x)) == 1 # Only one position
filtered_rules = rules[mask1 & mask2 & mask3]

filtered_rules.to_csv('reglas_negro_carlsen.csv')

