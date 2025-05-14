echo "start_services.sh is running"
python -m fastapi dev code/api/api_call.py &
python -m streamlit run code/streamlit/matching_app.py &
wait