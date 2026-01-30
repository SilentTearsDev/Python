import pyttsx3

Input = input("Enter the text you want to convert to speech: ")

engine = pyttsx3.init()
engine.setProperty("rate", 150)
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

engine.say(Input)
engine.runAndWait()
