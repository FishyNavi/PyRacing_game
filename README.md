# PyRacing

A 2D top-down racing game in Python.  
Drift, bump into wals and race! Built with [pyglet](https://pyglet.readthedocs.io/).

---

## Features

- **Drifting**  
  Slide the track like its covered in soap.

- **Collision handling**  
  Using advanced technologies like grayscale track mask, game detects if you are on track and somewhat realistically handles it. 

- **Multiple Cars & Tracks:**  
  Choose from several cars, each with parameters. (2 avaiable)
  Race on 4 unique pixel-art tracks.

- **Lap & Checkpoint System:**  
  Cross the start line to begin a lap. Hit checkpoint and cross finish line to finish the race! Laps and times tracked on screen.

- **Menus & UI:**  
  Cool custom buttons :D !

- **Custom Audio:**  
  Engine sound changes with speed. (Might not work on some systems) Hear your engine roar and your car bumping edges as you race.

- **Pause & Freecam:**  
  Pause the game anytime.  
  Try freecam mode to explore the track!

- **Restart & Unstuck:**  
  Got stuck in a wall?  
  The game detects it and pushes you out after a short wait.  
  Restart instantly from the pause menu.

---

## Controls

- **WASD / Arrow keys** — Drive
- **P** — Pause
- **R** — Restart race (while in game) 
- **F** — Freecam mode
- **E** — Close "settings" :3

---

## How to Play

### **Download**  
- Get the latest **bundled release** for Windows or Linux from [Releases](https://github.com/FishyNavi/PyRacing_game/releases)—no Python needed, just run it!

### **Or Run from Source**  
1. Install [Python 3](https://python.org)  
2. Install pyglet:  
    ```bash
    python3 -m pip install pyglet
    ```
3. Clone and start the game:  
    ```bash
    git clone https://github.com/FishyNavi/PyRacing_game.git
    cd PyRacing_game
    python3 src/main.py
    ```

---

## About the Code

- `main.py` — Game loop, input, menus, and track loading
- `player.py` — Car class: movement, drifting, collisions, lap logic, audio
- `menu.py` — All menus, buttons, and UI logic
- `objects.py` — Track, trees, and trail rendering
- `main_utils.py` — Asset loading and helpers
- `game_logic.py` — World, race state, input handler

---


**FishyNavi**  
Have fun!!!1! :3
