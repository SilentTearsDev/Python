#import requests


def get_weather(city):
    url = "https://api.open-meteo.com/v1/forecast?latitude=40.71&longitude=-74.01&current_weather=true"
    print(url.format_map({"city": city}))
    
get_weather("Komárom")