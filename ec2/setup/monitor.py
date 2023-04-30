#!/bin/python3
from mcstatus import JavaServer
import time
import os
import libtmux

MAX_T = 10
BOOT_T = 15

HIBERNATE = True
INSTANCE_ID = "i-0db1ce3d8171c7e44"

def monitor(is_first_boot = False):
  if is_first_boot:
    last_player_t = min(0, MAX_T-BOOT_T) # time since last player
  else:
    last_player_t = 0

  player_count = -1

  while last_player_t <= MAX_T:
    time.sleep(60)
    try:
      server = JavaServer.lookup("localhost:25565")

      status = server.status()
      player_count = status.players.online
      if player_count > 0:
        print(f"Player count is {player_count}. Resetting shutdown count.")
        last_player_t = 0
      else:
        last_player_t += 1
        print(f"Player count is {player_count}. Shutdown count is {last_player_t}/{MAX_T}.")
    except:
      player_count = -1
      last_player_t += 1
      print(f"Failed to get player count. Shutdown count is {last_player_t}/{MAX_T}.")

  if player_count != 1 and HIBERNATE:
    print("Hibernating instance")
    os.system(f"aws ec2 stop-instances --instance-ids {INSTANCE_ID} --hibernate")
  else:
    print("Stopping Minecraft")
    # Stop the running server
    s = libtmux.Server()
    mc_sessions = s.sessions.filter(session_name="minecraft")
    for mc_session in mc_sessions:
      print(f"Closing {mc_session}")
      for pane in mc_session.panes:
        pane.send_keys("stop\n")

    print("Waiting for server to halt")
    while len(s.sessions.filter(session_name="minecraft")) > 0:
      print(f"There are {len(s.sessions.filter(session_name='minecraft'))} sessions active")
      time.sleep(60)

    # Wait 1 minute just in case there's a bug; this gives us time to ssh in and fix problems
    time.sleep(60)

    print("Shutting down instance")
    
    os.system("sudo shutdown now")

if __name__ == "__main__":
  monitor(is_first_boot = True)
  if HIBERNATE:
    while True:
      time.sleep(15)
      monitor(is_first_boot = False)

