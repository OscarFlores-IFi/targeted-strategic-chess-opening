# Targeted Strategic Chess Opening

This project aims to visualize the best and worst opening positions for a player.

## Usage

1. **Download the PGN dataset**:
    - Obtain the PGN dataset you wish to analyze from providers like chess.com or lichess.org. You can find information on how to download your own games from these servers.

2. **Clone this repository**.

3. **Copy the PGN file(s) into the cloned repository**.
    - All the files have to be inside of a folder (DIRECTORY).

4. **Modify variables in `main.py`**:
    - `DIRECTORY`: Set the directory name where your PGN files are located.
    - `PLAYER_NAME`: Provide the exact name of the player you want to analyze in the PGN files. Use `None` if you want to analyze openings in general.
    - `PLAYER_PIECES`: If `PLAYER_NAME` is provided, you can analyze positions where the player has underperformed and overperformed compared to its average result.
    Possible values are `white`, `black`, `both`, `None`.     

5. **Create a conda environment**:
    - Using conda:
    ```bash
    conda create -n chess_env python=3.10
    conda activate chess_env
    ```

6. **Install required packages**:
    ```bash
    pip install -r requirements.txt
    ```

7. **Run `main.py`**:
    - Execute `main.py` using your preferred IDE or via command line.

8. **Enjoy!**
