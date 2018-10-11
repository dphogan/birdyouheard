#!/home/ubuntu/anaconda3/envs/tensorenv/bin/python

###!/opt/anaconda3/envs/tensorenv/bin/python
###!/home/ubuntu/anaconda3/envs/tensorenv/bin/python
###!/opt/anaconda3/bin/python3

"""
Given the path to a sound file, prints a JSON string of likely birds.
Note: Executes a user-supplied string.  Check for malicious code before calling.
"""

import sys
sys.path.append('/home/ubuntu/.local/lib/python3.6/site-packages')

import subprocess
import math
import numpy as np
import scipy as sp
import scipy.io.wavfile as wf
import scipy.signal as sg
import scipy.ndimage as sn
import skimage.measure as sm
#import tensorflow as tf
#import tensorflow.keras as keras
import tensorflow.keras.models as models
import pandas as pd
import json
import urllib
import urllib.parse

def makemono(waveform):
    if len(np.shape(waveform))>1:
        return np.mean(waveform,axis=1)
    else:
        return waveform

def highpass(mono, samplerate):
    b = sg.firwin(101, cutoff=1000, fs=samplerate, pass_zero=False)
    filtered = sg.lfilter(b, [1.0], mono)
    return filtered

#Identify when the individual sounds start
#  marginfactor is ratio between cutoff and RMS
#  windowwidthtime is window duration in seconds
#  windowpretime is how much time to save before peak
#  windowfraction and windowfraction2 are the fraction of windowwidthtime that is tolerable under certain circumstances
def chirpstarts(mono, samplerate, marginfactor=2, windowwidthtime=4, windowpretime=.5, windowfraction=0.5, windowfraction2=0.25):
    times = [x/samplerate for x in range(len(mono))]
    
    #Find and mark cutoff
    rms = np.sqrt(np.mean(mono**2))
    cutoff = rms*math.sqrt(2)*marginfactor + np.mean(mono)
        
    #Find and mark chirp starts
    windowstartindices = []
    windowendindices = []
    windowstartindex = 0
    windowendindex = 0
    windowpeakindex = 0
    windownextlookindex = 0
    numpoints = len(mono)
    while windownextlookindex < numpoints:
        windowpeakindex = windownextlookindex + np.argmax(mono[windownextlookindex:]>cutoff)
        windowstartindex = max(0,int(windowpeakindex - windowpretime*samplerate))
        windowendindex = int(windowstartindex + windowwidthtime*samplerate)
        windownextlookindex = int(windowstartindex + (windowwidthtime+windowpretime)*samplerate)
        if windowendindex>=numpoints:
            if (numpoints-windowstartindex)/samplerate<windowfraction*windowwidthtime:
                break
            else:
                windowendindex = numpoints-1
        windowstartindices.append(windowstartindex)
        windowendindices.append(windowendindex)
    if len(windowstartindices)==0 and numpoints/samplerate>windowfraction2*windowwidthtime: #Deals with a special case where no pulse is found   
        windowstartindices = [windowstartindex]
        windowendindices = [numpoints-1]
    windowstarttimes = []
    windowendtimes = []
    for windowstartindex in windowstartindices:
        windowstarttimes.append(times[windowstartindex])
    for windowendindex in windowendindices:
        windowendtimes.append(times[windowendindex])
        
    return windowstartindices, windowendindices, windowstarttimes, windowendtimes, cutoff

#Given a spectrogram and its axis labels (f, t, s), and a time window and acquisition rate
#(mintime, maxtime, samplerate), calculate a downsampled spectrogram in that window 
#to serve as a medium-sized two-dimensional representation of the sound.
def computefingerprint(f, t, s, mintime, maxtime, samplerate):
    #Time cut
    condition = np.logical_and(t>=mintime, t<=maxtime)
    s = s[:,condition]
    t = t[condition]

    #Frequency cut
    condition = np.logical_and(f<=10000, f>=1000)
    s = s[condition,:]
    f = f[condition]
    
    #Use the logarithm of power spectral density
    floorterm = 1
    logs = np.log(s+floorterm)
    
    #Downsample.  Warning: Hard-coded numbers!
    idealsamplerate = 44100
    ftarget = 18
    ttarget = 158
    fblock = 3
    tblock = 5
    windowwidth = 4
    if samplerate == idealsamplerate:
        #In most common case, use fast downsampling
        sdown = sm.block_reduce(logs,(fblock,tblock),func=np.mean)
        fdown = f[::fblock]
        tdown = t[::tblock]
    else:
        #In other cases, use alternate downsampling
        ideallenf = ftarget
        ideallent = ttarget * (maxtime-mintime)/windowwidth
        sdown = sn.zoom(logs, (ideallenf/len(f), ideallent/len(t)))
        fdown = np.linspace(f[0],f[-1],ideallenf)
        tdown = np.linspace(t[0],t[-1],ideallent)
        samplerate = idealsamplerate

    #Cut or pad fingerprint, to ensure it's the exact right size
    sdown = sdown[:ftarget,:ttarget]
    fdown = fdown[:ftarget]
    tdown = tdown[:ttarget]
    sdown = np.pad(sdown, ((0,ftarget-np.shape(sdown)[0]),(0,ttarget-np.shape(sdown)[1])), 'constant', constant_values=0)
    fdown = np.linspace(f[0],f[-1],ftarget)
    tdown = np.linspace(t[0],t[0]+windowwidth,ttarget)
    #fdown = np.pad(fdown, (0,ftarget-np.shape(fdown)[0]), 'constant', constant_values=0)
    #tdown = np.pad(tdown, (0,ttarget-np.shape(tdown)[0]), 'constant', constant_values=0)
        
    #Plots (mostly for debugging)
    if False:
        plt.pcolor(t, f, logs)
        plt.colorbar()
        plt.show()
        plt.pcolor(tdown, fdown, sdown)
        plt.colorbar()
        plt.show()
        
    return sdown



def main(filepathinput, urlpathinput=''):

    #Load file from URL, if necessary
    if len(urlpathinput)>0:
        suffix = filepathinput[-4:]
        if not suffix in ['.mp3', '.wav']:
            #If the PHP didn't find out the file suffix, just assume mp3
            filepathinput += '.mp3'
        urlpathinput = urllib.parse.quote(urlpathinput,'/:?=&')
        urllib.request.urlretrieve(urlpathinput, filepathinput)
    
    #Convert file, if necessary
    mp3support = True
    if mp3support and filepathinput[-4:].lower()=='.mp3':
        filepath = filepathinput[:-4] + '.wav'
        commandstring = 'ffmpeg -y -i ' + filepathinput + ' ' + filepath + ' 2>/dev/null'
        subprocess.check_output(commandstring, shell=True)
    elif filepathinput[-4:].lower()=='.wav':
        filepath = filepathinput
    else:
        print('! Supported file formats are wav and mp3.')
        filepath = filepathinput

    #Read in file
    wavdata = wf.read(filepath)
    mono = makemono(wavdata[1])
    samplerate = wavdata[0]

    #Compute spectrogram, and also identify pulses in filtered waveform
    f, t, s = sp.signal.spectrogram(mono,fs=samplerate)
    filtered = highpass(mono, samplerate)
    startindices, endindices, starttimes, endtimes, cutoff = chirpstarts(filtered, samplerate)
        
    #Loop through the chirps, getting a downsampled spectrogram for each
    for chirpnum in range(len(startindices)):
        fingerprint = computefingerprint(f, t, s, starttimes[chirpnum], endtimes[chirpnum], samplerate)
        fingerprint = fingerprint.reshape(1, fingerprint.shape[0], fingerprint.shape[1], 1)

        if chirpnum==0:
            fingerprints = fingerprint
        else:
            fingerprints = np.concatenate((fingerprints, fingerprint))

    #Make prediction based on the Keras model saved as files
    modeljson = json.load(open('model.json', 'r'))
    model = models.model_from_json(modeljson)
    model.load_weights('model.hdf5')
    chirppredictions = model.predict(fingerprints)

    #Average the predictions for one overall prediction for the recording
    prediction = np.mean(chirppredictions, axis=0)

    #Convert prediction to 'molabel' of specific birds
    molabels = pd.read_csv('labels.csv', index_col=0)
    molabelarray = (molabels['molabel']).values
    order = (-prediction).argsort()
    sortedprediction = prediction[order]
    sortedmolabels = molabelarray[order]

    #Look up information about the birds
    df = pd.read_csv('common_birds.csv')
    birdlist = []
    for i in range(10):
        match = df['molabel']==sortedmolabels[i]
        birdline = df.loc[df['molabel']==sortedmolabels[i]]
        birddict = {
            'common name': (birdline['common name'].values)[0],
            'scientific name': (birdline['scientific name'].values)[0],
            'genus': (birdline['genus'].values)[0],
            'species': (birdline['species'].values)[0],
            'probability':float(sortedprediction[i])
        }
        birdlist.append(birddict)
    birdjson = json.dumps(birdlist)
    print(birdjson)
    
if __name__ == '__main__':
    if len(sys.argv)>2:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv)>1:
        main(sys.argv[1])
    else:
        print('! Syntax choices are:')
        print('  ./predict.py path/to/file.wav')
        print('  ./predict.py path/to/file http://example.com/file.wav')
