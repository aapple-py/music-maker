# Music Maker
#### Video Demo:  [link](https://youtu.be/wvxVP85xZL8)
- EDIT FROM VIDEO: the files download in .ogg, not .wav. The dropdown has been changed to match.

#### Live link: [link](https://musicmaker.andrewjkramer.dev)

## Description:

This project is a website that allows users to write music for various instruments. Note that it is not meant or recommended to be used on mobile as it will be harder to see as many of the notes.

## AI/Copilot use
All of the ideas in this project were created by me (a human). However, copilot was used to aid in debugging various features after I tried and failed to locate the bug. These sections of code are marked with a 'Debugged with copilot' comment. Any exceptions to this are detailled in the sections below.

## Stack:
this website's frontend is in html, css and javascript following what we learned. This uses bootstrap for some of the ui elements. Some of the more complex features are in python, as I was more comfortable with that language, and connected to the javascript using pyscript. The html is formatted with Jinja, seperate from flask.

## File contents:

##### samples/
Th directory contains all of the music files I used as sources, organized by instrument. These are in .ogg format because it is compact and thus the browser would have an easier time downloading them. They were generated from one sample at around the middle of an instrument's range that was then stretched/compressed by a seperate python script to generate the required audio. 

The instruments.json file contains the information that the site uses to read these files. It tells the python code what instruments are present and which notes they have, which in turn tells the code which files to load. 

### config.json
This file tells pyscript which libraries and files the python will use. Note that it does not contain the audio files, those are connected another way (more details below)

### recording.js
This file containts two helper functions that are used to record the audio that the browser is playing, which allows the user to download it as a .ogg file. Majority of this file was generated with copilot, as I was having a hard time interfacing with the browser's audio system. The idea for the recording mechanism and how it allows the user to save the file were still mine.

### index.html
This file is the main layout. It has most of the page, with a few spots for templates. At the top and bottom are script inclusions for the main.py and recording.js, pyscript, and bootstrap. Note that an html checker will likely flag the python import as it is not native to html, but using pyscript it is valid syntax.

The first part of the body contains the navbar. It is a bootstrap ui element that makes the selection window at the top of the page.

After that is the ruler - the line of numbers at the top that indicate to the user what beat they are on. This part also has a template as the beat numbers are also generated dynamically.

Finally, there is the main instrument grid. This is a template too.

### templates/
These are the three templates that fill the various spots in index.html. 

#### beat-ruler.html
This contains the code for the ruler, dynamically generated with jinja. It creates a beat element for each beat, after which there are a number of spacers determined by the number of divisions per beat. There is also a spacer at the start to align the ruler with the grid.

#### main-area.html
This contains the code for the instrument list and grid. First, it makes a list of all of the instruments, with their name, clear and delete buttons, volume control, and note lists. Then it dynamically generates the grid to size. Each button and grid cell also has a dynamically generated id so it can be accessed by the python code to add callbacks.

#### navbar-instrument-list.html
This file generates the dynamic instrument list used in the dropdown. It creates one list item for each, setting its id so it can be accessed later.

#### style.css
This file contains the styles for many of the elements. To find these attributes, I frequently googled 'what css element does...'. Other than that, little AI was used to create the file. The only part of the file that is especially interesting is the beat class. It comes in many varieties to have notes in or not, playing or not, and with a light border to make the beat lines.

#### main.py
This file contains the main python code. I will go through it section by section:

The render_template function is a jinja-only version of flask's render-template. This will be used later.

Then there is a series of functions relating to the navbar. The first of these initializes it with the dynamic instrument list. Then there are callback functions to the buttons on the navbar. This is the first part where the advantages of python were immediately obvious, as the @when decorator made the registering of callbacks much easier. The last three of these callbacks just load and verify the input, and then set a global. The first one has to be attatched to dynamically generated list elements, so I bound it to the parent and got the child id from the event argument.

Then there are the functions to do with the main section. The first one, ensure_notes_length makes sure that when the number of beats changes the list gets longer to match. The next few functions deal with the dynamic callbacks for the volume controls and the note squares, and instrument clear and delete buttons. Since those elements are added and removed, I had to create functions that registered the callbacks for each instrument. There are also multiple functions for registering the notes, some for clicking and some for dragging. Finally there is the functon render(). It renders the main section and then re-registers these callbacks.  

Then there are the functions that play the audio. The Note class defines the main audio system. Initially this was just a single Audio object, but there was a bug if you tried to play the same note in too quick succession. Because of this, the Note class implements a round-robin style of sharing of note calls between 5 audio ojects which removes the issue. The function play checks the notes dict and plays the corresponding Note elements, and the stop function stops it. Finally, there is a function called load_notes. This function is called when an instrument is added and it downloads and adds that note's Audio and Note objects. One important idea is that the files for an instrument are only loaded as needed, meaining that the browser does not have to load more data than necessary or too much data at once.

Next, there are some more functions to do with file saving. First is the one that loads a file from json. It first takes and validates the file before setting the globals to its contents, loading its instruments and rendering the grid. Then there is the function that takes the globals and saves them to the json, before downloading it. The downloading works by creating a link to the file, a link element to the link, and then clicking the link. Finally, there is the function to save the audio. It starts the javascript recording before playing the audio, and then stops both on a timeout. Then it downloads the resulting file in the same way as the json download.

Then there is a function, called in render(), that renders the ruler using the render_template function.

Then there are two functions that save and load data to/from the browser cache. These are very similar to the json loading, except instead of downloading/accepting a file they stringify the json and then store it. The store one is also called using @when to execute when the browser exits the page for any reasong.

Finally, we have the entry point. It calls the init functions for the navbar and ruler, and loads data from storage if it is there.