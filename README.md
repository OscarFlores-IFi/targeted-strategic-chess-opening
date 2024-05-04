# Targeted Strategic Chess Opening

Let's say that tomorrow you are facing a match against Magnus Carlsen. How would you prepare for the match? 
Trying to improve your endgame in one day is impossible (in my opinion). Trying to improve in the middlegame, also impossible I would say. 
Preparing an opening repertoire with the highest chances of winning, well... It may not change quite a lot your probabilities of winning anyways, but you can do it ;)

This project aims to visualize the best and worst opening positions for a player. So if tomorrow you aim to play against Magnus, you can know that if you play as black you should not play Scandinavian openings, as you are most likely to loose. 

## Usage

1. **Download the PGN dataset**:
    - Obtain the PGN dataset you wish to analyze from providers like chess.com or lichess.org. You can find information on how to download your own games from these servers.
    There's a lot of information about it online, but long story short, it works similar to this (copy the link and run it in your web browser): 
        ```
        https://lichess.org/games/export/DrNykterstein
        https://lichess.org/games/export/oscarmex45
        ```
    Or you can make use of https://lichessgamedownload.netlify.app/ 

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


The main contribution is that we can observe games as positions and not as a straight line. Transpositions play an important role in the games, so in the end it doesn't really matter if we start the game with a knight or with an e4 pawn if in the end we play an italian game. 
![The network from 3.6M games of the top lichess players](https://github.com/OscarFlores-IFi/targeted-strategic-chess-opening/blob/main/readme_images/network_of_lichess_elite_games.png)

Tooltips are useful to visualize each position and the information about it. 
![Tooltips available :) ](https://github.com/OscarFlores-IFi/targeted-strategic-chess-opening/blob/main/readme_images/tooltips_for_each_node.png)

Important analysis that can be exctracted out of this is the best positions and the worst positions when a player plays as white or as black. As an example we use the games played by Magnus Carlsen and we can observe that when he is playing with the white pieces he has performed the best against Scandinavian games (up to 80% probability of Carlsen winning)
![Best position for Magnus Carlsen when playing as white](https://github.com/OscarFlores-IFi/targeted-strategic-chess-opening/blob/main/readme_images/best_position_for_magnus_as_white.png)

In the similar way, we can also observe that when Carlsen plays with black pieces, in general his worst position is a London game countergambit with the c pawn. White's probability of winning against Carlsen is 37.5%, which is quite high considering that only 24% of the games with Carlsen as black end up with Carlsen loosing. 
![Worst position for magnus when playing as black](https://github.com/OscarFlores-IFi/targeted-strategic-chess-opening/blob/main/readme_images/worst_position_for_magnus_as_black.png)

There are 5 important variables shown in the tooltip: 
- Ranking by frequency: Should be self-explanatory. The most frequent position is the starting position, and from it, the rest of the positions. 
- Count of positions: In all the games, all the times that the position was reached. 
- Count of won games: Won games are measured always as white. So if you are analyzing a player as white, then it is straightforward. If you analyze the player as black, then you would have to keep in mind that the numbers should be shifted.
- White win ratio: Count of won games / Count of positions
- lift: White win ratio (in the selected position) / white win ratio (in initial position). 

Color codes are according to lift, the higher the lift, the greener. This would represent having an overall better probabilities when in that position compared with the other positions.
Keep in mind that this does not mean that the position is better, it may just mean that the player know better how to play that position. 
