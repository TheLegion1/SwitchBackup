from pyntc import ntc_device as NTC
from pyntc import ntc_device_by_name as NTCNAME #for getting switches from a config file
import json
from colorama import Fore, Back, Style
from datetime import date, datetime, timedelta
from threading import Timer
import difflib
import os
import getpass #allows typing passwords in terminal without them being put on screen in plaintext





#variables
switchList = []




#function for setting up a new switch
def add_vlans(switchObj):
    #dictionary of vlans
    vlans = {
    29:'Ancillary(ICU/Admin)',
    30:'Ancillary(Pharm/PATH/WWH/WGS)',
    35:'OR-PACU-R',
    40:'VOIP-R',
    45:'NursingAdmin-R',
    50:'MA/CP/EMR',
    75:'Cameras',
    80:'Pharmacy_POS',
    88:'DMZ',
    100:'IT',
    150:'HugginsSSID',
    151:'HugginsStaffSSID',
    152:'HugginsMDSSID',
    160:'huggins_guest_SSID',
    254:'NetworkManagement',
    444:'FW-HA',
    555:'FW-OUTSIDE-NETC',
    570:'CMC',
    575:'DHMC',
    666:'FW-OUTSIDE-BAYRING',
    900:'Outside_Network'
    }
    #end vlans
    for key in vlans.keys():
        print('Adding Vlan ' + str(key) + ' to the switch')
        #switchObj.config('vlan ' + str(key))
        #switchObj.config('name ' + vlans[key])
        switchObj.config_list(['vlan ' + str(key), 'name ' + vlans[key]])
    print('Added vlans to the switch')



def restoreConfig(switch):
    print("fuckoff m8 sucks 2 b u")




#user function for making a new switch object

#UPDATE added inputs for hostname and Support password
def newSwitch():
    #we assume that the standard local login will apply
    print("Enter the IP of the switch: ")
    hostname = raw_input()
    print('Enter the username for this switch: Blank = Support')
    username = raw_input()
    if username == "":
        username = 'Support'
    print("Enter the Support Password for this switch:")
    password = getpass.getpass()
    print("1. IOS Switch")
    print("2. NxOS Switch")
    switchType = raw_input()
    if(switchType == "1"):
        switchStyle = "cisco_ios_ssh"
    if(switchType == "2"):
        switchStyle = "cisco_nxos_nxapi"
    print("Connecting to " + hostname)
    try:
        switch = createSwitch(hostname, username, password, switchStyle)
    except:
        print(Fore.YELLOW + "Error adding new switch. Exception caught")
        menu() #return to menu after error
    saveConfigFile(switchType, switch, username, password, hostname)
    print("Connected")
    addVlans = raw_input("Would You like to add standard vlans to this switch? y/n")
    if(addVlans == "y"):
        add_vlans(switch)
    menu()


#helper function for newSwitch
def createSwitch(hostname, username, password, Switchtype):
    #types:
    #IOS: cisco_ios_ssh
    #NEXUS: cisco_nxos_nxapi
    tmpSwitch = NTC(host=hostname, username=username, password=password,device_type=Switchtype)
    switchList.append(tmpSwitch.facts['hostname']) #adds the hostname of the switch to our master list of hostnames
    return tmpSwitch

def saveConfigFile(switchType, switchObject, username, password, hostname):
    #look for duplicate entries for the same switches

    #conf_file = open(file_name, 'r') #open file in read only mode
    #lines = conf_file.readlines()
    #for x in lines:
    #    if("[" in x):
            #we found the line that contains the hostname of the switch, now loop through all saves hostnames in SwitchList to compare
    #        for x2 in switchList:
    #            if(x2 in x):
    #                print(Fore.YELLOW + "Error: Switch already exists in config file")
    #                menu()
    #conf_file.close()
    #update the file with the new switch
    print("Updating Switch Config File")
    line1 = '[cisco_ios_ssh:' + switchObject.facts['hostname'] + ']'
    line2 = 'host: ' + hostname
    line3 = 'username: ' + username
    line4 = 'password: ' + password
    if(switchType == "2"):
        line1 = '[cisco_nxos_nxapi' + switchObject.facts['hostname'] + ']'
        line5 = 'transport: http'
    else:
        line5 = 'port: 22'

    #write to the config file
    file_name = 'pyntc.ntc.conf'
    pyntc_config_file = open(file_name, 'a+') #append to file, if doesn't exist create new
    pyntc_config_file.write(line1 + '\n')
    pyntc_config_file.write(line2 + '\n')
    pyntc_config_file.write(line3 + '\n')
    pyntc_config_file.write(line4 + '\n')
    pyntc_config_file.write(line5 + '\n')
    pyntc_config_file.write('\n') #leave a blank line between switches
    pyntc_config_file.close()


def saveHostnames():
    file_name = 'switchList.txt'
    host_file = open(file_name, 'w+') #append to file, if doesn't exist create new
    for x in switchList:
        host_file.write(x + '\n')
    host_file.close()

def loadHostnames():
    file_name = 'switchList.txt'
    host_file = open(file_name, 'r+') #open file in read-only mode
    lines = host_file.readlines()
    for x in lines:
        switchName = x.rstrip("\n")
        switchList.append(switchName)
    host_file.close()

def autoBackupAllSwitchesTime():
    autoBackupAllSwitches()
    x = datetime.today()
    y = x.replace(day=x.day+1, hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
    delta_t = y-x
    secs = delta_t.seconds+1
    t = Timer(secs, autoBackupAllSwitchesTime)
    t.start()

def autoBackupAllSwitches():
    for x in switchList:
        try:
            switch = NTCNAME(x, "pyntc.ntc.conf") #open the switch object from the pyntc config file
            backupConfig(switch) #back up the config
            switch.close() #close the switch object
        except:
            print(Fore.YELLOW + "Error backing up: " + Fore.BLUE + x + Fore.YELLOW + " Exception Caught")


#function that pulls the running config from a given switch object
def backupConfig(switch):
    runningConfig = switch.running_config
    #print(runningConfig)
    hostname = switch.facts['hostname']
    print('Saving config for ' + str(hostname))
    #cmds = []
    #cmd = ('copy run flash:' + str(date.today()) + ".cfg")
    #cmds.append(cmd)
    #cmds.append(str(date.today()) + ".cfg")
    test = switch.save(str(date.today()) + ".cfg")
    #switch.config_list(cmds) #saves the config locally to the switch
    save_path = "/home/support/SwitchBackup/" + hostname + '/' #logic for selecting the correct subfolder on the server
    if(not os.path.exists(save_path)):
        os.mkdir(save_path)
    file_name = hostname + str(date.today()) + '.txt'
    full_file_name = os.path.join(save_path, file_name)

    config_file = open(full_file_name, 'w') #saves a copy of the config local to the server
    config_file.writelines(runningConfig)
    config_file.close()
    print('Config for ' + hostname + ' saved.')



def timedBackupSwitches():
    print("test")

def listSwitches():
    print("Switches Available:" + str(len(switchList)))
    for x in switchList:
        print(x)

def backupSpecific():
    listSwitches()
    print("Enter the name of the Switch to backup or \"quit\" to return to menu")
    if(len(switchList) < 1 or switchList[0] == ""):
        print(Fore.YELLOW + "Error: No switches currently registered")
        menu()
    selected = raw_input("Switch:")
    if(selected not in switchList):
        if(selected == "quit"):
            menu()
        backupSpecific()
        try:
            switch = NTCNAME(selected, "pyntc.ntc.conf")
            backupConfig(switch)
        except:
            print(Fore.YELLOW + "Error backup up switch")

def helpMenu():
    print("--- HELP PAGE ---")
    print(Fore.YELLOW + Style.BRIGHT + "?" + Fore.WHITE + "                  Prints this help page")
    print(Fore.YELLOW + Style.BRIGHT + "backup" + Fore.WHITE + "             Backs up a given switches running config")
    print(Fore.YELLOW + Style.BRIGHT + "backupAll" + Fore.WHITE + "          Backs up all connected switches")
    print(Fore.YELLOW + Style.BRIGHT + "restore" + Fore.WHITE + "            Restores a given switches config from a file")
    print(Fore.YELLOW + Style.BRIGHT + "newSwitch" + Fore.WHITE + "          Adds a new switch to the backup service")
    print(Fore.YELLOW + Style.BRIGHT + "listSwitches" + Fore.WHITE + "       Lists all connected switches")
    print(Fore.YELLOW + Style.BRIGHT + "quit" + Fore.WHITE + "               Exits this program")




def menu():

    userInput = raw_input(Fore.RED + Style.BRIGHT + "Command: ")
    print(Style.RESET_ALL)
    if(userInput == "quit"):
        quit()
    if(userInput == "?"):
        helpMenu()
    if(userInput == "help"):
        helpMenu()
    if(userInput == "backup"):
        backupSpecific()
    if(userInput == "backupAll"):
        autoBackupAllSwitches()
    if(userInput == "restore"):
        restoreConfig(selectSwitch())
    if(userInput == "newSwitch"):
        newSwitch()
    if(userInput == "listSwitches"):
        listSwitches()
    menu()
#main function
if __name__ == "__main__":
    print("---Switch Backup Utility v1.0---")
    loadHostnames()
    x = datetime.today()
    y = x.replace(day=x.day+1, hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
    delta_t = y-x
    secs = delta_t.seconds+1
    #t = Timer(secs, autoBackupAllSwitchesTime)
    #t.start()
    menu()
