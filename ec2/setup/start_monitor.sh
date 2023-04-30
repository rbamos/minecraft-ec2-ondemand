if tmux list-sessions | grep "monitor"; then
    echo "Already running monitor"
else
    tmux new-session -d -s monitor 'python3 ~/setup/monitor.py; read -p "exiting..."'
fi

