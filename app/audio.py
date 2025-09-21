import io
import pyaudio
import numpy as np
import wave

class Audio():
    def __init__(self, bus=None, rate=16000, buffer_size=1024):
        ''' Audio (PCM) device '''
        self.audio = pyaudio.PyAudio()
        self.bus = bus
        self.rate = rate
        self.buffer_size = buffer_size
        self.in_stream = self.audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        input=True,
                        frames_per_buffer=buffer_size)
        self.out_stream = self.audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        output=True)

    async def update(self):
        ''' Audio buffer task '''
        if not self.bus:
            return

        while self.in_stream.is_active():
            data = self.in_stream.read(self.buffer_size)
            await self.bus.emit("audio_input", data)

    def tone(self, duration: float):
        ''' 
            Play a 440 Hz tone during X seconds 
            (used for testing the audio output)
        '''
        # Audio parameters
        frequency = 440.0    # Hz (A4 note)

        # Generate sine wave
        t = np.linspace(0, duration, int(self.rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t)

        # Convert to 16-bit PCM format
        audio *= 32767 / np.max(np.abs(audio))
        audio = audio.astype(np.int16)

        # Play the tone
        self.out_stream.write(audio.tobytes())

    def record(self, duration: float):
        ''' 
            Record a audio sample in WAV format
            (used for testing the audio input)
        '''
        # Record frame by 1024 bytes
        frames = []
        for _ in range(0, int(self.rate / 1024 * duration)):
            data = self.in_stream.read(1024)
            frames.append(data)

        # Create a WAV file in memory from the RAW PCM Data
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b''.join(frames))

        return wav_buffer.getvalue()

    def close(self):
        ''' Close all audio channel '''
        self.in_stream.stop_stream()
        self.out_stream.stop_stream()
        self.in_stream.close()
        self.out_stream.close()
