import nfc
import serial, time, sys
import MySQLdb as mdb
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#definition needed for PN532 to function
def connected(taga):
    return

#database info
db_ip = "192.168.42.1"          #ip of the computer with the database
db_usr =  "desktop"             #account name that has permissions to access the database
db_psw = "raspberry"            #password to the account that can access the database
db_db = "rfid"                  #name of the database

MachineId = "Desktop Fan"       #the machine id as it will appear in the log



#Define Variables
check_timeinit = 10                 #how long after initialization to wait before first database check
check_timepass = 20                #how long to wait after a successful database check before doing the next check
check_timefail = 5                 #how long to wait after a failed databse check before doing the next check

read_engaged = 5                #how long do you want the approved card action to take place before next card read
read_disengaged = 1             #how long do you want the disapproved card action to take place before the next card read

blink_time = 1                  #how long do you want to blink the read light if there is a system failure



RELAY = 26                      #pin on pi that will control the relay
GREEN_LED = 19                  #pin on pi that will control the green led
BLUE_LED = 13                   #pin on pi that will control the blue led    
RED_LED = 6                     #pin on the pi that will control the red led
GPIO.setup(RELAY, GPIO.OUT)     #set relay pin as an output
GPIO.setup(BLUE_LED, GPIO.OUT)  #set the blue led pin as an output
GPIO.setup(GREEN_LED, GPIO.OUT) #set the green led pin as an output
GPIO.setup(RED_LED, GPIO.OUT)   #set the red led pin as an output

#Assigned GPIO Starting values
GPIO.output(RELAY, False)       #have the relay start as off
GPIO.output(BLUE_LED, True)     #have the blue led start as on
GPIO.output(RED_LED, False)     #have the red led start as off
GPIO.output(GREEN_LED, False)   #habe the green led start as off

print "RFID Lock-Out Preparing resources"
print

print "Attempting to connect to database"

#Define connection to database and connect
try:
    con = mdb.connect(host= db_ip,     #host = the_ip_of_the_host_computer_that_holds_the_database
                      user= db_usr,     #user = user_name_on_database_with_needed_permissions_todo_required_actions
                      passwd= db_psw,   #passwd = password_of_specified_user_on_database
                      db= db_db,       #db = name_of_database_on_host_computer
                      );               
    #mdb.connect(host= db_ip, user= db_usr, passwd= db_psw, db= db_db,);  
    check_fail = False
    print "Connected to database"
    print
except:
    check_fail = True
    print "Failed to connect to database"
    print

print "Attemtping to connect to RFID Reader"

#Define path to RFID reader, and connect
try:
    clf = nfc.ContactlessFrontend('tty:AMA0:pn532')
    print "RFID Card Reader ready"
    print
    read_fail = False
except:
    read_fail = True
    print "Failed to read from card reader"
    print


#Define initialization variables
Id_last = "null"
Id_cur = "null"

result = ''

check_cycle = check_timeinit
read_cycle = read_disengaged

connect_last = read_last = time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime())
read_lastcycle = blink_last = check_time = time.time()

blink_state = False
usage_active = False

print "System Time" , read_last
print "System ready"
print
try:
    while True:                                         # loop forever until an exception is raised
        thetime = time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime()) # get current time

        #check that you can connect to the database
        if ((time.time() - check_time) > check_cycle):      #if enough time has elapsed check the databse connection again
            try:                                                #try to check the database
                print "Perform Database Check"                      #print to the screen that an attempt to connect to the database has started
                check_start = time.time()
                mdb.connect(host= db_ip, user= db_usr, passwd= db_psw, db= db_db,); 
                cur = con.cursor()                              # activiate cursor in the database
                cur.execute("SELECT name FROM id WHERE card = %s",(Id_cur))  #query the databse for card ID
                null = cur.fetchone()                         # see if card exists and their name
                cur.close()                                     #close the cursor 
                connect_last = time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime())  #make note of when the last database check succeeded incase it fails in the future
                check_cycle = check_timepass                        #change the wait time between checks to a high number 
                check_fail = False                                  #make note that the check had passed
                print "Database Check Complete"                     #print to the screen that the database connection check has succeeded
                print                                               #print blank line to the screen for formating purposed
            except:                                             #if the databse check had failed
                check_cycle = check_timefail                        #change the check time to a low number to check it more frequently till it is able to connect       
                check_fail = True                                   #make note that the check has failed
                print "Database Check Failed"                       #print to the screen that the check has failed
                print "Last connect was", connect_last              #print to the screen when it last worked    
                print                                               #print blank line to the screen for formating purposes
            check_time = time.time()                            #start the database check timer over



        #make sure you can read the RFID reader, and see whats there
        if ((time.time() - read_lastcycle) > read_cycle):       #check if enough time has elapsed since the last card rea
            try:                                                #try to read from rfid reader
                clf = nfc.ContactlessFrontend('tty:AMA0:pn532')     #define path to the RFID reader
                read_timelimit = lambda: time.time() - read_timestart > 0.3     #set time limit for how long to wait for a card to be present
                read_timestart = time.time()                        #start time for card reading duration
                IdRaw = clf.connect(rdwr={'on-connect':connected}, terminate=read_timelimit) #read for any rfid cards, and log their info
                clf.close()                                         #close connection to rfid reader
                IdStr = "%s" %IdRaw                                 #convert card information to a string
                Id_cur = IdStr[12:]                                 #remove the first 12 characters from the string so that only the ID number is left
                if Id_cur == "":                                    #if no card was read
                    Id_cur = "null"                                     #change ID to "null"                              

                if read_fail == True:                               #if the reading had previously failed, but has succeeded this time
                    print "Card Read Successful"                        #print the screen that it has succeeded
                    print                                               #print blank line to the screen for formating purposes
                read_fail = False                                       #make note that the card reading has been successful
                read_last = time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime()) #update the time tracker so that we can know when it worked last if it fails later
            except:                                             #if the rfid reader failed to work
                print "RFID Card Reader Failed"                     #print to the screen that the rfid reader has failed
                print "Last RFID Read", read_last                   #print to the screen the last time it DID work for trouble shooting purposes
                read_fail = True                                    #make note that the card reading has failed
                read_cycle = read_disengaged
                read_lastcycle = time.time()   



        #if something is wrong blink the red LED   
        if ((time.time() - blink_last) > blink_time):   #check if enough time has elapsed to change the led state
            if ((read_fail == True) or (check_fail == True)):
                if blink_state == False:
                    GPIO.output(RED_LED, True)     #have the red led start as off                    
                    blink_state = True
                else:
                    GPIO.output(RED_LED, False)     #have the red led start as off                     
                    blink_state = False
            else:
                if blink_state == True:
                    GPIO.output(RED_LED, False)     #have the red led start as off                     
                    blink_state = False                    
            blink_last = time.time()
        
                    
        #if the RFID has changed and there is nothing wrong in the system
        if ((Id_cur != Id_last) and (check_fail != True) and (read_fail != True)):                               #see if the id has changed
            if Id_last != "null":                               #if the previous id was nulll, then do nothing
                if usage_active == True:                            #if a usgae timer was running
                    usage_time = time.time() - usage_start              #find the usage time by subtracting the start time from the current time
                    usage_time = long(usage_time)                       #convert the number of seconds to a long without any decimals
                    print usage_time , "Seconds of use"                 #print how long the card was active
                    print                                               #print blank line to the screen for formattign purposes
                    try:                                                #try to write the usage data to the database
                        mdb.connect(host= db_ip, user= db_usr, passwd= db_psw, db= db_db,);       
                        cur = con.cursor()                                  #turn on cursor in the database
                        cur.execute("INSERT INTO log VALUES(%s,%s,%s,%s)",(MachineId, result[0], usage_time, thetime))    #add line into log with the usage informations
                        con.commit()                                        #commit the entry to the log
                        cur.close()                                         #close the cursor on the database
                    except:                                             #if failed to write to the databse
                        print "Database logging failed"                     #print to the screen that the writing tot he log had faild
                        check_fail = True
                        check_cycle = check_timefail
                                                
            if Id_cur == "null":                            #if current ID is null, then perform actions for no card present
                GPIO.output(RELAY, False)                       #make sure relay is turned off
                GPIO.output(BLUE_LED, True)                     #turn off blue light
                GPIO.output(RED_LED, False)                     #turn on red led
                GPIO.output(GREEN_LED, False)                   #turn off green led
                read_cycle = read_disengaged                    #change the reading delay to respond quickly for the next card
                print "No Card present"                         #print to the screen that no card is present
                print                                           #print blank line to the screen
                result = ''                                     #change the result to '' to prevent the following steps for falsly exicuting
                usage_active = False                            #make note that the usgae timer is not active
            else:                                           #if ID is not null then look it up in the database
                
                print "RFID Scanned. Tag ID:", Id_cur            # print the tag number
                try:
                    mdb.connect(host= db_ip, user= db_usr, passwd= db_psw, db= db_db,);
                    cur = con.cursor()                              # activiate cursor in the database
                    cur.execute("SELECT name FROM id WHERE card = %s",(Id_cur))  #query the databse for card ID
                    result = cur.fetchone()                         # see if card exists and their name
                    cur.close()                                     #close the cursor 
                except:                                         #if exception thrown do the following
                    print "Database Lookup Failed"                  #print to screen that the databse look up had failed
                    check_fail = True
                    check_cycle = check_timefail
                    print                                           #add empty line to screen

            if not result:                                  #if card not found do this
                if (Id_cur != "null"):                          #if current id isnt null then take the action for a unauthorized card
                    GPIO.output(RELAY, False)                       #make sure relay is off
                    GPIO.output(BLUE_LED, False)                    #turn off blue light
                    GPIO.output(GREEN_LED, False)                   #turn on green led
                    GPIO.output(RED_LED, True)                      #turn off red led
                    read_cycle = read_disengaged                    #change the reading delay to respond quickly for the next card
                    print "UNAUTHORIZED RFID! [",Id_cur,"] scanned at", MachineId,"@",thetime    #print machine and card info for unauthorized card
                    print                                           #add empty line to the screen for formating purposes
                    usage_active = False                            #make note that usage timer is not active
            
            else:                                           #if card is found then do this
                usage_start = time.time()                       #start log of when the card started being used
                usage_active = True                             #make note that usage timer is active
                GPIO.output(RELAY, True)                        #trigger the relay to turn on the equipment
                GPIO.output(BLUE_LED, False)                    #turn off blue light
                GPIO.output(GREEN_LED, True)                    #turn on green led
                GPIO.output(RED_LED, False)                     #turn off the red LED
                read_cycle = read_engaged                       #change the reading delay to give more time for the action
                print result[0],"used",MachineId,"@", thetime   #print machine and user info to the screen for debugging

            if (check_fail != True):
                Id_last = Id_cur                                #after all actions are taken set the current ID as the last ID for the next cycle.
                

except KeyboardInterrupt:                               # if ctrl-c'd , cleanup your mess and exit
    print "Caught interrupt, exiting..."
                              
except:
    print "Unexpected error:", sys.exc_info()[0]
    raise

finally:
    # cleanup code if something goes wrong
    GPIO.cleanup()
    #ser.close()
