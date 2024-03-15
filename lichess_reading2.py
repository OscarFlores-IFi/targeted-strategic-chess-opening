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
OPENING_MOVES = 5

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
                 
        move_count = 0
        for move in moves:
            board.push(move)
            first_n_moves.append(board.fen().split()[0]) # position, not move
            move_count += 1
            if move_count >= OPENING_MOVES*2:
                break
        
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
BigDF = BigDF.pivot(index =['id',
                            'white_elo', 
                            'black_elo', 
                            'player_white', 
                            'result'], columns = ['moves'], values = ['value']).reset_index()

BigDF.to_parquet('chess_games_fen_carlsen.parquet')
#%% Shape dataset into market basket analysis similar. 

alt_parquet = pd.read_parquet('chess_games_fen_carlsen.parquet')

alt_parquet = alt_parquet[alt_parquet['player_white'] == 1]

result_dummies = pd.get_dummies(alt_parquet['result'])

alt_parquet = alt_parquet.fillna(0).drop(columns=[
    'white_elo',
    'black_elo',
    'player_white',
    'result'
    ])
alt_parquet.columns = [i[1] for i in alt_parquet.columns]
alt_parquet = pd.concat([result_dummies, alt_parquet], axis=1)# 
alt_parquet = alt_parquet.astype(bool)

#%% Get rules!!!
min_support = 20/alt_parquet.shape[0] 
frequent_itemsets = apriori(alt_parquet, min_support = min_support , use_colnames=True)

#get association rules. 
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.05)

# Moves where I am consistently loosing. 
mask1 = rules['consequents'].apply(lambda x: True if ('0-1') in str(x) else False) # Higher probabilities of loosing.
mask2 = rules['consequents'].apply(lambda x: len(x)) == 1 # Only one result
mask3 = rules['antecedents'].apply(lambda x: len(x)) == 1 # Only one position
filtered_rules = rules[mask1 & mask2 & mask3]


#%% take one of the rules and check some of the games. 
# idx = alt_parquet[alt_parquet['1 e2e3']==1].index

# path_to_file = 'C:/Users/52331/Downloads/lichess_oscarmex45_2024-03-06.pgn'

# ################## Get games where I start with 1 e2e3.

# small_table = []

# # Open PGN file for reading
# pgn_file = open(path_to_file, encoding="utf8")

# cont_i = 0
# # Iterate through each game in the PGN file
# while True: 

#     # Check if game exists
#     if game is None:
#         break
    
#     # Read next game from the PGN file
#     game = chess.pgn.read_game(pgn_file)
    
#     if game.headers['White'] == 'oscarmex45':
#         if cont_i in idx:
#             small_table.append(game)
#         cont_i += 1
                   
# # Close PGN file
# pgn_file.close()

