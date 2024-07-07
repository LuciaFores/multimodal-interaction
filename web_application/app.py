# Import all the needed libraries
from flask import Flask, render_template, jsonify
import pandas as pd
import datetime
from vosk import Model, KaldiRecognizer
import pyaudio
from gtts import gTTS
from io import BytesIO
from pygame import mixer
import time
from paddleocr import PaddleOCR
import cv2
from thefuzz import fuzz
import requests
from dotenv import load_dotenv
import os
import threading
from flask_socketio import SocketIO, emit

### MULTIMODAL INTERACTION ###
# define a function that will be used to setup the speech recognition module
def setup_speech_recognition():
    # Load the model and create a recognizer
    model = Model("../model/vosk-model-small-it-0.22")
    recognizer = KaldiRecognizer(model, 16000)
    # setup the microphone to record audio
    mic = pyaudio.PyAudio()
    stream = mic.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8192
    )
    # return the recognizer and the stream
    return recognizer, stream

# define a function that will be used to setup the speech synthesis module
def setup_speech_synthesis():
    # setup the mixer to play the audio
    mixer.init()
    # return the mixer
    return mixer

def setup_ocr():
    # needed for the first run in which the ocr model will be downloaded
    ocr_model = PaddleOCR(lang='it')
    return ocr_model

# define a function that will be used to recognize the speech
def recognize_speech(recognizer, stream):
    # read the audio data from the stream
    data = stream.read(4096)
    # check if the data is empty
    if len(data) == 0:
        return None
    # check if the recognizer has recognized the speech
    if recognizer.AcceptWaveform(data):
        # return the recognized speech
        return recognizer.Result()[14:-3] # remove the first 14 characters and the last 3 characters, needed to remove the metadata
    # return None if the speech is not recognized
    return None

# define a function that will be used to synthesize the speech
def synthesize_speech(text):
    # create a BytesIO object to store the mp3 file
    mp3_fp = BytesIO()
    # create a gTTS object and write the mp3 file to the BytesIO object and so perform the synthesis
    tts = gTTS(text, lang='it')
    tts.write_to_fp(mp3_fp)
    return mp3_fp

# define a function that will be used to play the synthesized speech
def play_speech(mixer, mp3_fp):
    # set the BytesIO object to the beginning of the file
    mp3_fp.seek(0)
    # play the mp3 file
    mixer.music.load(mp3_fp)
    mixer.music.play()
    # wait until the audio is played
    while mixer.music.get_busy():
        time.sleep(0.1)
    return

def get_bot_data(bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    data = response.json()
    return data

def get_chat_id(handle, data):
    for i in data['result']:
        if 'message' in i.keys():
            if i['message']['chat']['username'] == handle:
                return str(i['message']['chat']['id'])

def get_patient_data():
    df_registry = pd.read_csv('../patient_registry.csv')
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")  
    bot_data = get_bot_data(BOT_TOKEN)
    # create a dictionary with the patient data
    patient = {}
    patient['name'] = df_registry['name'][0]
    patient['gender'] = df_registry['gender'][0]
    patient['age'] = int(df_registry['age'][0])
    handle_columns = [col for col in df_registry.columns if col.startswith('cg_handle_')]
    handles = df_registry[handle_columns].values.flatten().tolist()
    patient['chat_ids'] = []
    for handle in handles:
        patient['chat_ids'].append(get_chat_id(handle, bot_data))
    return patient

def get_therapy_plan(day):
    df_therapy_plan = pd.read_csv(f'../therapy_plan/therapy_plan_{day}.csv')
    # create a dictionary with the therapy plan data
    therapy_plan = {}
    # iterate over the therapy plan data and get only the rows for which the column medication_1 is not empty
    for _, row in df_therapy_plan.iterrows():
        if not pd.isna(row['medication_1']): # meaning that the patient must take at least one medication at that time
            # get all the medications that the patient must take at that time
            medications_quantities = row.drop(['hour']).dropna().tolist()
            therapy = [(x, y) for x, y in zip(medications_quantities[::2], medications_quantities[1::2])]
            therapy_plan[row['hour']] = therapy
    return therapy_plan

def speech_synthesis(text, mixer):
    mp3_fp = synthesize_speech(text)
    play_speech(mixer, mp3_fp)
    return

def send_telegram_message(bot_chat_id, bot_message):
   load_dotenv()
   BOT_TOKEN = os.getenv("BOT_TOKEN") 
   send_text = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + bot_chat_id + '&parse_mode=Markdown&text=' + bot_message
   response = requests.get(send_text)
   return response.json()

def send_help_message(patient, mixer):
    has_multiple_caregivers = len(patient['chat_ids']) > 1
    if has_multiple_caregivers:
        text = f"{patient['name']} invio un messaggio ai tuoi caregiver."
    else:
        text = f"{patient['name']} invio  un messaggio al tuo caregiver."
    speech_synthesis(text, mixer)
    for chat_id in patient['chat_ids']:
        send_telegram_message(chat_id, f"/sendhelp<{patient['name']}>")
    if has_multiple_caregivers:
        text = f"Okay {patient['name']}, ho inviato un messaggio ai tuoi caregiver, ti contatteranno al più presto."
    else:
        text = f"Okay {patient['name']}, ho inviato un messaggio al tuo caregiver, ti contatterà al più presto."
    speech_synthesis(text, mixer)
    return

def greet_patient(patient, mixer):
    text = f"Ciao {patient['name']}, come ti senti?"
    speech_synthesis(text, mixer)
    return

def speech_therapy_plan_info(patient, medications, mixer):
    text = f"{patient['name']} è il momento di prendere i seguenti farmaci: "
    for medication in medications:
        text += medication[0] + ", "
    speech_synthesis(text, mixer)
    text = "Per ogni farmaco mi mostrerai la scatola e io ti dirò se è quella corretta;"
    text += "nel caso in cui lo sia ti dirò quanto prenderne"
    speech_synthesis(text, mixer)
    return

def analyze_feelings(patient, feelings, mixer, stream, recognizer):
    has_multiple_caregivers = len(patient['chat_ids']) > 1
    if feelings.startswith("ben"):
        socketio.emit('background_event_change', {'image': 'medication_happy_background.jpg'})
        text = f"Bene {patient['name']}, sono contento di sentire che ti senti bene!"
        speech_synthesis(text, mixer)
        return "bene"
    elif feelings.startswith("mal"):
        socketio.emit('background_event_change', {'image': 'medication_sad_background.jpg'})
        text = f"Mi dispiace {patient['name']}, spero tu ti senta meglio presto."
        if has_multiple_caregivers:
            text += "Vuoi inviare un messaggio di aiuto ai tuoi caregiver?"
        else:
            text += "Vuoi inviare un messaggio di aiuto al tuo caregiver?"
        speech_synthesis(text, mixer)
        while True:
            speech = None
            stream.start_stream()
            while speech == None:
            # wait for the patient to say something
                speech = recognize_speech(recognizer, stream)
            stream.stop_stream()
            if speech.startswith("sì"):
                socketio.emit('background_event_change', {'image': 'alert_background.jpg'})
                send_help_message(patient, mixer)
                break
            elif speech.startswith("no"):
                break
            else:
                text = "Scusa non ho capito, potresti rispondermi con sì o no?"
                speech_synthesis(text, mixer)
        return "male"
    else:
        text = "Scusa non ho capito, potresti rispondermi con bene o male?"
        speech_synthesis(text, mixer)
        return ""
    
def speech_medication_instructions(medication, mixer):
    text = f"Prendi {medication}; quando sei pronto a farmi riconoscere la scatola dimmi foto."
    speech_synthesis(text, mixer)
    return

# define a function to take a picture of the medication box
# and save the picture in the folder medications/today/{medication}.jpg
def take_picture(today, medication):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture device.")
        return
    # Capture a single frame
    ret, frame = cap.read()
    # Release the webcam
    cap.release()
    if not ret:
        print("Error: Could not read frame from video capture device.")
        return
    cv2.imwrite(f'../medications/{today}/{medication}.jpg', frame)
    return

# define a function to recognize the medication box
# the function will perform OCR on the image, then if the parameter medication of the function
# is similar to one of the results of the OCR it will return True, otherwise False
def recognize_medication(today, medication, ocr_model, threshold=80):
    img_path = f'../medications/{today}/{medication}.jpg'
    results = ocr_model.ocr(img_path)
    if results != [None]:
        for result in results:
            for item in result:
                predicted_name, _ = item[1]
                predicted_name = predicted_name.lower()
                if fuzz.partial_ratio(medication, predicted_name) >= threshold:
                    return True
    return False

def get_medication_instructions(patient, quantity, mixer):
    text = f"Bene {patient['name']} è la scatola corretta, devi prenderne {quantity}."
    text += "Quando sei pronto a procedere con il prossimo farmaco pronuncia avanti"
    speech_synthesis(text, mixer)
    return

def goodbye_patient(patient, mixer):
    has_multiple_caregivers = len(patient['chat_ids']) > 1
    text = f"Bene {patient['name']} hai preso tutti i farmaci necessari."
    if has_multiple_caregivers:
        text += "Ora invierò un messaggio di riepilogo ai tuoi caregiver"
    else:
        text += "Ora invierò un messaggio di riepilogo al tuo caregiver"
    text += "Noi ci risentiamo quando dovrai prendere i prossimi farmaci."
    text += "Intanto, nel caso tu abbia bisogno di aiuto, ricorda di pronunciare aiuto"
    if has_multiple_caregivers:
        text += "così invierò un messaggio di aiuto ai tuoi caregiver"
    else:
        text += "così invierò un messaggio di aiuto al tuo caregiver"
    speech_synthesis(text, mixer)
    return

def send_recap_message(patient, feeling, today, hour, minute):
    for chat_id in patient['chat_ids']:
        send_telegram_message(chat_id, f"/sendrecap<{patient['name']}><{feeling}><{today}-{hour}:{minute}>")
    return

def delete_images(today):
    if os.listdir(f'../medications/{today}'):
        for image in os.listdir(f'../medications/{today}'):
            os.remove(f'../medications/{today}/{image}')
    return

def interaction():
    patient = get_patient_data()
    # define the starting day
    last_day = 'monday'
    today = ''
    # setup the speech recognition module
    recognizer, stream = setup_speech_recognition()
    # setup the speech synthesis module
    mixer = setup_speech_synthesis()
    # setup the ocr module
    ocr_model = setup_ocr()
    while True:
        speech = None
        feeling = None
        # get the current day and update if needed the therapy plan
        today = time.strftime('%A').lower()
        if today != last_day:
            therapy_plan = get_therapy_plan(today)
            last_day = today 
        # start the speech recognition
        stream.start_stream()
        # if the user says "aiuto" start the help procedure
        speech = recognize_speech(recognizer, stream)
        if speech != None and 'aiuto' in speech:
            stream.stop_stream()
            socketio.emit('background_event_change', {'image': 'alert_background.jpg'})
            send_help_message(patient, mixer)
            speech = None
            stream.start_stream()
            socketio.emit('background_idle_change', {'image': 'background.jpg'})
        # if the helper finds out that is time to take a medication start the therapy plan procedure
        current_time = time.strftime('%H:%M', time.localtime())
        if current_time in therapy_plan.keys():
            stream.stop_stream()
            socketio.emit('background_event_change', {'image': 'medication_background.jpg'})
            delete_images(today)
            # greet the patient and ask them how they are feeling
            greet_patient(patient, mixer)
            # to simulate a do while loop
            while True:
                speech = None
                stream.start_stream()
                while speech == None:
                # wait for the patient to say something
                    speech = recognize_speech(recognizer, stream)
                stream.stop_stream()
                feeling = analyze_feelings(patient, speech, mixer, stream, recognizer)
                if feeling != "":
                    break
            socketio.emit('background_event_change', {'image': 'medication_background.jpg'})
            # get the current medications to take
            medications = therapy_plan[current_time]
            # pronunce the therapy plan rules
            speech_therapy_plan_info(patient, medications, mixer)
            for medication, quantity in medications:
                socketio.emit('background_event_change', {'image': 'medication_background.jpg'})
                speech_medication_instructions(medication, mixer)
                box_recognized = False
                # while the box is not recognized
                while not box_recognized:
                    socketio.emit('background_event_change', {'image': 'photo_background.jpg'})
                    stream.start_stream()
                    while True:
                        speech = None
                        speech = recognize_speech(recognizer, stream)
                        if speech != None and 'foto' in speech:
                            break
                    stream.stop_stream()
                    take_picture(today, medication)
                    # recognize the medication box
                    box_recognized = recognize_medication(today, medication, ocr_model)
                    if box_recognized:
                        socketio.emit('background_event_change', {'image': 'medication_happy_background.jpg'})
                        get_medication_instructions(patient, quantity, mixer)
                        stream.start_stream()
                        while True:
                            speech = None
                            speech = recognize_speech(recognizer, stream)
                            if speech != None and 'avanti' in speech:
                                break
                    else:
                        socketio.emit('background_event_change', {'image': 'medication_sad_background.jpg'})
                        text = "Scusa non è la scatola corretta, potresti riprovare?"
                        speech_synthesis(text, mixer)
            stream.stop_stream()
            socketio.emit('background_event_change', {'image': 'medication_background.jpg'})
            goodbye_patient(patient, mixer)
            current_hour = time.strftime('%H')
            current_minute = time.strftime('%M') 
            send_recap_message(patient, feeling, today, current_hour, current_minute)
            socketio.emit('background_idle_change', {'image': 'background.jpg'})


### UI ###
app = Flask(__name__)
socketio = SocketIO(app)

# Function to translate to italian the current day
def translate_day(day):
    italian_days = {
        'monday': 'Lunedì',
        'tuesday': 'Martedì',
        'wednesday': 'Mercoledì',
        'thursday': 'Giovedì',
        'friday': 'Venerdì',
        'saturday': 'Sabato',
        'sunday': 'Domenica'
    }
    return italian_days[day]

# Function to get the current day of the week
def get_current_day():
    return datetime.datetime.now().strftime('%A').lower()

# Function to read the CSV file for the current day
def get_therapy_plan_display(day):
    file_path = f'../therapy_plan/therapy_plan_{day}.csv'
    df = pd.read_csv(file_path)

    # Drop rows where all columns except "Hour" are NaN
    df = df.dropna(subset=df.columns.difference(['hour']), how='all')

    # Replace NaN values with empty strings
    df = df.fillna('')

    # Rename the columns
    column_mapping = {'hour': 'Orario'}
    for i in range(1, (len(df.columns) - 1) // 2 + 1):
        column_mapping[f'medication_{i}'] = f'Medicinale {i}'
        column_mapping[f'quantity_medication_{i}'] = f'Quantità {i}'

    df = df.rename(columns=column_mapping)

    return df

@app.route('/')
def index():
    current_day = get_current_day()
    display_day = translate_day(get_current_day())
    therapy_plan_display = get_therapy_plan_display(current_day)
    return render_template('index.html', therapy_plan_display=therapy_plan_display.to_dict(orient='records'), columns=therapy_plan_display.columns, current_day=current_day, display_day=display_day)

@app.route('/current_time')
def current_time():
    now = datetime.datetime.now()
    day_of_week = now.strftime('%A').lower()  # Get full day name in English and convert to lowercase
    italian_day = translate_day(day_of_week)  # Translate day to Italian
    date_str = now.strftime(f'{italian_day} - %d/%m/%Y')  # Format date with Italian day
    time_str = now.strftime('%H:%M:%S')  # Format time
    return jsonify(date=date_str, time=time_str)

@app.route('/next_medication')
def next_medication():
    now = datetime.datetime.now().strftime('%H:%M')  # Get current time as HH:MM
    therapy_plan_alert = get_therapy_plan(get_current_day())

    # Find the next medication time after the current time
    next_time = None
    next_medications = None
    for time in sorted(therapy_plan_alert.keys()):
        if time > now:
            next_time = time
            next_medications = therapy_plan_alert[time]
            break

    if next_time:
        return jsonify(time=next_time, medications=next_medications)
    else:
        return jsonify(time=None, medications=None)

if __name__ == '__main__':
    background_thread = threading.Thread(target=interaction)
    background_thread.start()
    socketio.run(app, debug=False)
