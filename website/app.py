from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import subprocess
import os

app = Flask(__name__)
app.static_folder = 'public/static'
app.static_url_path = '/public/static'

#database config
db_url = os.environ.get('DATABASE_URL') #retrieves the environment variable 
if db_url: #if the variable exists set the Flask config to that URL so the app can connect to external databases
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    db_path = os.path.join(app.instance_path, 'cattracks.db') #set the database path
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}' #let Flask know where the database is

db = SQLAlchemy(app) #create the database

class Stops(db.Model):
    stop_id = db.Column(db.Integer, primary_key = True) #database will have a column to track the ID of the stops
    name = db.Column(db.String(100), unique=True, nullable=False) #database table will have a column to hold the stop names 

with app.app_context(): #creates the Flask context which is needed for querying
    db.create_all() #creates the tables in the database


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/planner', methods=['GET', 'POST'])
def planner():
    stops = Stops.query.all() #queries all the rows from the table and stores them in the stops variable

    # list to hold the names of the stops
    stop_names = []
    for stop in stops: #for each stop object in Stops
        stop_names.append(stop.name) #add the value of the name attribute of the stop to the stop_names list
    #variable to hold the message to send to the user
    message = None
    #if sending a post request
    if request.method == 'POST':
        #get the value of the starting and ending stops
        from_stop = request.form.get('from-stops')
        to_stop = request.form.get('to-stops')
        #pass the values of those stops to the backend
        if from_stop in stop_names and to_stop in stop_names:
            script_path = os.path.join(os.path.dirname(__file__), '..', 'build_and_run.sh') #build the parth to build and run
            env = os.environ.copy() #copies the current environment variables
            env['FROM_STOP'] = from_stop #adds from stop to the environemtn variables
            env['TO_STOP'] = to_stop #adds to stop to the current environment variables
            try:
                subprocess.run([script_path], env=env, cwd=os.path.dirname(script_path)) #runs the build and run file with the updated variables
            except Exception as e:
                message = f"Failed to run script: {str(e)}"
        else:
            message = "Invalid stops."
    
    return render_template('index.html', message=message, stops=stop_names) #renders the index.html file and passes message and stop_names as varaibles

if __name__ == '__main__':
    app.run()