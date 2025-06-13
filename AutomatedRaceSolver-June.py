import pandas as pd
import numpy as np
import requests
import csv
import math
from datetime import datetime

SOLAR_RAY_EFFICIENCY_PERCENTAGE = xxx
ARRAY_SIZE = xxx
BATTERYKWH = xxx

api_key = xxx
latitude = xxx  # Replace with race location's latitude
longitude = xxx # Replace with race location's longitude

#Due to limited queries, this is disabled generally
'''url = f'https://api.solcast.com.au/world_radiation/estimated_actuals?latitude={latitude}&longitude={longitude}&format=json&api_key={api_key}'
response = requests.get(url)
print("ran")

if response.status_code == 200:
    try:
        data = response.json()
        ghi_data =[entry['ghi'] for entry in data['estimated_actuals']]
        time_data = [entry['period_end'] for entry in data['estimated_actuals']]
        print("Data retrieved successfully:", ghi_data)
    except requests.JSONDecodeError:
        print("Error: Response is not in JSON format.")
else:
    print("Error fetching data:", response.status_code, response.text)'''

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

'''def UpdateSpeedandPowerArr(curr_speed):
    lowerIndex = Find_Lower_Bound(curr_speed)
    upperIndex = Find_Upper_Bound(curr_speed)
    lowerBoundSpeedArray.append(Speeds_Array[lowerIndex])
    upperBoundSpeedArray.append(Speeds_Array[upperIndex])
    powerEstimatedArray.append(Zephyr_Power[lowerIndex])'''
    
#Formula: (Power due to Incline + Power Estimated)*0.5-Energy In
def energy_net(power_due_to_incline, power_estimated, energy_in):
    return (power_due_to_incline + power_estimated) * 0.5 - energy_in

#Formula: Previous Battery Value - (Energy Net / (Battery in kWh*1000))
def soc_estimated(prev_battery, energy_net, batterykwh):
    return prev_battery - (energy_net / (batterykwh*1000))

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
    print("Battery has been charged to: " + str(round(battery_val, 2)))
    return battery_val

day_one_speed = int(input("Day One Average Speed (in mph) "))
day_two_speed = int(input("Day Two Average Speed (in mph) "))
day_three_speed = int(input("Day Three Average Speed (in mph) "))
track_length = xxx #Replace with race track length in miles
#Sample GHI Values
GHI_day_one = [201, 385, 501, 593, 651, 681, 730, 733, 712, 689, 743, 740, 731, 539, 514, 470]
GHI_day_two = [470, 380, 246, 215, 242, 180, 132, 90, 165, 241, 296, 240, 484, 571, 514, 397]
GHI_day_three = [397, 534, 614, 677, 551, 628, 470, 200, 238, 350, 253, 343, 271, 182, 198, 185]

def estimate_one_day(avg_speed, start_of_day_battery, num_laps, GHI_Testing):
        solarPowerArray = []
        energyInArray = []
        targetSpeedArray = []
        lapTimeArray = []
        energyNetArray = []
        powerNetArray = []
        powerEstimatedArray = []
        batteryArray = []
        lowerBoundSpeedArray = []
        upperBoundSpeedArray = []
        numLaps = []
        invalid = False
        for i in range(0, 16):
            lowerIndex = Find_Lower_Bound(avg_speed)
            upperIndex = Find_Upper_Bound(avg_speed)
            lowerSpeed = Speeds_Array[lowerIndex]
            upperSpeed = Speeds_Array[upperIndex]
            lowerBoundSpeedArray.append(round(lowerSpeed, 2))
            upperBoundSpeedArray.append(round(upperSpeed, 2))
            powerEstimated = (Car_Power[upperIndex] - Car_Power[lowerIndex])*(avg_speed - lowerSpeed)/(upperSpeed - lowerSpeed) + Excalibur_Power[lowerIndex]
            #if (i+1)%4 == 0 and i != 15:
            #    powerEstimated = 2/3*powerEstimated #Enable to account for 10 minute pitstops, which occur every 2 hrs
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
            if (batteryArray[-1] < 0):
                print("Too fast, invalid speed input")
                invalid = True
                break
        if invalid == False:
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
    print("DAY 2--------------------------------------------------------")
    day_one_battery = charging(day_one_battery, [200, 500, 700, 400]) #DAY 1: evening charge
    day_one_battery = charging(day_one_battery, [200, 500, 700, 400]) #DAY 2: morning charge
    day_two_battery, day_two_laps = estimate_one_day(day_two_speed, day_one_battery, day_one_laps, GHI_day_two)
    day_two_battery = charging(day_two_battery, [200, 500, 700, 400]) #DAY 2: evening charge
    day_two_battery = charging(day_two_battery, [200, 400, 500, 700]) #DAY 3: morning charge
    print("DAY 3--------------------------------------------------------")
    day_three_battery, day_two_laps = estimate_one_day(day_three_speed, day_two_battery, day_two_laps, GHI_day_three)

main()