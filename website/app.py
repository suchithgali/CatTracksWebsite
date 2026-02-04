from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import subprocess
import os
import pandas as pd

app = Flask(__name__, static_folder='public/static', static_url_path='/public/static')

#database config
db_url = os.environ.get('DATABASE_URL') #retrieves the environment variable 
if db_url: #if the variable exists set the Flask config to that URL so the app can connect to external databases
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    db_path = os.path.join(app.instance_path, 'cattracks.db') #set the database path
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}' #let Flask know where the database is

db = SQLAlchemy(app) #create the database
df = pd.read_csv('../data/general/all_addresses.csv', dtype=str) #read in the csv file as a backup and each row is a string
df['clean_address'] = df['Address'].str.strip().str.lower() #create a column to act as the index for hashing
df = df.set_index('clean_address') #set the column to use for hashing

class Stops(db.Model):
    stop_id = db.Column(db.Integer, primary_key = True) #database will have a column to track the ID of the stops
    name = db.Column(db.String(100), unique=True, nullable=False) #database table will have a column to hold the stop names 

with app.app_context(): #creates the Flask context which is needed for querying
    db.create_all() #creates the tables in the database


@app.route('/', methods=['GET'])
def index():
    stops = Stops.query.all()
    stop_names = [stop.name for stop in stops]
    return render_template('index.html', stops=stop_names)

@app.route('/planner', methods=['GET', 'POST'])
def planner():
    #variable to hold the message to send to the user
    message = None
    #if sending a post request
    if request.method == 'POST':
        #get the value of the starting and ending stops
        from_stop = request.form.get('from-stops')
        to_stop = request.form.get('to-stops')
        #check if stops exist in database
        from_exists_db = Stops.query.filter_by(name=from_stop).first() is not None
        to_exists_db = Stops.query.filter_by(name=to_stop).first() is not None
        #pass the values of those stops to the backend
        if from_exists_db and to_exists_db:
            script_path = os.path.join(os.path.dirname(__file__), '..', 'build_and_run.sh') #build the parth to build and run
            env = os.environ.copy() #copies the current environment variables
            env['FROM_STOP'] = from_stop #adds from stop to the environemtn variables
            env['TO_STOP'] = to_stop #adds to stop to the current environment variables
            try:
                result = subprocess.run([script_path], env=env, cwd=os.path.dirname(script_path), capture_output=True, text=True) #runs the build and run file with the updated variables
                if result.returncode == 0:
                    message = result.stdout
                else:
                    message = f"Failed to run script: {result.stderr}"
            except Exception as e:
                message = f"Failed to run script: {str(e)}"
        else:
            #fallback to local check in all_addresses then add to db if in all_addresses
            from_target = from_stop
            search_key = from_target.strip().lower()
            from_exists = search_key in df.index

            to_target = to_stop
            search_key = to_target.strip().lower()
            to_exists = search_key in df.index

            if from_exists == True and to_exists == True:
                #add them to the database and pass to the the build and run file
                if not from_exists_db:
                    new_stop = Stops(name=from_stop)
                    db.session.add(new_stop)
                if not to_exists_db:
                    new_stop = Stops(name=to_stop)
                    db.session.add(new_stop)
                db.session.commit()
                # now run the script
                script_path = os.path.join(os.path.dirname(__file__), '..', 'build_and_run.sh')
                env = os.environ.copy()
                env['FROM_STOP'] = from_stop
                env['TO_STOP'] = to_stop
                try:
                    result = subprocess.run([script_path], env=env, cwd=os.path.dirname(script_path), capture_output=True, text=True)
                    if result.returncode == 0:
                        message = result.stdout
                    else:
                        message = f"Failed to run script: {result.stderr}"
                except Exception as e:
                    message = f"Failed to run script: {str(e)}"
            else:
                message = "Invalid stops."
    
    # get all stops for the template
    stops = Stops.query.all()
    stop_names = [stop.name for stop in stops]
    return render_template('liveroutes.html', message=message, stops=stop_names) #renders the index.html file and passes message and stop_names as varaibles

if __name__ == '__main__':
    app.run()