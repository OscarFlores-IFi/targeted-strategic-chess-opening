from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import os
from pathlib import Path

from coalesce_parquets import coalesce_parquets
import pgn_processor


#%%
# Directory containing PGN files of elite players
directory = 'LichessEliteDatabase'

# Get all files in the directory
files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

# Filter files to include only those with .pgn extension
list_of_pgn_files = [f for f in files if f.endswith('.pgn')]

def process_pgn_file(path_to_file, PLAYER_NAME = None):
    # Open PGN file for reading
    pgn_file = open(path_to_file, encoding="utf8")
    
    # Process the game using the compiled Cython function
    result_df = pgn_processor.process_games(pgn_file, PLAYER_NAME)
    
    # Close PGN file
    pgn_file.close()

    result_df.to_parquet(path_to_file[:-3] + 'parquet')
    return result_df
    

def main():
    multiprocessing.freeze_support()
    
    # read pgn and convert them into parquet files. 
    processes = []
    with ProcessPoolExecutor(max_workers=16) as executor:
        for file_path in list_of_pgn_files:
            if not os.path.exists(file_path[:-3] + 'parquet'):
    
                processes.append(executor.submit(process_pgn_file, file_path))
    
    # merge parquet files into one.
    paths = Path("Filtered" + directory).glob("*.parquet")
    coalesce_parquets(paths, "chess_games_large_elite_players.parquet")
    
    for task in as_completed(processes):
        print(task.result().shape)
        



if __name__ == '__main__':

    main()    