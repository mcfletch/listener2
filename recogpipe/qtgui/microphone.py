
class Microphone(QtMultimedia.QAudioRecorder):
    """Attempt to use qt multimedia to feed recogpipe
    
    mic = Microphone()
    # mic.choose_default()
    if mic.default_pipe():
        mic.record()
    
    """
    def default_format(self):
        self.setAudioCodec( 'audio/x-raw' )
        settings = QtMultimedia.QAudioEncoderSettings()
        settings.setChannelCount(1)
        settings.setSampleRate(16000)
        self.setEncodingSettings(settings)

    def default_pipe(self):
        path = '/run/user/%s/recogpipe/audio'%os.geteuid() 
        if os.path.exists(path):
            self.setOutputLocation(QtCore.QUrl.fromLocalFile(path))
            return True
        else:
            log.warning("RecogPipe is not currently listening")
