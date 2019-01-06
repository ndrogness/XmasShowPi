#!/usr/bin/env python3

import sys
import os
import alsaaudio as aa
import wave
from struct import unpack
import numpy as np

##################################################################
# Global Defines

# Maximum Signal intensity
MAX_SIGNAL_LEVEL = 8

# Default Frequencies & Weights for FFT analysis
DEFAULT_FREQUENCIES = [80, 150, 310, 450, 800, 2500, 5000, 10000]
DEFAULT_FREQ_WEIGHT = [2,    4,   8,   8,  16,   16,   32,    64]

# High Fidelity Info
SubBass = {'name': 'SubBass',
           'freq_low': 20,
           'freq_high': 60,
           'freq_sweetspot': 60,
           'step_size': 5,
           'weight': 1,
           'num_freqs_to_include': 0,
           'freqs': [60]
           }


Bass = {'name': 'Bass',
        'freq_low': 61,
        'freq_high': 250,
        'freq_sweetspot': 140,
        'step_size': 25,
        'weight': 2,
        'num_freqs_to_include': 1,
        'freqs': [80]
        }

LowMidrange = {'name': 'LowMidrange',
               'freq_low': 251,
               'freq_high': 500,
               'freq_sweetspot': 300,
               'step_size': 30,
               'weight': 4,
               'num_freqs_to_include': 1,
               'freqs': [300]
               }

Midrange = {'name': 'Midrange',
            'freq_low': 501,
            'freq_high': 2000,
            'freq_sweetspot': 1000,
            'step_size': 180,
            'weight': 8,
            'num_freqs_to_include': 2,
            'freqs': [500, 1000]
            #'freqs': [500]
            }

UpperMidrange = {'name': 'UpperMidrange',
                 'freq_low': 2001,
                 'freq_high': 4000,
                 'freq_sweetspot': 2500,
                 'step_size': 250,
                 'weight': 32,
                 'num_freqs_to_include': 0,
                 'freqs': [2500, 3500]
                 #'freqs': [2000]
                 }

Presence = {'name': 'Presence',
            'freq_low': 4001,
            'freq_high': 6000,
            'freq_sweetspot': 5000,
            'step_size': 250,
            'weight': 32,
            'num_freqs_to_include': 1,
            'freqs': [5000]
            }

Brilliance = {'name': 'Brilliance',
              'freq_low': 6001,
              'freq_high': 20000,
              'freq_sweetspot': 12000,
              'step_size': 1500,
              'weight': 64,
              'num_freqs_to_include': 1,
              'freqs': [12000]
              }

HiFi_ascending = [SubBass, Bass, LowMidrange, Midrange, UpperMidrange, Presence, Brilliance]


##################################################################
class AudioFile:

    def __init__(self, afile, type='WAV', achunk=4096):

        if not os.path.exists(afile):
            print("Audio File: ", afile, "not found!")
            # return()

        self.filename = afile
        self.chunk_size = achunk
        self.chunk_levels = [0, 0, 0, 0, 0, 0, 0, 0]
        self.IsPlaying = False

        # Open the wave file
        self.wave_file = wave.open(afile, 'rb')
        self.nchannels = self.wave_file.getnchannels()
        self.frame_rate = self.wave_file.getframerate()
        self.sample_width = self.wave_file.getsampwidth()
        self.nframes = self.wave_file.getnframes()

        # prepare audio for output
        self.audio_output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL)
        self.audio_output.setchannels(self.nchannels)
        self.audio_output.setrate(self.frame_rate)
        self.audio_output.setformat(aa.PCM_FORMAT_S16_LE)
        self.audio_output.setperiodsize(achunk)


    def read_chunk(self):
        _wdata = self.wave_file.readframes(self.chunk_size)
        return _wdata

    def read_analyze_chunk(self, frqs=DEFAULT_FREQUENCIES, wghts=DEFAULT_FREQ_WEIGHT):
        _wdata = self.wave_file.readframes(self.chunk_size)
        self.chunk_levels.clear()
        self.chunk_levels = calculate_levels(_wdata, self.chunk_size, self.frame_rate, frqs, wghts)
        return _wdata

    def write_chunk(self, adata):
        self.audio_output.write(adata)

    def stop(self):
        self.audio_output.close()
        self.wave_file.close()

# End AudioFile Class
##################################################################

##################################################################
class Signals:

    def __init__(self, stype="hifi", frequencies=DEFAULT_FREQUENCIES, weights=DEFAULT_FREQ_WEIGHT):

        self.weights = []
        self.frequencies = []
        self.fidelities = []

        if stype == "manual" and len(frequencies) > 0:
            self.frequencies = frequencies
            if len(weights) == len(frequencies):
                _need_weights = False
                self.weights = weights
            else:
                _need_weights = True

        else:
            self.frequencies = build_freqs_from_hifi()
            self.weights = build_weights_from_hifi()
            _need_weights = False

        self.num_freqs = len(self.frequencies)
        for i in range(0, self.num_freqs):
            self.fidelities.append(get_hifi_name_from_freq(self.frequencies[i]))
            if _need_weights:
                self.weights.append(get_hifi_name_from_freq(self.frequencies[i]))


# End Signals Class
##################################################################


#############################################################################################
def get_hifi_name_from_freq(frequency):

    # print("Freq:",frequency)
    for i in range(0, len(HiFi_ascending)):

        if frequency >= HiFi_ascending[i]['freq_low'] and frequency <= HiFi_ascending[i]['freq_high']:
            # print(" Found:",HiFi_ascending[i]['name'],HiFi_ascending[i]['freq_low'],HiFi_ascending[i]['freq_high'])
            return HiFi_ascending[i]['name']

    return "UNKNOWN"

# End get_hifi_name_from_freq
##################################################################


#############################################################################################
def get_hifi_weight_from_freq(frequency):

    for i in range(0, len(HiFi_ascending)):

        if frequency >= HiFi_ascending[i]['freq_low'] and frequency <= HiFi_ascending[i]['freq_high']:
            return int(HiFi_ascending[i]['weight'])

    return 0

# End get_hifi_name_from_freq
##################################################################


#############################################################################################
def build_freqs_from_hifi():

    hifi_frequencies = []
    for i in range(0, len(HiFi_ascending)):

        for j in range(0, HiFi_ascending[i]['num_freqs_to_include']):
            hifi_frequencies.append(HiFi_ascending[i]['freqs'][j])

    return hifi_frequencies

# End build_freqs_from_hifi
##################################################################

#############################################################################################
def build_weights_from_hifi():

    hifi_weights = []
    for i in range(0, len(HiFi_ascending)):

        for j in range(0, HiFi_ascending[i]['num_freqs_to_include']):
            hifi_weights.append(HiFi_ascending[i]['weight'])

    return hifi_weights

# End build_freqs_from_hifi
##################################################################


#############################################################################################
def freq_hifi_auto_build_from_file(filename, freqs, weights, ChunkSize=4096, MaxFreqs=8):

    DataFFT = []

    # possible_freqs
    HiFi_freqs = dict()
    HiFi_weights = dict()
    HiFi_counts = dict()

    for i in range(0, len(HiFi_ascending)):
        HiFi_freqs[HiFi_ascending[i]['name']] = build_freq_matrix(HiFi_ascending[i]['freq_low'],
                                                                  HiFi_ascending[i]['step_size'],
                                                                  HiFi_ascending[i]['freq_high'])

        HiFi_weights[HiFi_ascending[i]['name']] = [HiFi_ascending[i]['weight'] for x in range(0, len(HiFi_freqs[HiFi_ascending[i]['name']]))]

        HiFi_counts[HiFi_ascending[i]['name']] = [int(0) for x in range(0,len(HiFi_freqs[HiFi_ascending[i]['name']]))]

        # print(HiFi_freqs[HiFi_ascending[i]['name']])
        # print(HiFi_weights[HiFi_ascending[i]['name']])
  
    wavfile = wave.open(filename, 'r')
    sample_rate = wavfile.getframerate()

    data = wavfile.readframes(ChunkSize)
    print ("Calculating FFT on Wavfile...")

    while sys.getsizeof(data) > 16000:

        for HIFI in HiFi_freqs.keys():
            # print ("Processing Hifi:",HIFI,HiFi_freqs[HIFI],HiFi_weights[HIFI])
            DataFFT = calculate_levels(data, ChunkSize, sample_rate, HiFi_freqs[HIFI], HiFi_weights[HIFI])

            for j in range(0, len(DataFFT)):
                # possible_freqs_count[j] += DataFFT[j]
                HiFi_counts[HIFI][j] += DataFFT[j]

        data = wavfile.readframes(ChunkSize)

    wavfile.close()


    final_freq_counter = 0
    for j in range(0, len(HiFi_ascending)):
        name = HiFi_ascending[j]['name']
        num = HiFi_ascending[j]['num_freqs_to_include']
        HiFi_maxes = HiFi_counts[name]
        HiFi_maxes.sort(reverse=True)

        for k in range(0, num):
            candidate_count = HiFi_maxes[k]

            for l in range(0, len(HiFi_counts[name])):
                if HiFi_counts[name][l] == candidate_count:
                    print("Name", name, "Adding Frequency:", HiFi_freqs[name][l], "Count:", HiFi_counts[name][l])
                    freqs.append(HiFi_freqs[name][l])
                    weights.append(HiFi_weights[name][l])
                    final_freq_counter += 1

#### End freq_hifi_auto_build_from_file
##########################################################################

##########################################################################
def freq_auto_build_from_file(filename, freqs, weights, ChunkSize=4096, MaxFreqs=8):

    possible_freqs = build_freq_matrix(100, 100, 20000)
    print(possible_freqs)

    NumPossibleFreqs = len(possible_freqs)
    possible_freqs_count = [int(0) for i in range(0, NumPossibleFreqs)]

    # Counts=[int(0) for i in range(0,MaxFreqs)]

    possible_weights = [int(1) for i in range(0, NumPossibleFreqs)]
    DataFFT = []
    defaultweighting = [[0,1], [150,2], [625,8], [2500,16], [5000,32], [10000,64]]

    for i in range(0, NumPossibleFreqs):

        for j in range(0, len(defaultweighting)):
            if (defaultweighting[j][0] < possible_freqs[i]):
                possible_weights[i] = defaultweighting[j][1]

        if possible_weights[i] < 2:
            possible_weights[i]=2

    # print ("Freq:",possible_freqs[i],"Weight:",possible_weights[i])
      
    wavfile = wave.open(filename, 'r')
    sample_rate = wavfile.getframerate()

    data = wavfile.readframes(ChunkSize)

    print("Calculating FFT on Wavfile...")
    while sys.getsizeof(data) > 16000:
        # print("Processing FFT on Chunk")
        DataFFT = calculate_levels(data, ChunkSize, sample_rate, possible_freqs, possible_weights)

        for j in range(0, len(DataFFT)):
            possible_freqs_count[j] += DataFFT[j]

        data = wavfile.readframes(ChunkSize)

    wavfile.close()

    FreqCount = dict()
    for k in range(0, len(possible_freqs_count)):
        FreqCount[possible_freqs_count[k]] = k

    print(possible_freqs_count)
    print("Sorting List:")
    freqs_counts = possible_freqs_count
    freqs_counts.sort(reverse=True)
  
    print(freqs_counts)

    Counts = freqs_counts[0:MaxFreqs]
    print(Counts)

    for j in range(0, len(Counts)):
        freqs[j] = possible_freqs[ FreqCount[Counts[j]] ]
        print("Final Frequency:", freqs[j], "with count:", Counts[j])


  # print("Final Freqs:",freqs)

# End freq_auto_build_from_file
# ########################################################################

##########################################################################
def build_freq_matrix(start_freq=50, step_size=50, end_freq=20000):

    if start_freq < 20:
        start_freq = 20

    stop = int(round((end_freq-start_freq)/step_size))
    # print ("Stop:",stop)
    return [start_freq+(step_size*x) for x in range(0, stop)]

#### End build_freq_matrix
##########################################################################

##########################################################################
def calculate_levels(data, chunk, sample_rate, freqs, weighting):

    signal_levels = [int(0) for i in range(0, len(freqs))]

    power = []

    # Convert raw data (ASCII string) to numpy array
    data = unpack("%dh" % (len(data)/2), data)
    data = np.array(data, dtype='h')

    # Apply FFT - real data
    fourier = np.fft.rfft(data)

    # Remove last element in array to make it the same size as chunk
    fourier = np.delete(fourier, len(fourier)-1)

    # Find average 'amplitude' for specific frequency ranges in Hz
    power = np.abs(fourier)
 
    # Loop through freqs
    v1 = int(2*chunk*0/sample_rate)

    for i in range(0, len(freqs)):
        v2 = int(2*chunk*freqs[i]/sample_rate)
        # print (v1,v2)
        try:
            signal_levels[i] = int((np.mean(power[v1:v2:1]) * weighting[i]) / 1000000)

        except:
            signal_levels[i] = 0

        # Clip signal level at max
        if signal_levels[i] > MAX_SIGNAL_LEVEL:
            signal_levels[i] = MAX_SIGNAL_LEVEL

        v1 = v2

    return signal_levels

#### End calculate_levels
##########################################################################

##########################################################################
def print_levels(level_data):

    os.system("clear")
    for i in range(1, MAX_SIGNAL_LEVEL+1):
        row = (MAX_SIGNAL_LEVEL + 1) - i

        for j in range(0, len(level_data)):

            if row <= level_data[j]:
                sys.stdout.write(str('*'))

            else:
                sys.stdout.write(str(' '))

        print("")

    for i in range(0, len(level_data)):
        sys.stdout.write(str(i))

    print("")

#### End print_levels
##########################################################################

