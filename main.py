from jinja2 import Template
from pyscript import document, when, fs
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
file_connected = False

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
@when("click", "#navbar-export-wav")
def export_wav_cb(event):
    print("export wav")

def add_instrument(name):
    # add to notes dict
    notes[name] = {note: [False] * (num_beats * 4) for note in instrument_dict[name]["notes"]}

    # load the note objects if we haven't already
    if name not in note_objects:
        load_notes(name)

    render()

    

@when("click", "#navbar-instrument-list")
async def instrument_cb(event):
    # this is a good time to ensure file i/o is working
    global file_connected
    if not file_connected:
        await fs.mount("/appdata", mode="readwrite")
        file_connected = True


    if not can_edit: return

    if event.target.id.startswith("navbar-instrument-"):
        try:
            instrument_id = event.target.id.replace("navbar-instrument-", "")
            if instrument_id not in notes:
                add_instrument(instrument_id)
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
def render():
    render_template("templates/main-area.html", "main-area", instruments=[instrument_dict[i] for i in notes], num_beats=num_beats, current_notes=notes)
    register_note_callbacks()
    ensure_notes_length()

    # ensure the callbacks are registered; debugged with Copilot
    for name in notes:
        document.getElementById(f"clear-{name}").addEventListener("click", create_proxy(clear_instrument_cb))
        document.getElementById(f"delete-{name}").addEventListener("click", create_proxy(delete_instrument_cb))

def ensure_notes_length():
    for instrument_name, instrument_notes in notes.items():
        for note_name, beats in instrument_notes.items():
            if len(beats) < num_beats * 4:
                beats.extend([False] * (num_beats * 4 - len(beats)))
            elif len(beats) > num_beats * 4:
                notes[instrument_name][note_name] = beats[:num_beats * 4]

def register_note_callbacks():
    for instrument_name, instrument_notes in notes.items():
        for note_name, beats in instrument_notes.items():
            for beat in range(num_beats * 4):
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
    ms_per_beat = 60000 / (tempo * 4) # 4 for 16th notes
    beat = 0

    def play_beat():
        nonlocal beat
        prev_beat = (beat - 1) % (num_beats * 4)

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
        beat = (beat + 1) % (num_beats * 4)

        
    # schedule the beat playback
    global play_interval_id
    play_interval_id = js.setInterval(create_proxy(play_beat), ms_per_beat)

def stop():
    global play_interval_id
    js.clearInterval(play_interval_id)

    # remove "playing" class from all notes    
    for instrument_name, instrument_notes in notes.items():
        for note_name, beats in instrument_notes.items():
            for beat in range(num_beats * 4):
                document.getElementById(f"{instrument_name}-beat-{beat}-note-{note_name}").classList.remove("playing")

def load_notes(instrument_name):
    note_objects[instrument_name] = {}
    for note in notes[instrument_name]:
        note_objects[instrument_name][note] = Note(f"samples/{instrument_name}/{note}.ogg", instrument_dict[instrument_name].get("hold", None))

class Note:
    def __init__(self, path, hold_duration):
        self.path = path
        self.hold = hold_duration
        self.audio = js.Audio.new(path)

    def play(self):
        self.audio.currentTime = 0
        self.audio.play()

        # if the note is not sustained stop after two sections (1/2 of a beat)
        if self.hold:
            js.setTimeout(create_proxy(lambda: self.audio.pause()), 60000/tempo/4*self.hold)

def clear_instrument_cb(event):
    if not can_edit: return

    instrument_name = event.target.id.replace("clear-", "")
    for note in notes[instrument_name]:
        notes[instrument_name][note] = [False] * (num_beats * 4)
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
    global tempo, num_beats, notes
    tempo = data["tempo"]
    num_beats = data["num_beats"]
    notes = data["notes"]

    # load the instrument data
    for instrument_name in notes:
        add_instrument(instrument_name)

@when("click", "#navbar-save-json")
async def save_file_json_cb(event):
    if not file_connected:
        return
    
    print("saving file")
    data = {
        "tempo": tempo,
        "num_beats": num_beats,
        "notes": notes
    }
    with open("/appdata/composition.json", "w") as file:
        json.dump(data, file)
    await fs.sync("/appdata")
    js.alert("Saved composition to composition.json")


async def main():
    init_navbar()
    
main()