import graphiti
import nest_thermostat
import requests

from configobj import ConfigObj

config = ConfigObj('nest.conf')

# Nest Credentials
USERNAME = config['nest']['user']
PASSWORD = config['nest']['pass']

# Carbon config
HOSTNAME = config['graphite']['hostname']
PORT = int(config['graphite']['port'])

c = graphiti.Client(host=HOSTNAME, port=PORT)

WEATHER_URL = 'http://weather.nest.com/weather/v1?query=%s'


def ctf(temp):
    return nest_thermostat.utils.c_to_f(temp)


def main():
    nest = nest_thermostat.Nest(USERNAME, PASSWORD)

    structures = nest.structures
    # Graphiti batching?
    for s in structures:
        s_name = s.name.lower()
        zipcode = s.postal_code
        r = requests.get(WEATHER_URL % zipcode)
        wdata = r.json()
        outer_temp = wdata[zipcode]['current']['temp_f']
        outer_humidity = wdata[zipcode]['current']['humidity']
        c.send(('nest', s_name, 'outside_temp'), outer_temp)
        c.send(('nest', s_name, 'outside_humidity'), outer_humidity)
        for d in s.devices:
            d_name = d.name.lower()
            c.send(('nest', s_name, d_name, 'temperature'), ctf(d.temperature))
            c.send(('nest', s_name, d_name, 'target'), ctf(d.target))
            c.send(('nest', s_name, d_name, 'humidity'), d.humidity)
    # Flush data
    c.stop()

if __name__ == '__main__':
        main()
