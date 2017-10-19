import time
import math
 
#import spi library
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
 
#software SPI configuration
CLK = 18
MISO = 23
MOSI = 24
CS = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK,cs=CS,miso=MISO,mosi=MOSI)

#current read declared variable
ISensorPin = 0
ICal = 70.184
ADC_COUNTS = 1024
Ioffset = 512
Isamples = 200
SupplyVoltage = 3.3
ReadingOffset = -2.9

#current read used variables
Irms = 0.0
Isample = 0.0
Ifiltered = 0.0
Isq = 0.0
Isum = 0.0
I_Ratio = 0.0

while True:
        for i in range (1,Isamples):
                Isample = mcp.read_adc(ISensorPin)
                #print(Isample)
                Ioffset = (Ioffset + (Isample - Ioffset)/ 1024)
                #print(Ioffset)
                Ifiltered = Isample - Ioffset
                #print(Ifiltered)
                Isq = Ifiltered*Ifiltered   
                #print(Isq)
                Isum = Isum + Isq
                #print(Isum)
        I_Ratio = ICal * (SupplyVoltage/ADC_COUNTS)
        Irms = I_Ratio*math.sqrt(Isum/Isamples)
        Irms=Irms + ReadingOffset
        print(Irms)
        Isum = 0.0
        Ioffset = 512
