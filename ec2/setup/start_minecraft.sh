if tmux list-sessions | grep "minecraft"; then
    echo "Already running minecraft"
else
    tmux new-session -d -s minecraft 'cd ~/minecraft/; ./start.sh'
fi
