import os
import librosa
import soundfile as sf

STARTING_NOTE = "C4"

NOTE_DIR = "processing/piano"

DESIRED_NOTES = [
    "C3",
    "C#3",
    "D3",
    "D#3",
    "E3",
    "F3",
    "F#3",
    "G3",
    "G#3",
    "A3",
    "A#3",
    "B3",
    "C4",
    "C#4",
    "D4",
    "D#4",
    "E4",
    "F4",
    "F#4",
    "G4",
    "G#4",
    "A4",
    "A#4",
    "B4",
    "C5",
    "C#5",
    "D5",
    "D#5",
    "E5",
    "F5",
    "F#5",
    "G5",
    "G#5",
    "A5",
    "A#5",
    "B5",
    "C6",
]

SOURCE_FILE = os.path.join(NOTE_DIR, f"{STARTING_NOTE}.wav")

if not os.path.exists(SOURCE_FILE):
    raise FileNotFoundError(f"Missing source file: {SOURCE_FILE}")

# Load source note
audio, sr = librosa.load(SOURCE_FILE, sr=None, mono=False)

# Keep only the first second
max_samples = sr

if audio.ndim == 1:
    audio = audio[:max_samples]
else:
    audio = audio[:, :max_samples]

for note in DESIRED_NOTES:
    semitones = librosa.note_to_midi(note) - librosa.note_to_midi(STARTING_NOTE)

    print(f"Generating {note} ({semitones:+d} semitones)")

    shifted = librosa.effects.pitch_shift(
        audio,
        sr=sr,
        n_steps=semitones,
    )

    output_file = os.path.join(NOTE_DIR, f"{note.replace("#", "s")}.ogg")
    sf.write(
        output_file,
        shifted.T if shifted.ndim > 1 else shifted,
        sr,
        format="OGG",
        subtype="VORBIS",
    )

print("Done.")