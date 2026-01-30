from flask import Flask, request, render_template
import subprocess
import os

app = Flask(__name__, static_folder='.', static_url_path='/')

# List of valid stops
valid_stops = [
    "University Transit Center",
    "Mercy Hospital / Tri-College (Southbound)",
    "El Portal Plaza & G St. (Southbound)",
    "G St. & W. Alexander Ave. (Paul's Place)",
    "Granville Apartments",
    "G St. & W. Alexander Ave. (76 Gas Station)",
    "Rite Aid / Walgreens",
    "El Portal Plaza & G St. (Northbound)",
    "Mercy Hospital / Tri-College (Northbound)",
    "M Circle Bus Stop",
    "781 Irma Drive",
    "Merced Mall Target",
    "Amtrak Station",
    "Yosemite Crossings Shopping Center"
]

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', stops=valid_stops)

@app.route('/planner', methods=['GET', 'POST'])
def planner():
    message = None
    if request.method == 'POST':
        from_stop = request.form.get('from-stops')
        to_stop = request.form.get('to-stops')
        
        if from_stop in valid_stops and to_stop in valid_stops:
            script_path = os.path.join(os.path.dirname(__file__), '..', 'build_and_run.sh')
            env = os.environ.copy()
            env['FROM_STOP'] = from_stop
            env['TO_STOP'] = to_stop
            try:
                subprocess.run([script_path], env=env, cwd=os.path.dirname(script_path))
            except Exception as e:
                message = f"Failed to run script: {str(e)}"
        else:
            message = "Invalid stops."
    
    return render_template('index.html', message=message, stops=valid_stops)

if __name__ == '__main__':
    app.run()