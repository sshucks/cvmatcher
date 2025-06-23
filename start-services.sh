#!/bin/bash

# Start a new tmux session with two panes
tmux new-session -d -s devsession

# Run FastAPI in the first pane
tmux send-keys -t devsession 'python -m fastapi dev src/api/api_call.py --host 0.0.0.0 --port 8000' C-m

# Split the window and run Streamlit in the second pane
tmux split-window -h -t devsession
tmux send-keys -t devsession 'python -m streamlit run src/streamlit/matching_app.py --server.address=0.0.0.0' C-m

# Attach to the session
tmux attach-session -t devsession