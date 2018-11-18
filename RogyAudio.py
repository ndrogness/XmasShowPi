#!/usr/bin/env python3

import sys
import os
import time
import pyaudio
import random
import alsaaudio as aa
import wave


##############################################
class RogyAudioFile:

    def __init__(self, afile, type='WAV', achunk=4096):

        if not os.path.exists(afile):
            print("Audio File: ", afile, "not found!")
            return()

        self.filename = afile
        self.chunk_size = achunk
        self.IsPlaying = False

        _wf = wave.open(afile, 'rb')
        _p = pyaudio.PyAudio()

        self.wave_file = _wf
        self._pa_object = _p
        self.sample_width = _wf.getsampwidth()
        self.format = _p.get_format_from_width(self.sample_width)
        self.nchannels = _wf.getnchannels()
        self.frame_rate = _wf.getframerate()

        self._astream = _p.open(format=self.format,
                           channels=self.nchannels,
                           rate=self.frame_rate,
                           output=True)


    def read_chunk(self):
        _wdata = self.wave_file.readframes(self.chunk_size)
        return (_wdata)

    def write_chunk(self, adata):
        self._astream.write(adata)

    def stop(self):
        self._astream.stop_stream()
        self._astream.close()
        self._pa_object.terminate()

##############################################

#HiFi [StartFreq,EndFreq,SweetSpot,Weight]
SubBass={'name':'SubBass','freq_low':20,'freq_high':60,'freq_sweetspot':60,'step_size':5,'weight':1,'num_freqs_to_include':0}

Bass={'name':'Bass','freq_low':61,'freq_high':250,'freq_sweetspot':140,'step_size': 25,'weight':2,'num_freqs_to_include':1}

LowMidrange={'name':'LowMidrange','freq_low':251,'freq_high':500,'freq_sweetspot':300,'step_size':30,'weight':4,'num_freqs_to_include':1}

Midrange={'name':'Midrange','freq_low':501,'freq_high':2000,'freq_sweetspot':1000,'step_size':180,'weight':8,'num_freqs_to_include':2}

UpperMidrange={'name':'UpperMidrange','freq_low':2001,'freq_high':4000,'freq_sweetspot':2500,'step_size':250,'weight':16,'num_freqs_to_include':2}

Presence={'name':'Presence','freq_low':4001,'freq_high':6000,'freq_sweetspot':5000,'step_size':250,'weight':32,'num_freqs_to_include':1}

Brilliance={'name':'Brilliance','freq_low':6001,'freq_high':20000,'freq_sweetspot':12000,'step_size':1500,'weight':64,'num_freqs_to_include':1}

HiFi_ascending=[SubBass,Bass,LowMidrange,Midrange,UpperMidrange,Presence,Brilliance]

