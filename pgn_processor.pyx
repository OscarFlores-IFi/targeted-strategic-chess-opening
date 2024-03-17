import pandas as pd
import chess.pgn

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
                                'result': result, 
                                'moves': first_n_moves})
            
            if PLAYER_NAME:
                if game.headers['White'] == PLAYER_NAME:
                    player_white = 1
                elif game.headers['Black'] == PLAYER_NAME:
                    player_white = 0
                tmp['player_white'] = player_white
    
            tmp['value'] = True
            
            big_table.append(tmp)
            
            if counter % 1000 == 0:
                print(counter)
            counter += 1
    return pd.concat(big_table)
