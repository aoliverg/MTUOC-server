import codecs
import os
import sys

try:
    entrada=codecs.open("MarianServerPID.pid","r",encoding="utf-8")
    for linia in entrada:
        pid=linia.strip()
        try:
            command="kill "+pid
            print(command)
            os.system(command)
        except:
            print("Error stopping Marian.",sys.exc_info())
    command="rm MarianServerPID.pid"
    print(command)
    os.system(command)
except:
    print("Error stopping Marian.",sys.exc_info())
    


try:
    entrada=codecs.open("MTUOCServerPID.pid","r",encoding="utf-8")
    for linia in entrada:
        pid=linia.strip()
        try:
            command="kill "+pid
            print(command)
            os.system(command)
        except:
            print("Error stopping MTUOC.",sys.exc_info())
    command="rm MTUOCServerPID.pid"
    print(command)
    os.system(command)
except:
    print("Error stopping MTUOC.",sys.exc_info())


try:
    entrada=codecs.open("MTUOCWatchdogPID.pid","r",encoding="utf-8")
    for linia in entrada:
        pid=linia.strip()
        try:
            command="kill "+pid
            print(command)
            os.system(command)
        except:
            print("Error stopping Watchdog.",sys.exc_info())
    command="rm MTUOCWatchdogPID.pid"
    print(command)
    os.system(command)
except:
    print("Error stopping Watchdog.",sys.exc_info())

