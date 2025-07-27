import matplotlib
matplotlib.use('Agg') # Use Agg backend for non-interactive image generation in web environment

import matplotlib.pyplot as plt # Kept for potential future use or if converting mpl plots to plotly
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go # Using Plotly for interactive web charts
import collections
import time
import re
import threading
import os
import sys
import io
from datetime import datetime # For better time handling

# --- Configuration ---
NGINX_LOG_PATH = '/var/log/nginx/access.log'
# MODIFIED: Let's try a slightly different regex, focusing on capturing the IP:Port after "Backend:"
# This regex is made more flexible for potential leading backslashes or spaces before "Backend:"
# It captures the IP:Port part.
LOG_PATTERN = re.compile(r'.*Backend:\s*\\?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)')
TPS_WINDOW_SECONDS = 60 # Window for TPS calculation
DASHBOARD_APP_PORT = "8050" # Dashboard app's internal port to filter out

# --- Global Data Structures (shared between main app and background thread) ---
request_counts = collections.Counter() # Stores cumulative request counts per backend
request_timestamps = collections.deque() # Stores timestamps of requests for TPS calculation

# Stores historical snapshots of request_counts for the line graph
HISTORICAL_DATA_MAX_LEN = (5 * 60) // 2 # 5 minutes / 2 second interval
historical_request_data = collections.deque(maxlen=HISTORICAL_DATA_MAX_LEN)

# --- Log Tailing Function (MODIFIED for debugging) ---
def tail_nginx_log():
    print(f"Background thread: Attempting to tail log file: {NGINX_LOG_PATH}", flush=True)
    try:
        # Loop to wait for the log file to appear
        while not os.path.exists(NGINX_LOG_PATH):
            print(f"Background thread: Waiting for log file to appear at {NGINX_LOG_PATH}...", flush=True)
            time.sleep(1)

        fd = os.open(NGINX_LOG_PATH, os.O_RDONLY)
        with io.TextIOWrapper(os.fdopen(fd, 'rb'), encoding='utf-8', errors='ignore') as f:
            f.seek(0, os.SEEK_END) # Start reading from the end of the file

            print(f"Background thread: Started tailing log file: {NGINX_LOG_PATH}", flush=True)
            print(f"Background thread: Current LOG_PATTERN: '{LOG_PATTERN.pattern}'", flush=True) # Print current regex pattern
            
            while True:
                line = f.readline() # Read new lines from the file
                if not line: # If no new line, wait briefly and try again
                    time.sleep(0.1) # Short sleep to avoid busy-waiting
                    continue

                log_line = line.strip() # Remove leading/trailing whitespace
                
                # --- ADDED DEBUGGING PRINTS ---
                print(f"Background thread: Raw line read: '{log_line}'", flush=True)
                
                match = LOG_PATTERN.search(log_line)
                
                if match:
                    backend_address = match.group(1)
                    print(f"Background thread: MATCH FOUND! Extracted Backend: '{backend_address}'", flush=True)
                    
                    # Filtering logic
                    if backend_address.endswith(f":{DASHBOARD_APP_PORT}"):
                        print(f"Background thread: Filtered out dashboard traffic: '{backend_address}'", flush=True)
                        continue # Skip counting this log line
                    
                    request_counts[backend_address] += 1
                    request_timestamps.append(time.time())
                    print(f"Background thread: Updated counts: {request_counts}", flush=True)
                else:
                    print(f"Background thread: NO MATCH for line: '{log_line}'", flush=True)
                # --- END DEBUGGING PRINTS ---
                
                # Maintain the TPS window
                while request_timestamps and request_timestamps[0] < time.time() - TPS_WINDOW_SECONDS:
                    request_timestamps.popleft()

    except Exception as e:
        print(f"Background thread: An error occurred during log tailing: {e}", file=sys.stderr)

# --- Dash Application Setup ---
app = dash.Dash(__name__, title="Nginx Load Balancing Dashboard",
                requests_pathname_prefix='/dashboard/') # IMPORTANT: Set the base path for Dash assets

# Define the layout of the dashboard web page
app.layout = html.Div(style={'fontFamily': 'sans-serif', 'textAlign': 'center', 'backgroundColor': '#f0f0f0', 'minHeight': '100vh'}, children=[
    html.H1("Generic Hash LB by request URI", style={'color': '#333'}),
    
    html.Div(id='live-update-text', style={'fontSize': '1.2em', 'margin': '10px 0', 'color': '#555'}),
    
    # Graph component for the interactive line chart
    dcc.Graph(id='live-update-line-graph'), # Changed ID from 'live-update-graph'
    
    # Interval component to trigger periodic updates
    dcc.Interval(
        id='interval-component',
        interval=2000, # Update every 2 seconds (in milliseconds)
        n_intervals=0
    ),
    
    html.Div(className="note", style={'marginTop': '20px', 'color': '#666', 'fontSize': '0.9em'}, children=[
        html.P(f"Dashboard created with Plotly Dash. Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}"),
        html.P("Generate traffic to http://localhost/ and observe updates.")
    ])
])

# Callback to update the line graph and text every interval
@app.callback(
    [Output('live-update-line-graph', 'figure'), # Changed Output ID
     Output('live-update-text', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_graph_live(n):
    current_time_dt = datetime.now()
    
    # Capture a snapshot of current request counts and append to historical data
    current_snapshot = dict(request_counts) # Convert Counter to dict for storage
    historical_request_data.append((current_time_dt, current_snapshot))

    # Prepare data for Plotly line graph
    # Get all unique backend server addresses that have appeared in the historical data
    all_servers = sorted(list(set(s for _, snapshot in historical_request_data for s in snapshot.keys())))
    
    # Create traces (lines) for each server
    traces = []
    for server_addr in all_servers:
        x_times = []
        y_counts = []
        for timestamp, snapshot in historical_request_data:
            x_times.append(timestamp)
            y_counts.append(snapshot.get(server_addr, 0)) # Get count for this server, 0 if not present at that snapshot

        traces.append(go.Scatter(
            x=x_times,
            y=y_counts,
            mode='lines+markers', # Display lines and markers
            name=server_addr, # Name for the legend
            hovertemplate=f'<b>Server:</b> {server_addr}<br><b>Time:</b> %{{x|%H:%M:%S}}<br><b>Requests:</b> %{{y}}<extra></extra>'
        ))

    # Create Plotly Figure for Line Graph
    fig = go.Figure(data=traces)
    fig.update_layout(
        title_text='Cumulative Requests per Backend Server Over Time',
        xaxis_title='Time',
        yaxis_title='Total Request Count (Cumulative)',
        height=450, # Slightly increased height for better visibility
        margin=dict(l=40, r=40, t=60, b=100), # Adjust margins for better fit
        plot_bgcolor='#f0f0f0', # Light background for plot area
        paper_bgcolor='#f0f0f0', # Light background for figure paper
        hovermode="x unified" # Unified hover for better comparison across lines
    )

    # Calculate live TPS and total requests for the text display
    total_requests_cumulative = sum(request_counts.values())
    tps_last_seconds = len(request_timestamps) / TPS_WINDOW_SECONDS if TPS_WINDOW_SECONDS > 0 else 0
    
    # Update text content displayed on the dashboard
    text_content = html.Span([
        f'Total Requests (Cumulative): {total_requests_cumulative} | ',
        f'TPS (last {TPS_WINDOW_SECONDS}s): {tps_last_seconds:.2f} | ',
        f'Current Time: {datetime.now().strftime("%H:%M:%S")}'
    ])

    return fig, text_content

# --- Main execution block for the Dash app (run by Gunicorn in Docker) ---
# 'server' is the underlying Flask/Werkzeug server object that Gunicorn uses.
server = app.server 

# This code runs when the 'dashboard_app.py' script is imported/executed by Gunicorn.
# It starts the background log tailing thread.
print("Dash app server initializing. Launching log tailing thread...")
log_thread = threading.Thread(target=tail_nginx_log, daemon=True)
log_thread.start()
print("Log tailing thread launched.")


if __name__ == '__main__':
    # This block is for local development/debugging outside of Docker/Gunicorn.
    # The log tailing thread is already started above.
    print("Running Dash app directly (for local debugging).")
    # Set debug=True for local development to see errors and auto-reload.
    # In production, debug should be False.
    app.run_server(debug=True, host='0.0.0.0', port=8050)
