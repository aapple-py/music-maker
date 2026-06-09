from jinja2 import Template
from pyscript import document, when
import js # type: ignore
import json
import time

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

with open("samples/instruments.json", "r") as file:
    all_instruments = json.load(file)
instrument_dict = {instrument["name"]: instrument for instrument in all_instruments}

# --------------------
# Navbar class
# --------------------

class Navbar:
    """
    Registers and detects navbar button callbacks.
    """
    def __init__(self):
        
        # render navbar dropdown
        instrument_list = [instrument["name"] for instrument in all_instruments]
        render_template("templates/navbar-instrument-list.html", "navbar-instrument-list", instruments=instrument_list)

    # the callbacks
    @staticmethod
    @when("click", "#navbar-import")
    def import_cb(event):
        print("import")

    @staticmethod
    @when("click", "#navbar-export-wav")
    def export_wav_cb(event):
        print("export wav")
    
    @staticmethod
    @when("click", "#navbar-export-json")
    def export_json_cb(event):
        print("export json")

    @staticmethod
    @when("click", "#navbar-instrument-list")
    def instrument_cb(event):
        if 'navbar-instrument-' in event.target.id:
            instrument_id = event.target.id.replace("navbar-instrument-", "")
            if instrument_id not in notes:
                notes[instrument_id] = {note["name"]: [False] * (num_beats * 4) for note in instrument_dict[instrument_id]["notes"]}
                render()
        else: # import from wav
            print("import wav")

    @staticmethod
    @when("click", "#navbar-set-beats")
    def settings_beats_cb(event):
        try:
            global num_beats
            new_num_beats = int(document.getElementById("navbar-beats").value)
            assert 1 <= new_num_beats
            num_beats = new_num_beats
        except ValueError:
            js.alert("Please enter a valid number for the number of beats.")
        except AssertionError:
            js.alert("Please enter a number of beats between 1 and 16.")
        print(f"settings beats: {num_beats}")
        render()


    @staticmethod
    @when("click", "#navbar-set-tempo")
    def settings_tempo_cb(event):
        try:
            global tempo
            new_tempo = float(document.getElementById("navbar-tempo").value)
            assert 20 <= new_tempo <= 300
            tempo = new_tempo
        except ValueError:
            js.alert("Please enter a valid number for the tempo.")
        except AssertionError:
            js.alert("Please enter a tempo between 20 and 300 BPM.")
        print(f"settings tempo: {tempo}")

    @staticmethod
    @when("click", "#navbar-play")
    def play_cb(event):
        print("play")

# --------------------
# Main section
# --------------------
def render():
    render_template("templates/main-area.html", "main-area", instruments=[instrument_dict[i] for i in notes], num_beats=num_beats)
    register_note_callbacks()

def register_note_callbacks():
    for instrument_name, instrument_notes in notes.items():
        for note_name, beats in instrument_notes.items():
            for beat in range(num_beats * 4):
                @when("click", f"#{instrument_name}-beat-{beat}-note-{note_name}")
                def note_cb(event, instrument_name=instrument_name, note_name=note_name, beat=beat):
                    beats[beat] = not beats[beat]
                    event.target.classList.toggle("active")



def main():
    nav = Navbar()
    
main()