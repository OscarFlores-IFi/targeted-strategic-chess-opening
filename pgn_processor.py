import pandas as pd
import chess.pgn
import re


def process_pgn_file(path_to_file, PLAYER_NAME = None):
    # Open PGN file for reading
    pgn_file = open(path_to_file, encoding="utf8")
    
    # Get games in df format from pgn files
    result_df = process_games(pgn_file, PLAYER_NAME)
    
    # Close PGN file
    pgn_file.close()

    # Get rid of unique positions. 
    result_df = result_df[result_df.duplicated(['moves'], keep=False)]
    
    result_df.to_parquet(path_to_file[:-3] + 'parquet')
    return result_df


def process_games(chunk, PLAYER_NAME = None):
    big_table = []
    counter = 0
    # Iterate through each game in the PGN file
    while True:
    # for _ in range(10):
        # Read next game from the PGN file
        game = chess.pgn.read_game(chunk)
        
        # Check if game exists
        if game is None:
            break
                      
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
        
            # Extract moves
            moves = game.mainline_moves()
            
            board = game.board()
            first_n_moves = []
                     
            for move in moves:
                board.push(move)
                # we save position, not move
                positon_as_fen = board.fen().split()[0]
                clean_fen_position = re.sub(r'[^\w/]+$', '', positon_as_fen)
                first_n_moves.append(clean_fen_position) 
    
            tmp = pd.DataFrame({'id': counter,
                                'white_elo': white_elo, 
                                'black_elo': black_elo, 
                                'result': result, 
                                'moves': first_n_moves})
            
            if PLAYER_NAME:
                try:
                    if game.headers['White'] == PLAYER_NAME:
                        player_white = 1
                    elif game.headers['Black'] == PLAYER_NAME:
                        player_white = 0
                    tmp['player_white'] = player_white
                except:
                    print('Please make sure all the games contain the PLAYER_NAME')
            tmp['value'] = True
            
            big_table.append(tmp)

            counter += 1
    return pd.concat(big_table)

    # python setup.py build_ext --inplace
