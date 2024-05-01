from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import os
from pathlib import Path

from coalesce_parquets import coalesce_parquets
from pgn_processor import process_pgn_file
import time
from model import model

#%%
# Directory containing PGN files of elite players
# DIRECTORY = 'Oscarmex45'
# PLAYER_NAME = 'oscarmex45' # Substitute with Lichess or chesscom player name. 
# PLAYER_PIECES = 'white' # 'white' or 'black' or None. 

DIRECTORY = 'LichessEliteDatabase'
PLAYER_NAME = None
PLAYER_PIECES = None
 

   
def main():

    multiprocessing.freeze_support()
    
    # Get all files in the directory
    files = [os.path.join(DIRECTORY, f) for f in os.listdir(DIRECTORY) if os.path.isfile(os.path.join(DIRECTORY, f))]

    # Filter files to include only those with .pgn extension
    list_of_pgn_files = [f for f in files if f.endswith('.pgn')]
    
    # read pgn and convert them into parquet files. 
    processes = []
    with ProcessPoolExecutor(max_workers=16) as executor:
        for file_path in list_of_pgn_files:
            if not os.path.exists(file_path[:-3] + 'parquet'):
                processes.append(executor.submit(process_pgn_file, file_path, PLAYER_NAME))
    for task in as_completed(processes):
        print('Shape transformed dataset: ' + str(task.result().shape))
    
    # merge parquet files into one.
    paths = Path(DIRECTORY).glob("*.parquet")
    final_path = Path(DIRECTORY + "/final.parquet")
    if not os.path.exists(final_path):
        coalesce_parquets(paths, final_path)
    
    # Run model and store values into pkl
    model(final_path, PLAYER_PIECES)
    
    
    

        



if __name__ == '__main__':

    main()    