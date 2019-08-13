# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 16:52:47 2019

@author: edward qu
autogyro@qq.com

"""

import sys
import datetime as dt
import numpy as np
import cv2
import serial
import serial.tools.list_ports
import threading
import time


class ReThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop_thermal=False           
        self.Tmax = 45
        self.Tmin = 15

    
    def run(self):
        self.ser = serial.Serial ('com13')
        self.ser.baudrate = 460800        
        self.ser.write(serial.to_bytes([0xA5, 0x25, 0x01, 0xCB]))  # set frequency of module to 4 Hz
        time.sleep(2)#wait for data loading
        self.ser.write(serial.to_bytes([0xA5,0x35,0x02,0xDC]))
        try:
            while True:
                if (self.stop_thermal):
                    print ('Thermal camera Stopped!')
                    break
                else:
                    data = self.ser.read(1544)
                    Ta, Tc, temp_array , f = self.getTempArray(data)
                    if f == True:
                        continue
                    ta_img = self.td2Image(temp_array)		
                    img = cv2.applyColorMap(ta_img, cv2.COLORMAP_JET)
                    img = cv2.resize(img, (640,480), interpolation = cv2.INTER_CUBIC)                    
                    img = cv2.flip(img, 1)
                    temp_min=temp_array.min()/100
                    temp_max=temp_array.max()/100
                    if temp_max>self.Tmax:
                        continue                        
                    text1 = 'Min:{:.1f} Max: {:.1f}'.format(temp_min, temp_max)
                    text2 = 'Center {:.1f} Envirment: {:.1f}'.format(Tc, Ta)
                    blur = cv2.GaussianBlur(img,(5,5),0)
                    median = cv2.medianBlur(blur,5)
                    x_s=int(median.shape[1]*0.15)
                    y_s=int(median.shape[0]*0.8)
                    y_s2=int(median.shape[0]*0.9)
                    cv2.putText(median, text1, (x_s, y_s), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 1)
                    cv2.putText(median, text2, (x_s, y_s2), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 1)
                    cv2.imshow('Thermal Camera', median)  
                    key = cv2.waitKey(1) & 0xFF      # if 's' is pressed - saving of picture                   
                    if key == ord("s"):
                        fname = 'pic_' + dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.jpg'
                        cv2.imwrite(fname, img)
                        print('Saving image ', fname)                            
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            self.ser.close()
            cv2.destroyAllWindows()
       
        except KeyboardInterrupt:
            self.ser.write(serial.to_bytes([0xA5,0x35,0x01,0xDB]))
            self.ser.close()
            cv2.destroyAllWindows()
    
    def getTempArray(self, ser_data):
        datum_error=False
        T_a = (int(ser_data[1540]) + int(ser_data[1541])*256)/100 
        T_c = (int(ser_data[1538]) + int(ser_data[1539])*256)/100   
        raw_data = ser_data[4:1540]# getting raw array of pixels temperature
        T_array = np.frombuffer(raw_data, dtype=np.int16)
        if 0<min(T_array)<4500: 
            pass
        else:
            datum_error=True    
        return T_a, T_c, T_array, datum_error

    def td2Image(self, f):
        norm = np.uint8((f/100 - self.Tmin)*255/(self.Tmax-self.Tmin))
        norm.shape = (24,32)
        return norm
            
    def stopThermal(self,parm):         
        self.stop_thermal=parm #boolean
        print ('shutdown this thread {}'.format(parm))

 
if  __name__=="__main__":
    testThread=ReThread()
    testThread.setDaemon(True)          
    testThread.start()             
    time.sleep(100)                   
    testThread.stopThermal(True)  
    time.sleep(2)  
    print("Is it alive ? {}".format(testThread.is_alive())) 