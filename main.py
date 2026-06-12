import asyncio

from jinja2 import Template
from pyscript import document, when, fs, window
import js # type: ignore
import json
from pyodide.ffi import create_proxy # type: ignore

# --------------------
# Helper functions and globals
# --------------------

def render_template(file: str, dest_id: str, **kwargs):
    """
    Renders a Jinja template and paints it to the DOM.

    :param file: The path to the Jinja template file.
    :type file: str
    :param dest_id: The ID of the DOM element where the rendered template will be inserted.
    :type dest_id: str
    :param kwargs: The variables to pass to the Jinja template.
    """

    # load raw HTML layout
    with open(file, "r") as file:
        layout = file.read()
    
    # compile and add variables with Jinja
    template = Template(layout)
    output = template.render(**kwargs)
    
    # add to document
    document.getElementById(dest_id).innerHTML = output

tempo = 120
num_beats = 4 # * 4 for 16th notes
notes = {} # dict of instrument name to (dict of note name to list of bool of whether the note is on for each beat)
note_objects = {} # dict of instrument name to (dict of note name to Note object)
can_edit = True
play_interval_id = None
divisions_per_beat = 4

with open("samples/instruments.json", "r") as file:
    all_instruments = json.load(file)
instrument_dict = {instrument["name"]: instrument for instrument in all_instruments}

# --------------------
# Navbar
# --------------------

def init_navbar():
    instrument_list = [instrument["name"] for instrument in all_instruments]
    render_template("templates/navbar-instrument-list.html", "navbar-instrument-list", instruments=instrument_list)

# the callbacks
@when("click", "#navbar-instrument-list")
async def instrument_cb(event):
    if not can_edit: return

    if event.target.id.startswith("navbar-instrument-"):
        try:
            instrument_id = event.target.id.replace("navbar-instrument-", "")
            if instrument_id not in notes:
                notes[instrument_id] = {note: [False] * (num_beats * divisions_per_beat) for note in instrument_dict[instrument_id]["notes"]}
                load_notes(instrument_id)
                render()
        except Exception: pass

@when("click", "#navbar-set-beats")
def settings_beats_cb(event):
    event.preventDefault()
    if not can_edit: return
    
    try:
        global num_beats
        new_num_beats = int(document.getElementById("navbar-beats").value)
        assert 1 <= new_num_beats
        num_beats = new_num_beats
    except ValueError:
        js.alert("Please enter a valid number for the number of beats.")
    except AssertionError:
        js.alert("Please enter a number of beats between 1 and 16.")
    render()

@when("click", "#navbar-set-divisions")
def settings_divisions_cb(event):
    event.preventDefault()
    if not can_edit: return
    
    try:
        global divisions_per_beat
        new_divisions = int(document.getElementById("navbar-divisions").value)
        assert 1 <= new_divisions <= 8
        divisions_per_beat = new_divisions
    except ValueError:
        js.alert("Please enter a valid number for the divisions per beat.")
    except AssertionError:
        js.alert("Please enter a number of divisions per beat between 1 and 8.")
    render()

@when("click", "#navbar-set-tempo")
def settings_tempo_cb(event):
    event.preventDefault()
    if not can_edit: return

    try:
        global tempo
        new_tempo = float(document.getElementById("navbar-tempo").value)
        assert 20 <= new_tempo <= 300
        tempo = new_tempo
    except ValueError:
        js.alert("Please enter a valid number for the tempo.")
    except AssertionError:
        js.alert("Please enter a tempo between 20 and 300 BPM.")

@when("click", "#navbar-play")
def play_cb(event):
    event.preventDefault()
    global can_edit
    can_edit = not can_edit
    if not can_edit:
        document.getElementById("navbar-play").innerHTML="&nbsp;&nbsp;&nbsp;Stop&nbsp;&nbsp;&nbsp;"
        play()
    else:
        document.getElementById("navbar-play").innerHTML="&#9654;&nbsp;&nbsp;Play&nbsp;&nbsp;"
        stop()

# --------------------
# Main section
# --------------------
def register_volume_callbacks():
    for instrument_name in note_objects:
        @when("input", f"#volume-{instrument_name}")
        def volume_cb(event, instrument_name=instrument_name):
            event.preventDefault()
            try:
                new_volume = float(event.target.value)
                assert 0 <= new_volume <= 100
                for note_obj in note_objects[instrument_name].values():
                    for audio in note_obj.audio_pool:
                        audio.volume = new_volume / 100
            except ValueError:
                js.alert("Please enter a valid number for the volume.")
            except AssertionError:
                js.alert("Please enter a volume between 0 and 100.")


def render():
    global num_beats, divisions_per_beat
    render_template("templates/main-area.html", "main-area", instruments=[instrument_dict[i] for i in notes], num_beats=num_beats, current_notes=notes, divisions_per_beat=divisions_per_beat)
    register_note_callbacks()
    ensure_notes_length()

    # ensure the callbacks are registered; debugged with Copilot
    for name in notes:
        document.getElementById(f"clear-{name}").addEventListener("click", create_proxy(clear_instrument_cb))
        document.getElementById(f"delete-{name}").addEventListener("click", create_proxy(delete_instrument_cb))

    register_volume_callbacks()
    
    # ensure the ruler is updated as well
    render_ruler()

def ensure_notes_length():
    for instrument_name, instrument_notes in notes.items():
        for note_name, beats in instrument_notes.items():
            if len(beats) < num_beats * divisions_per_beat:
                beats.extend([False] * (num_beats * divisions_per_beat - len(beats)))
            elif len(beats) > num_beats * divisions_per_beat:
                notes[instrument_name][note_name] = beats[:num_beats * divisions_per_beat]

def register_note_callbacks():
    for instrument_name, instrument_notes in notes.items():
        for note_name, beats in instrument_notes.items():
            for beat in range(num_beats * divisions_per_beat):
                @when("click", f"#{instrument_name}-beat-{beat}-note-{note_name}")
                # debugged with Copilot
                def note_cb(event, instrument_name=instrument_name, note_name=note_name, beat=beat, beats=beats):
                    if not can_edit: return

                    # play the note
                    note_objects[instrument_name][note_name].play()

                    beats[beat] = not beats[beat]
                    event.target.classList.toggle("active")

# Debugged with Copilot
def play():
    ms_per_beat = 60000 / (tempo * divisions_per_beat)
    beat = 0

    def play_beat():
        nonlocal beat
        prev_beat = (beat - 1) % (num_beats * divisions_per_beat)

        # iterate over each note of each instrument
        for instrument_name, instrument_notes in notes.items():
            for note_name, beats in instrument_notes.items():
                # play the note if it's active for the current beat
                if beats[beat]:
                    note_objects[instrument_name][note_name].play()
                
                # add the "playing" class to the current beat
                document.getElementById(f"{instrument_name}-beat-{beat}-note-{note_name}").classList.add("playing")

                # remove the "playing" class from the previous beat
                document.getElementById(f"{instrument_name}-beat-{prev_beat}-note-{note_name}").classList.remove("playing")

        # advance beat once after all instruments/notes are processed
        beat = (beat + 1) % (num_beats * divisions_per_beat)

        
    # schedule the beat playback
    global play_interval_id
    play_interval_id = js.setInterval(create_proxy(play_beat), ms_per_beat)

def stop():
    global play_interval_id
    js.clearInterval(play_interval_id)

    # remove "playing" class from all notes    
    for instrument_name, instrument_notes in notes.items():
        for note_name, beats in instrument_notes.items():
            for beat in range(num_beats * divisions_per_beat):
                document.getElementById(f"{instrument_name}-beat-{beat}-note-{note_name}").classList.remove("playing")

def load_notes(instrument_name):
    note_objects[instrument_name] = {}
    for note in notes[instrument_name]:
        note_objects[instrument_name][note] = Note(f"samples/{instrument_name}/{note}.ogg", instrument_dict[instrument_name].get("hold", None))

class Note:
    def __init__(self, path, hold_duration):
        self.path = path
        self.hold = hold_duration

        # audio pool so a note can finish playing even if it's triggered again; debugged with Copilot
        self.audio_pool = [js.Audio.new(path) for _ in range(5)]
        self.current_index = 0

    def play(self):
        # Use the next audio element in the pool (round-robin)
        audio = self.audio_pool[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.audio_pool)
        
        try:
            audio.pause()
        except: 
            print("error pausing audio")
        audio.currentTime = 0
        audio.play()

        # if the note is not sustained stop after two sections (1/2 of a beat)
        if self.hold:
            def stop_note():
                try:
                    audio.pause()
                except: 
                    print("error pausing audio")
            js.setTimeout(create_proxy(stop_note), 60000/tempo/divisions_per_beat*self.hold)

def clear_instrument_cb(event):
    if not can_edit: return

    instrument_name = event.target.id.replace("clear-", "")
    for note in notes[instrument_name]:
        notes[instrument_name][note] = [False] * (num_beats * divisions_per_beat)
    render()

def delete_instrument_cb(event):
    if not can_edit: return

    instrument_name = event.target.id.replace("delete-", "")
    del notes[instrument_name]
    del note_objects[instrument_name]
    render()
    


# --------------------
# File I/O
# --------------------
@when("change", "#navbar-load-file")
async def load_file_cb(event):

    # get the file
    files = event.target.files
    if files.length <= 0:
        return
    file = files.item(0)

    # ensure it's a JSON file
    if not file.name.endswith(".json"):
        js.alert("Please select a JSON file.")
        return
    
    # read and parse the file
    text = await file.text()
    data = json.loads(text)
    global tempo, num_beats, notes, divisions_per_beat
    tempo = data["tempo"]
    num_beats = data["num_beats"]
    notes = data["notes"]
    divisions_per_beat = data["divisions_per_beat"]

    # load the instrument data
    for instrument_name in notes:
        load_notes(instrument_name)
    render()

@when("click", "#navbar-save-json")
async def save_file_json_cb(event):
    data = {
        "tempo": tempo,
        "num_beats": num_beats,
        "notes": notes,
        "divisions_per_beat": divisions_per_beat
    }
    
    # make the data into a blob and download it
    blob = js.Blob.new([json.dumps(data)], { "type": "application/json" })
    url = js.URL.createObjectURL(blob)
    link = document.createElement("a")
    link.href = url
    link.download = "composition.json"
    link.click()

@when("click", "#navbar-export-wav")
def record_audio():
    js.alert("In order to record the audio, the website will record one full cycle of the composition. Please do not press the stop button to ensure that this does not fail.")

    # collect all Audio objects
    all_audio = []
    for _, instrument_notes in note_objects.items():
        for _, note_obj in instrument_notes.items():
            all_audio.extend(note_obj.audio_pool)

    # set the time for stopping the recording
    async def stop_recording():
        window.stopCapturingAudioTimeline()
        stop()

        # download the file
        await asyncio.sleep(0.5) # Quick buffer for processing
        blob_url = window.latestCombinedAudioUrl
        
        link = document.createElement("a")
        link.href = blob_url
        link.download = "composition.ogg"
        link.click()

    js.setTimeout(create_proxy(stop_recording), 60000/tempo/divisions_per_beat*num_beats*divisions_per_beat)

    # start recording
    window.startCapturingAudioTimeline(all_audio)
    play()

# --------------------
# Ruler
# --------------------

def render_ruler():
    render_template("templates/beat-ruler.html", "beat-ruler", num_beats=num_beats, divisions_per_beat=divisions_per_beat)

# --------------------
# Save to browser storage on exit
# --------------------
@when("visibilitychange", document)
def save_on_exit(event):
    print("Saving composition to local storage...")
    data = {
        "tempo": tempo,
        "num_beats": num_beats,
        "notes": notes,
        "divisions_per_beat": divisions_per_beat
    }
    js.localStorage.setItem("composition", json.dumps(data))

# Debugged with Copilot
def load_from_storage():
    data = js.localStorage.getItem("composition")
    if data:
        data = json.loads(data)
        global tempo, num_beats, notes, divisions_per_beat
        tempo = data["tempo"]
        num_beats = data["num_beats"]
        notes = data["notes"]
        divisions_per_beat = data["divisions_per_beat"]
        # load the instrument data
        for instrument_name in notes:
            load_notes(instrument_name)
        render()

async def main():
    init_navbar()
    render_ruler()
    try:
        load_from_storage()
    except: pass # no data to load
    
main()