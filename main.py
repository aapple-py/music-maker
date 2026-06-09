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
num_beats = 4

# --------------------
# Navbar class
# --------------------

class Navbar:
    """
    Registers and detects navbar button callbacks.
    """
    def __init__(self):
        
        # render navbar dropdown
        with open("samples/instruments.json", "r") as file:
            instruments = json.load(file)
        instrument_list = [instrument["name"] for instrument in instruments]
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
        instrument_id = event.target.id.replace("navbar-instrument-", "").replace("-", " ")
        print(f"add {instrument_id}")

    @staticmethod
    @when("click", "#navbar-settings-beats")
    def settings_beats_cb(event):
        print("settings beats")

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

def main():
    nav = Navbar()
    
main()