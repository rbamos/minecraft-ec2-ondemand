if tmux list-sessions | grep "network"; then
    echo "Already running network"
else
    tmux new-session -d -s network 'cd ~/setup; ./network.sh'
fi

