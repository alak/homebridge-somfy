#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pigpio


TXGPIO=4 # 433.42 MHz emitter on GPIO 4

#Button values
commandUp = 0x2
commandStop = 0x1
commandDown = 0x4
commandProg = 0x8

textCommands = {commandUp: "Up", commandStop: "Stop", commandDown: "Down", commandProg: "Prog"}

frame = bytearray(7)

def send_command(telco, bouton): #Sending a frame
   checksum = 0
   
   with open(os.path.dirname(os.path.abspath(__file__)) + "/remotes/" + telco, 'r') as file:# the files are un a subfolder "somfy"
      data = file.readlines()

   teleco = int(data[0], 16)
   code = int(data[1])
   data[1] = str(code + 1)

   with open(os.path.dirname(os.path.abspath(__file__)) + "/remotes/" + telco, 'w') as file:
      file.writelines(data)

   print "GPIO          : " + str(TXGPIO)
   print "Remote        : " + "0x%0.2X" % teleco
   print "Button        : " + textCommands[bouton] + " with command " + "0x%0.2X" % bouton
   print "Rolling code  : " + str(code)
   print ""

   pi = pigpio.pi() # connect to Pi

   if not pi.connected:
      exit()

   pi.wave_add_new()
   pi.set_mode(TXGPIO, pigpio.OUTPUT)

   frame[0] = 0xA7;       # Encryption key. Doesn't matter much
   frame[1] = bouton << 4 # Which button did  you press? The 4 LSB will be the checksum
   frame[2] = code >> 8               # Rolling code (big endian)
   frame[3] = (code & 0xFF)           # Rolling code
   frame[4] = teleco >> 16            # Remote address
   frame[5] = ((teleco >>  8) & 0xFF) # Remote address
   frame[6] = (teleco & 0xFF)         # Remote address

   print "Frame  :    ",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

   for i in range(0, 7):
      checksum = checksum ^ frame[i] ^ (frame[i] >> 4)

   checksum &= 0b1111; # We keep the last 4 bits only

   frame[1] |= checksum;

   print "With cks  : ",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

   for i in range(1, 7):
      frame[i] ^= frame[i-1];

   print "Obfuscated :",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

#This is where all the awesomeness is happening. You're telling the daemon what you wana send
   wf=[]
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 9415))
   wf.append(pigpio.pulse(0, 1<<TXGPIO, 89565))
   for i in range(2):
      wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
      wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550))
   wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

   for i in range (0, 56):
      if ((frame[i/8] >> (7 - (i%8))) & 1):
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
      else:
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

   wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415))

   #2
   for i in range(7):
      wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
      wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550))
   wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

   for i in range (0, 56):
      if ((frame[i/8] >> (7 - (i%8))) & 1):
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
      else:
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

   wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415))

   #2
   for i in range(7):
      wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
      wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550))
   wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

   for i in range (0, 56):
      if ((frame[i/8] >> (7 - (i%8))) & 1):
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
      else:
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

   wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415))

   pi.wave_add_generic(wf)
   wid = pi.wave_create()
   pi.wave_send_once(wid)
   while pi.wave_tx_busy():
      pass
   pi.wave_delete(wid)

   pi.stop()
   
   
if __name__ == "__main__":
      remote = sys.argv[1]
      command = int(sys.argv[2])
      commands = [commandUp, commandStop, commandDown, commandProg]
      send_command(remote, commands[command])