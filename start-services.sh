echo "start_services.sh is running"

# Start a new tmux session with two panes
tmux new-session -d -s devsession

# Run FastAPI in the first pane
tmux send-keys -t devsession 'python -m fastapi dev src/api/api_call.py' C-m

# Split the window and run Streamlit in the second pane
tmux split-window -h -t devsession
tmux send-keys -t devsession 'python -m streamlit run src/streamlit/matching_app.py' C-m

# Attach to the session
tmux attach-session -t devsession