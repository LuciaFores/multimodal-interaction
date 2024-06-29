from flask import Flask, render_template, jsonify
import pandas as pd
import datetime
import os

app = Flask(__name__)

# Function to get the current day of the week
def get_current_day():
    return datetime.datetime.now().strftime('%A').lower()

def get_therapy_plan(day):
    file_path = f'../therapy_plan/therapy_plan_{day}.csv'
    df = pd.read_csv(file_path)
    # Drop rows where all columns except "Hour" are NaN
    df = df.dropna(subset=df.columns.difference(['hour']), how='all')
    # Replace NaN values with empty strings
    df = df.fillna('')
    return df

@app.route('/')
def index():
    current_day = get_current_day()
    therapy_plan = get_therapy_plan(current_day)
    return render_template('index.html', therapy_plan=therapy_plan.to_dict(orient='records'), columns=therapy_plan.columns, current_day=current_day)

@app.route('/current_time')
def current_time():
    now = datetime.datetime.now()
    date_str = now.strftime('%a - %d/%m/%Y')
    time_str = now.strftime('%H:%M:%S')
    return jsonify(date=date_str, time=time_str)

if __name__ == '__main__':
    app.run(debug=True)
