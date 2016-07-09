import scipy, numpy, wave, struct, pydub
import scipy.io.wavfile
from pydub import AudioSegment
import math

def filterbanks( audio ):
    audioSquared = [a*b for a,b in zip(audio,audio)]
    bandlimits = [32, 64, 128, 256, 512, 1024, 2048, 5096, 10192]
    maxfreq = 12000
    n = len(audio)
    xRMS = 20*math.log10(sum(audioSquared)/(n*.00002))
    A = 10**((70-xRMS)/20)
    audio[:] = [x*A for x in audio] #normalize audio

    dft = numpy.fft.fft(audio)
    nf = len(dft)

    nbands = len(bandlimits)
    bl = []
    br = []
    
    for i in range(nbands-1):
        bl.append(math.floor(bandlimits[i]*nf/maxfreq/2)+1)
        br.append(math.floor(bandlimits[i+1]*nf/maxfreq/2))

    bl.append(math.floor(bandlimits[nbands-1]/maxfreq*n/2)+1)
    br.append(math.floor(n/2))

    output = [[0]*nf for i in range(nbands)] 

    for i in range(nbands):
        output[i] = numpy.concatenate((dft[bl[i]:br[i]],dft[n+1-br[i]:n+1-bl[i]]))
    print len(output[1])
    return output

def hwindow(audio):
    n = len(audio[0])
    frequencyBands = [32, 64, 128, 256, 512, 1024, 2048, 5096, 10192]
    nbands = len(frequencyBands)
    maxFreq = 12000
    hannLen = 2*.05*maxFreq
    hann = []
    for a in range(int(math.floor(hannLen))):
        hann.append((math.cos(a*math.pi/hannLen/2))**2)

    wave = [[0]*n for i in range(nbands)] 

    for i in range(nbands):
        wave[i] = numpy.fft.ifft(audio[i])
        wave[i] = wave[i].real
        print len(wave[i])

    wave2 = [[] for i in range(nbands)]
    count = 1
    freq =[[] for i in range(nbands)]
    output = [[] for i in range(nbands)]

    for i in range(nbands):
        for j in range(n):
            if wave[i][j] < 0:
                wave[i][j] = -wave[i][j]
        filtered[i] = numpy.convolve(wave,hann)

        output[i] = numpy.fft.ifft(filtered[i])
        output[i] = output[i].real
    print len(output[1])
    for i in range(nbands):
        for j in range(len(output[i])):
            if j%180 == 0:
                wave2[i].append(output[i][j])
    return wave2

def differect( audio ):
    frequencyBands = [32, 64, 128, 256, 512, 1024, 2048, 5096, 10192]
    nbands = len(frequencyBands)

sound = AudioSegment.from_file('2baE-draft-002.wav')
sound2 = sound.split_to_mono()
sound2 = sound2[0]
audio = sound2.get_array_of_samples()
length = int(round(len(audio)/20))
audio = audio[0:length]
audio = audio.tolist()


filtered = filterbanks(audio)
windowed = hwindow(filtered)
print len(filtered)
print windowed
