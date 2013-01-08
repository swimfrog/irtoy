#!/usr/bin/python

""" The IRToy is fun! (except when it's not [working]) """

import serial
import binascii
import pdb
import getopt, sys

ser = None
device = "/dev/ttyACM0"
global inittimeout
inittimeout = 1
global pausewait
pausewait = 5
verbose = False
input = None
output = None



    
def initSerial(devstr="/dev/ttyACM0", initTimeout=1, initPausewait=5):
    """ Initialize the serial port and return the Serial object """
    theSer = None
    try:
        theSer = serial.Serial(device)
        #ser.baudrate=9600
        theSer.timeout = inittimeout
        theSer.close()
        theSer.open()
    except serial.serialutil.SerialException:
        print "Error occurred opening %s" % (device)
        exit(1)
    return theSer

def reset():
    ser.write("\x00\x00\x00\x00\x00")

def usage():
    print "Usage: toy.py [-v|--verbose] [-h|--help] [-i infile] [-o outfile] [-d device]"

def testDevice():
    reset()
    setMode("test")
    result = ser.read(4)
    if ((result.startswith("V")) and (len(result) == 4)):
        if (verbose): print "IRToy %s, Firmware version: %s" % (result[1:2], result[3:4])
        return True
    return False

def setMode(mode):
    modedict = {
        "sample":"S",
        "irio":"X",
        "bridge":"U",
        "intruder":"E",
        "test":"T",
    }
    modesel = modedict[mode]
    if (modesel):
        ser.write(modesel)
        return True
    return False

def setSampleFrequency(byte):
    if (len(byte)==1):
        ser.write("\x05")
        ser.write(byte)
        return True
    return False

def receiveSequence():
    gotdata = False
    pause = 0
    oldlength = 0
    data = ""
    
    print "Press a button."
    while (pause < pausewait):
        data = data + ser.read(1)
        if (len(data) == oldlength):
            # We timed out.
            if (gotdata == True):
                # If we've seen data before, then increment pause, otherwise we wait forever
                pause += 1
        else:
            # We got some data
            gotdata = True
        oldlength=len(data)
    
    if (verbose): print "OK Received: %s" % (binascii.hexlify(data))
    return data

def transmitSequence(data):
    if (data.endswith("\xff\xff")):
        ser.write("\x03")
        ser.write(data)
        #ser.write("\x00") # Reset back to IRMan mode.
        return True
    return False
    

def writeFile(fileName, data):
    try:
        file = open(fileName, "wb")
        file.write(data)
        return True
    except IOError:
        print "Error writing to file %s" % fileName
    finally:
        file.close()

def readFile(fileName):
    try:
        file = open(fileName, "rb")
        data = file.read()
        return data
    except IOError:
        print "Error reading from file %s" % fileName
    finally:
        file.close()

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvi:o:d:", ["help", "output=", "input=", "verbose", "device=",])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    output = None
    input = None
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        if o in ("-h", "--help"):
            usage()
            sys.exit(2)
        if o in ("-i", "--infile"):
            input = a
        if o in ("-o", "--outfile"):
            output = a
        if o in ("-d", "--device"):
	    global device
            device = a


    if (input and output):
        print "You must specify either input or output, not both"
        usage()
        exit(2)

    global ser
    ser = initSerial()

    if (verbose): print "Resetting device..."
    reset()

    #testDevice()

    setMode("sample")
    response = ser.read(3)
    if (response == "S01"):
        print "IRToy OK"
    else:
        print "Error. No response from IRToy in %d sec" % inittimeout
        exit(2)
    
    data = None
    if (input):
        if (verbose): print "Reading data from %s" % input
        data = readFile(input)
    else:
        if (verbose): print "Reading data from IRToy"
        data = receiveSequence()

    if (data == None):
        print "Could not retrieve data"
        exit(1)

    if (output):
        if (verbose): print "Writing %d bytes of data to %s" % (len(data), output)
        writeFile(output, data)
    else:
        if (verbose): print "Sending via IR" 
        transmitSequence(data)
        if (verbose): print "Done sending" 
        reset()
	setMode("sample")

    #setSampleFrequency("\x04")
    
    #writeFile("/tmp/testfile", data)
    #readFile(data)
    
    #ser.write("\x04")
    #timing=ser.read(8)
    #print(binascii.hexlify(timing))

    #ser.write("\x06") # Setup transmit modulation frequency (PR2)
    #ser.write("\x4d\x00")

    ser.close()

if __name__ == "__main__":
    main()

