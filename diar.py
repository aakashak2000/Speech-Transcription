from pyAudioAnalysis.audioSegmentation import mid_term_file_classification, evaluate_speaker_diarization, speaker_diarization,hmm_segmentation
from pydub import AudioSegment    
from scipy.io import wavfile
import os
import time
from IPython.display import clear_output, Audio
import speech_recognition as sr
import matplotlib.pyplot as plt
import pandas as pd
import wave
import contextlib

def get_duration(fname):
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        return (duration)
    
    
        
def speed_change(sound, speed=1.0):
    
    '''
    Function to override the frame_rate. This tells the computer how many samples to play per second. Basically, slows down the input audio file by the given hyperparameter.
    
    Parameters:
    ---------------
    sound: pydub.Audiosegment file that needs change in speed.
    speed: change in speed. Default:1.0
    
    Returns:
    ---------------
    Speed-altered audiosegment
    '''
    
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })

    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    
    
    
def non_speech_removal(a):
    
    """
    Function to remove non-speech segments like music, silence, etc. from audio.
    
    Parameters:
    -----------------
    a: Input audio file path
    
    Returns:
    -----------------
    Audiosegment with only speech.
    """
    
    
    #Uses a knn model to identify is there is speech or a music/silence in the audio file at every second.
    #Extracts timestamps for those segments where there is music/silence.
    #Using that extracts segments where there is only speech.
    #Joins all speech segments together to form a new audio file ith only speech
    #Return the new audio.
    
    #pyAudioAnalysis/data/models/
    [flagsInd, classesAll, acc, CM] = mid_term_file_classification(a, "knn_sm", "knn", plot_results=True)


    sound = AudioSegment.from_file(a)
    multiplier = (len(sound)/len(flagsInd))


    t = []
    for sec, flag in enumerate(flagsInd):
        if flag == 1:
            t.append(sec)


    start=0
    end=0
    ts=[]
    for i, val in enumerate(t):
        if t[i]-t[i-1]>5:
            end=t[i-1]
            if start!=end:
                ts.append([start*multiplier, end*multiplier])
            start=t[i]
            end=t[i]   

            
    ns = sound
    for t in ts:
        s1=ns[:t[0]]
        s2=ns[t[0]:t[1]]
        s3=ns[t[1]:]
        ns=s1+s3
        
    return ns






    



def getScript(audio, language = 'english', mid_step = 0.2, mid_window = 5):
    
#     mid_step = 0.2
    thresh = 20

    mag=0.87
    if language == 'english':
        mag = 0.85
    else:
        mag = 0.3
        
    
        
    
    
        
    
#     print('---------non speech removal--------')
#     print('cropping audio')
    destination = "cropped/converted.wav"
#     print('removing silence and music')
    sound = non_speech_removal(audio)
    sound.export(destination, format="wav")
    if len(sound)>100000:
        mid_window=5
        mid_step = 0.3
        if language=='hindi':
            mid_step=0.4
            mid_window = 10
    else:
        mid_window = 2
        if language=='hindi':
            mid_step=0.2
            mid_window = 5
#     print('diarizing')
    op = speaker_diarization(destination, 2, mid_step=mid_step, lda_dim=0, mid_window = mid_window)
    
    
    
    
    
#     print('--------Extracting timestamps--------')
    sound = AudioSegment.from_wav(destination)
    

    
    label_e = 0
    label_c = int(not(label_e))
    op = op.astype('int')
    multiplier = (len(sound)/len(op))
    labels = [0,1]
    
    
    destinations = []
    for label in labels:
#         print(f'for speaker{label}')
        t=[]
        if op[0]==label:
            t.append(0)
            
        timestamp = []
        for i in range(1, len(op)):
            if op[i] != op[i-1]:
                if op[i]!=label:
                    t.append((i+4)*multiplier)
                    timestamp.append(t)
                    t=[]
                elif op[i]==label:
                    t.append((i)*multiplier)
                    
        newAudio = sound[0:0]        
        for i in range(len(timestamp)):
            t = timestamp[i]
            newAudio += sound[t[0]:t[1]]  
        destination = f"cropped/sp{label}.wav"
        destinations.append(destination)
        newAudio.export(destination, format='wav')
        
        
        
    
        
#     print('--------Generating Scripts--------\n')
    scripts = []
    for destination in destinations:
        'starting.....'
        newAudio = AudioSegment.from_file(destination)
#         print(len(newAudio))
        d = get_duration(destination)
        
        
        print(d)
    
        if d>thresh:
            m = int(d/thresh)
        else:
            m=0
        
        print(m)
        myscript=''
        
        mul = len(newAudio)/d 
        for i in range(m+1):
#             print(f'cropping segment{i}')
            start=mul*(i*thresh)
            if i==m:
                end = len(newAudio)
            else:
                end=mul*((i+1)*thresh)
#             print(start,end)
            crop_file = newAudio[start:end] #crops out audio segment from input audio
            slow_sound = speed_change(crop_file, mag)
            slow_sound.export('cropped/ss.wav', 'wav')
#             print(f'recognizing segment{i}\n')
            r = sr.Recognizer()
            with sr.AudioFile('cropped/ss.wav') as source:
                r.adjust_for_ambient_noise(source)
                audio = r.record(source)
            try:
                speech = r.recognize_google(audio, language='en-IN')
#                 print(speech)
#                 print('-------')
                myscript +=speech+' '
    #             print(speech)
            except sr.UnknownValueError:
                print('')
            except sr.RequestError as e:
                print("Recognizer error; {0}".format(e), '\n')
            if os.path.exists('cropped/ss.wav'):
                os.remove('cropped/ss.wav') 
        if os.path.exists(destination):
            os.remove(destination)      
#         print('\ngenerated a script\n')
                  
        scripts.append(myscript)

    
    if os.path.exists('cropped/converted.wav'):
        os.remove('cropped/converted.wav')    
#     print('all scripts ready')
    return scripts