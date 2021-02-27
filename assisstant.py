from __future__ import print_function
import datetime
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pytz
import playsound
import speech_recognition as sr
from gtts import gTTS
import subprocess

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ["january", "february", "march", "april", "may", "june","july", "august", "september","october", "november", "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def speak(text):
    '''
        Using the default audio output, it speaks the words 
        specified in the text (string) parameter. 
    '''
    tts = gTTS(text=text, lang='en')
    filename = 'voice.mp3'
    tts.save(filename)
    playsound.playsound(filename)
    os.remove("voice.mp3")
    
    
def get_audio():
    '''
    This feature detects the user's voice, translates the audio 
    into text and returns it to the user. Wait for the user to 
    speak to begin translating.
    '''
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""
        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print(str(e))
    return said.lower()


def authenticate_google():
    '''
    The function responsible for performing authentication in google.
    '''
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds)


def get_events(day, service):
    '''
    Get the n amount of events that appear next in our calendar
    '''
    date = (datetime.datetime.combine(day, datetime.datetime.min.time())).astimezone(pytz.UTC)
    end = (datetime.datetime.combine(day, datetime.datetime.max.time())).astimezone(pytz.UTC)
    events_result = service.events().list(calendarId='primary', 
                                          timeMin=date.isoformat(), 
                                          timeMax=end.isoformat(),
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f"You have {len(events)} events on this day.")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split("-")[0])
            if int(start_time.split(":")[0]) < 12:
                start_time = start_time + "am"
            else:
                start_time = str(int(start_time.split(":")[0])-12)
                start_time = start_time + "pm"
            speak(event["summary"] + " at " + start_time)


def get_date(text):
    '''
    Parse the text passed in parameter and look for a month and/or a day.
    '''
    text = text.lower()
    today = datetime.date.today()
    if text.count("today") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)

    if month < today.month and month != -1:
        year = year+1
    if month == -1 and day != -1:  
        month = today.month + 1 if day < today.day else today.month
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week
        if dif < 0:
            dif += 7
            if text.count("next") >= 1:
                dif += 7
        return today + datetime.timedelta(dif)
    if day != -1:  
        return datetime.date(month=month, day=day, year=year)
    
    
def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + "-note.txt"
    with open(file_name, "w") as f:
        f.write(text)
    subprocess.Popen(["notepad.exe", file_name])
    
    
    
SERVICE = authenticate_google()
print("Start")

CALENDAR_STRS = ["what do i have", "do i have plans", "am i busy"]
NOTE_STRS = ["make a note", "write this down", "remember this", "type this"]

while True:
    print("Listening")
    text = get_audio()
    if text.count('wake up') > 0:
        speak("I am ready")
        text = get_audio()
        for phrase in CALENDAR_STRS:
            if phrase in text:
                date = get_date(text)
                if date:
                    get_events(date, SERVICE)
                else:
                    speak("Please Try Again")     
        for phrase in NOTE_STRS:
            if phrase in text:
                speak("What would you like me to write down? ")
                write_down = get_audio()
                note(write_down)
                speak("I've made a note of that.")