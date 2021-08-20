# AUTOBILL 1.5
# Automatically pulls the power draw from O&G solar fields
# broken down by on-peak and off-peak draw

# Copyright 2021, Julia Hoffman
# No use or modification without explicit permission

# Icon from flaticon.com (https://www.flaticon.com/free-icon/sun-energy_931797?related_id=931848&origin=search)

###############################################################################
# UPDATE LOG:

# Version 1.0:
# - Wrote code for main functionality

# Version 1.1:
# - Fixed catastrophic error that caused code to crash upon displaying results (type error)
# - Created functional executable using PyInstaller
# - Added progress counter 

# Version 1.2:
# - Added functionality for Bridgeport and Torrington sites

# Version 1.3:
# - Changed the computation method for Torrington to account for error with Solrenview
# - Added progress bar
# - Added icon :)

# Version 1.4:
# - Fixed error that occured if there was no generation on a day in Torrington
# - Changed error handling

# Version 1.5:
# - Updated the calculations to no longer need a DST lookup table (will NOT break in 2026)
# - Changed error reporting (now tells user full error message)
###############################################################################

import requests, datetime
# Need requests to pull the data, datetime to handle the dates
# datetime is part of the python standard library, requests is not
# Both, however, are bundled with the executable (no modules needed to run it!)


def isDST(dateObj):
    # Takes a datetime.date object and returns if a given date is in DST
    # Returns a bool (TRUE if in DST, FALSE if not)
    
    year = dateObj.year

    # Get start and end dates
    dstStartDate = datetime.date(year, 3, 1)
    count = 0
    while count < 2:
        # Start is the 2nd Sunday in March
        dstStartDate += datetime.timedelta(days=1)
        if dstStartDate.weekday() == 6: count += 1

    dstEndDate = datetime.date(year, 10, 31)
    count = 0
    while count < 1:
        # End is the 1st Sunday in November
        dstEndDate += datetime.timedelta(days=1)
        if dstEndDate.weekday() == 6: count += 1

    # If the date is in between the start and end dates, it's in DST
    return dstStartDate <= dateObj < dstEndDate


def pullDateData(dateObj, siteID):
    # Pulls the date's JSON file of all the power produced, and returns it binned 
    # into on- and off-peak production
    # Takes a datetime.date object, and also which site
    # Returns the tuple (offPkHrs, onPkHours), except for Torrington, where it returns (totalHours, 0)

    kWhOnPk = 0
    kWhOffPk = 0

    # Uses requests to pull the JSON file from solrenview
    dateObjTmr = dateObj + datetime.timedelta(days=1)
    if siteID == 0:
        linkToPull = # link removed for security
    elif siteID == 1:
        linkToPull = # link removed for security
    elif siteID == 2:
        linkToPull = # link removed for security
    r = requests.get(linkToPull)

    datasheet = r.json()

    # Annoyingly, the sum of the hour-by-hour breakdown isn't exactly the same as the recorded daily total, 
    # so for the Torrington site (which doesn't bill diffrently on- or off-pk), I use the daily recorded total
    # Of course then I have to deal with a diffrent JSON file...
    if siteID == 2: # If we're in Torrington
        
        # The good news is that I only need one value from this sheet
        # The bad news is that it's a string, and I'd like a float

        # I had issues where no solar was produced in a day, so the only data was ''
        # '', of course, isn't a float
        if datasheet["dataset"][0]["data"][1]["value"] != "":
            data = float(datasheet["dataset"][0]["data"][1]["value"])
        else: 
            data = 0

        return data, 0

    else: #If we are *not* in Torrington

        # By default, everything is a string, and times are am/pm
        # So I clean them up, and convert it all to a dictionary in the form {time (24hr): energy}
        # time is an int, energy is a float
        dataset = dict()
        for dataPtIndex in range(0, len(datasheet["categories"][0]["category"])):
            time = datasheet["categories"][0]["category"][dataPtIndex]["label"]
            if time[1] == " " and time[2] == "p": time = int(time[0])+ 12
            elif time[1] == " ": time = int(time[0])
            elif time[3] == "p" and time[1] != "2": time = int(time[0:2]) + 12
            else: time = int(time[0:2])
            
            data = datasheet["dataset"][0]["data"][dataPtIndex]["value"]
            if data == '': data = 0
            else: data = float(data)

            dataset.update({time : data})

        # If it's the weekend, power is all off-peak
        if dateObj.weekday() > 4:
            for dataPt in dataset:
                kWhOffPk += dataset[dataPt]

        # DST changes when on-peak hrs are
        elif not isDST(dateObj):
            for dataPt in dataset:
                if dataPt < 12 or dataPt > 20: kWhOffPk += dataset[dataPt] # on-peak is 12-8 in the winter
                else: kWhOnPk += dataset[dataPt]
        
        else:
            for dataPt in dataset:
                if dataPt < 13 or dataPt > 21: kWhOffPk += dataset[dataPt] # 1-9 in the summer
                else: kWhOnPk += dataset[dataPt]
        
        return kWhOffPk, kWhOnPk



# Main loop

print("Welcome to Autobill v 1.5")
print("Continue to automatically calculate the energy output of the O&G solar sites \n")
while True:
    # Get which site
    print("Site IDs are as follows:")
    print("Southbury: 0, Bridgeport: 1, Torrington: 2")
    while True:
        try:
            siteID = int(input("Site ID to calculate >> "))
            if siteID in [0,1,2]: break
        except: pass

        print("Please enter a valid site ID")
    
    print("")

    # Get start and end dates for calculation
    while True:
        date = input("Billing cycle start date (MM/DD/YYYY) >> ")

        try:
            if len(date) != 10: 
                print("Please enter a valid date")
                continue

            if int(date[0]) == 0: month = int(date[1])
            else: month = int(date[0:2])

            if int(date[3]) == 0: day = int(date[4])
            else: day = int(date[3:5])

            year = int(date[6:])
            if year < 1 or year > 9999:
                print("Please enter a date between 1 CE and 9999 CE")
                continue

            stDate = datetime.date(year, month, day)
            break
        except: print("Please enter a valid date")


    while True:
        date = input("Billing cycle end date (MM/DD/YYYY) >> ")

        try:
            if len(date) != 10: 
                print("Please enter a valid date")
                continue

            if int(date[0]) == 0: month = int(date[1])
            else: month = int(date[0:2])

            if int(date[3]) == 0: day = int(date[4])
            else: day = int(date[3:5])

            year = int(date[6:])
            if year < 1 or year > 9999:
                print("Please enter a date between 1 CE and 9999 CE")
                continue

            endDate = datetime.date(year, month, day)
            if endDate < stDate:
                print("Please insure the end date is after the start date")
                continue
            break
        except: print("Please enter a valid date")

    print("\nCalculating...")

    # Now just gotta pull numbers for each day in the cycle and add 'em up!
    kWhOnPk = 0
    kWhOffPk = 0

    delta = endDate-stDate + datetime.timedelta(days=1)
    number = 1

    while stDate <= endDate:
        try:
            # This is NOT efficient, so here's a progress bar so people don't worry
            progressBar = "■"*round((number/delta.days)*30) + " "*(30-round((number/delta.days)*30)) # looks like "■■■■     "
            print(f"Progress: |{progressBar}| {number}/{delta.days}", end="\r")

            dkWhOff, dkWhOn = pullDateData(stDate, siteID)

            # This computation works properly for Southbury and Bridgeport 
            # For Torrington, only kWhOffPk gets incremented
            kWhOffPk += dkWhOff
            kWhOnPk += dkWhOn
            number += 1
        
            stDate += datetime.timedelta(days=1)
        except Exception as e:
            print(f"\nThe following error occured while trying to pull data from {stDate.strftime('%d/%m/%y')}:")
            print(e)
            print("\nIf the error persists, contact Julia Hoffman")

            input("Press ENTER to close the program")
            exit()

    try:    
        if siteID == 0: site = "Southbury"
        elif siteID == 1: site = "Bridgeport"
        elif siteID == 2: site = "Torrington"

        print(f"\n\nResults for {site}:")
        if kWhOnPk+kWhOffPk != 0:
            print(f"Total kWh generated: {round(kWhOnPk+kWhOffPk, 1)}")
            if siteID != 2: print(f"kWh On Peak: {round(kWhOnPk, 1)}, kWh Off Peak: {round(kWhOffPk, 1)}")
            if siteID != 2: print(f"Percent Generation On Peak: {round(kWhOnPk/(kWhOnPk+kWhOffPk)*100)}%")
        else: print("Total kWh generated: 0")

    except Exception as e:
        print("The following error occured while attemting to display the data")
        print(e)
        print("\nIf the error persists, contact Julia Hoffman")

        input("Press ENTER to close the program")
        exit()

    input("\nPress ENTER to run another calculation")
    print("\n")