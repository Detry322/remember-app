import scipy, numpy, wave, struct, pydub
import matplotlib.pyplot as plt
from scipy import signal
import scipy.io.wavfile
from pydub import AudioSegment
#from pydub.utils import mediainfo
import math
from scipy.signal import butter, filtfilt

def butter_lowpass(cutoff, fs, order = 5):
    nyq = fs/2
    normal_cutoff=cutoff/nyq
    b,a = butter(order,normal_cutoff, btype='low',analog = False)
    return b,a

def butter_lowpass_filtfilt(data, cutoff,fs,order=5):
    b,a = butter_lowpass(cutoff, fs, order = order)
    y = filtfilt(b,a,data)
    return y

def hwindow(audio, audioSize):
    print 'window'

    for j in range(audioSize):
       if audio[j] < 0:
             audio[j] = -audio[j]
    print 'filtering'
    filtered = abs(signal.hilbert(audio))
    output = filtered
    output2 = []

    for j in range(len(output)):
        if j%180 == 0:
             output2.append(output[j])
    winLength =  51
    output2 = numpy.convolve(output2, numpy.ones((winLength,))/winLength)[winLength-1:]
    output3 = []
    for i in output2: output3.append(i)
    
    pad = [0]
    return pad+output3


def diffrect( audio ):
    print 'diffrect'

    n = len(audio)
    output = []

    for j in range(1,n):
        if audio[j] > 0 and audio[j-1] > 0:
            d = numpy.log10(audio[j]) - numpy.log10(audio[j-1])
        else: d = 0
        if d > 0:
            output.append(d)
        else :
            output.append(0)

    for j in range(len(output) - 30):
        for k in range(31):
            if output[j] < output[j+k]:
                 output[j] = 0
            elif output[j]> output[j+k]:
                output[j+k] = 0

        if output[j] < max(output)/5: output[j] = 0
            
    return output


def main(audioFile):
    sound = AudioSegment.from_file(audioFile)
    sample_rate = 44100
    sound2 = sound.split_to_mono()
    sound2 = sound2[0]
    audio = sound2.get_array_of_samples()
    audio = audio.tolist()
    length = int(round(len(audio)))
    audioShort = audio[0:int(math.floor(length))]
    lengthShort = len(audioShort)
    differed = []
    windowed = []
    div = 6
    a = []
    b = []

    timeDict = {}

    for i in range(div):
        beg = int(math.floor(i*lengthShort/div))
        last1 = int(math.floor((i+1)*lengthShort/div))
        print 'beg' , beg
        print 'last ', last1
        a = hwindow(audioShort[beg:last1],last1-beg)
        b = diffrect(a)
        windowed = windowed + a
        differed = differed + b

    for i in range(len(differed)):
        if differed[i] > 0:
            time = i/(sample_rate/180)
            timeDict[time] = differed[i]
    return timeDict

    
            


