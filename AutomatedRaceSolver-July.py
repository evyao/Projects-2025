import pandas as pd
import numpy as np
import requests
import csv
import math
from datetime import datetime

SOLAR_RAY_EFFICIENCY_PERCENTAGE = xxx
ARRAY_SIZE = xxx
LAP_LENGTH = xxx
BATTERYKWH = xxx

api_key = xxx
latitude = xxx  #Replace with race location's latitude
longitude = xxx  #Replace with race location's longitude

live = f'https://api.solcast.com.au/data/live/radiation_and_weather?latitude={latitude}&longitude={longitude}&hours=168&api_key={api_key}&format=json'
live_response = requests.get(live)
forecast = f'https://api.solcast.com.au/data/forecast/radiation_and_weather?latitude={latitude}&longitude={longitude}&hours=336&api_key={api_key}&format=json'
forecast_response = requests.get(forecast)
print("ran")

day_one = "2025-07-05"
day_two = "2025-07-06"
day_three = "2025-07-07"

if forecast_response.status_code == 200 and live_response.status_code == 200:
    try:
        live_data = live_response.json()
        forecast_data = forecast_response.json()
        day_one_ghi = [entry['ghi'] for entry in live_data['estimated_actuals'] if entry['period_end'][:10] == day_one]
        day_one_ghi.reverse()
        day_two_ghi = [entry['ghi'] for entry in live_data['estimated_actuals'] if entry['period_end'][:10] == day_two]
        day_two_ghi.reverse()
        day_three_ghi = [entry['ghi'] for entry in live_data['estimated_actuals'] if entry['period_end'][:10] == day_three]
        day_three_ghi.reverse()
        day_one_ghi.extend([entry['ghi'] for entry in forecast_data['forecasts'] if entry['period_end'][:10] == day_one])
        day_two_ghi.extend([entry['ghi'] for entry in forecast_data['forecasts'] if entry['period_end'][:10] == day_two])
        day_three_ghi.extend([entry['ghi'] for entry in forecast_data['forecasts'] if entry['period_end'][:10] == day_three])
        
        print("Data retrieved successfully:")
        print("Day 1: ", day_one_ghi, len(day_one_ghi))
        print("Day 2: ", day_two_ghi, len(day_two_ghi))
        print("Day 3: ", day_three_ghi, len(day_three_ghi))
    except requests.JSONDecodeError:
        print("Error: Response is not in JSON format.")
else:
    print("Error fetching data:", live_response.status_code, live_response.text, forecast_response.status_code, forecast_response.text)

Car_Power = [xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx, xxx] #Power consumption for each speed value
Speeds_Array = [15, 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]

#Speed Lower Bound: returns index of lower bound speed
def Find_Lower_Bound(curr_speed): 
    i = 0
    while(curr_speed > Speeds_Array[i]):
        i += 1
    return max(0, i-1)

#Speed Upper Bound: returns index of lower bound speed
def Find_Upper_Bound(curr_speed):
    return Find_Lower_Bound(curr_speed) + 1
    
#Formula: (Power due to Incline + Power Estimated)*0.5-Energy In
def energy_net(power_due_to_incline, power_estimated, energy_in):
    return (power_due_to_incline + power_estimated) * 0.5 - energy_in

#Formula: Previous Battery Value - (Energy Net / (Battery in kWh*1000))
def soc_estimated(prev_battery, energy_net, batterykwh):
    return prev_battery - (energy_net / (BATTERYKWH*1000))

#Formula: 60*Length (miles) / Target Speed (mph); Output in minutes
def lap_time(length, target_speed):
    return 60 * length / target_speed

def soc_change(battery_value):
    return battery_value[-2] - battery_value[-1]
    
#Power coming from the sun; ghi should be the latest value of a GHI array
def solar_power(ghi):
    return ghi * SOLAR_RAY_EFFICIENCY_PERCENTAGE * ARRAY_SIZE

#Charging of car while stationary
def charging(current_battery, ghi):
    battery_val = current_battery
    for ghi_val in ghi:
        power_in = solar_power(ghi_val)
        energy_in = energy_net(0, 0, 0.5*power_in)
        battery_val = soc_estimated(battery_val, energy_in, BATTERYKWH)
    if battery_val >= 1:
        battery_val = 1
    print("Charging: ", ghi)
    print("Battery has been charged to: " + str(round(battery_val, 2)))
    return battery_val

day_one_speed = int(input("Day One Average Speed (in mph) "))
day_two_speed = int(input("Day Two Average Speed (in mph) "))
day_three_speed = int(input("Day Three Average Speed (in mph) "))
track_length = xxx #Replace with race track length in miles

GHI_day_one = day_one_ghi[xxx:xxx] #Conversion between UTC to time zone of race location
GHI_day_two = day_two_ghi[xxx:xxx]
GHI_day_three = day_three_ghi[xxx:xxx]

def estimate_one_day(avg_speed, start_of_day_battery, num_laps, GHI_Testing):
        solarPowerArray = []
        energyInArray = []
        energyNetArray = []
        powerNetArray = []
        powerEstimatedArray = []
        batteryArray = []
        lowerBoundSpeedArray = []
        upperBoundSpeedArray = []
        numLaps = []
        invalid = False
        for i in range(0, 16): #8 hours of race, broken into 30 minute intervals
            lowerIndex = Find_Lower_Bound(avg_speed)
            upperIndex = Find_Upper_Bound(avg_speed)
            lowerSpeed = Speeds_Array[lowerIndex]
            upperSpeed = Speeds_Array[upperIndex]
            lowerBoundSpeedArray.append(round(lowerSpeed, 2))
            upperBoundSpeedArray.append(round(upperSpeed, 2))
            powerEstimated = (Car_Power[upperIndex] - Car_Power[lowerIndex])*(avg_speed - lowerSpeed)/(upperSpeed - lowerSpeed) + Car_Power[lowerIndex]
            #if (i+1)%4 == 0 and i != 15:
            #    powerEstimated = 2/3*powerEstimated #Accounting for 10 minute pitstops, which occur every 2 hrs
            powerEstimatedArray.append(round(powerEstimated, 2))
            solarPowerArray.append(round(solar_power(GHI_Testing[i]), 2))
            energyInArray.append(round(0.5*solarPowerArray[i], 2))
            energyNetArray.append(round(energy_net(0, powerEstimatedArray[i], energyInArray[i]), 2))
            powerNetArray.append(round(solarPowerArray[i] - powerEstimatedArray[i], 2))
            if i == 0:
                batteryArray.append(round(start_of_day_battery, 2))
            else:
                batteryArray.append(round(batteryArray[-1] - powerEstimatedArray[i]*0.5/(BATTERYKWH*1000), 2))
            numLaps.append(num_laps + math.floor(avg_speed*(i*0.5)/track_length))
            if (batteryArray[-1] < 0) and invalid == False:
                print("Too fast, invalid speed input")
                invalid = True
                #break
        print("Lower Bound Speed Array: ", lowerBoundSpeedArray)
        print("Upper Bound Speed: ", upperBoundSpeedArray)
        print("Power Estimated: ", powerEstimatedArray)
        print("Solar Power: ", solarPowerArray)
        print("Energy In: ", energyInArray)
        print("Energy Net: ", energyNetArray)
        print("Net Power: ", powerNetArray)
        print("Battery: ", batteryArray)
        print("Number of Laps: ", numLaps)
        return batteryArray[-1], numLaps[-1]

def main():
    print("DAY 1--------------------------------------------------------")
    day_one_battery, day_one_laps = estimate_one_day(day_one_speed, 1, 0, GHI_day_one)
    day_one_battery = charging(day_one_battery, day_two_ghi[xxx:xxx]) #DAY 1: evening charge
    print("DAY 2--------------------------------------------------------")
    day_one_battery = charging(day_one_battery, day_two_ghi[xxx:xxx]) #DAY 2: morning charge
    day_two_battery, day_two_laps = estimate_one_day(day_two_speed, day_one_battery, day_one_laps, GHI_day_two)
    day_two_battery = charging(day_two_battery, day_three_ghi[xxx:xxx]) #DAY 2: evening charge
    print("DAY 3--------------------------------------------------------")
    day_two_battery = charging(day_two_battery, day_three_ghi[xxx:xxx]) #DAY 3: morning charge
    day_three_battery, day_two_laps = estimate_one_day(day_three_speed, day_two_battery, day_two_laps, GHI_day_three)

main()