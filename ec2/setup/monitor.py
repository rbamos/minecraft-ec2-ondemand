#!/bin/python3
from mcstatus import JavaServer
import time
import os
import libtmux

MAX_T = 15
BOOT_T = 30

last_player_t = min(0, MAX_T-BOOT_T) # time since last player

while last_player_t < MAX_T:
  time.sleep(60)
  try:
    server = JavaServer.lookup("localhost:25565")

    status = server.status()
    player_count = status.players.online
    if player_count > 0:
      last_player_t = 0
    else:
      last_player_t += 1
    print(f"Player count is {player_count}. Shutdown count is {last_player_t}/{MAX_T}")
  except:
    last_player_t += 1
    print(f"Failed to get player count. Shutdown count is {last_player_t}/{MAX_T}")


# Stop the running server
s = libtmux.Server()
mc_sessions = s.sessions.filter(session_name="minecraft")
for mc_session in mc_sessions:
  print(f"Closing {mc_session}")
  for pane in mc_session.panes:
    pane.send_keys("stop\n")

# Wait for the Minecraft server's tmux session to close
while len(s.sessions.filter(session_name="minecraft")) > 0:
  print(f"There are {len(s.sessions.filter(session_name='minecraft'))} sessions active")
  time.sleep(60)

# Wait 1 minute just in case there's a bug; this gives us time to ssh in and fix problems
time.sleep(60)

os.system("sudo shutdown now")