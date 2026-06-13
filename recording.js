// Created with copilot

let mediaRecorder;
let recordedChunks = [];

// Start recording all audio elements
function startCapturingAudioTimeline(audioElementsList) {
    recordedChunks = [];
    
    // Create a centralized audio routing manager
    const audioContext = new(window.AudioContext || window.webkitAudioContext)();
    
    // Set up an internal recording destination node (bypasses system mic inputs)
    const recordDestination = audioContext.createMediaStreamDestination();
    
    // Route every audio element into the recorder and the user's speakers
    audioElementsList.forEach(audioObj => {
        // Intercept the element's audio output path
        const source = audioContext.createMediaElementSource(audioObj);
        
        source.connect(recordDestination); // Route to the recorder
        source.connect(audioContext
            .destination); // Route to speakers so user still hears it
    });
    
    // Bind the internal stream directly into a MediaRecorder engine
    mediaRecorder = new MediaRecorder(recordDestination.stream);
    
    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };
    
    // When recording stops, compile the chunks into a single audio file
    mediaRecorder.onstop = () => {
        // Compile all streaming data pieces together natively into a standard OGG/WebM file
        const mixedAudioBlob = new Blob(recordedChunks, { type: 'audio/ogg; codecs=opus' });
        
        // Expose the temporary link globally so PyScript can read or download it
        window.latestCombinedAudioUrl = URL.createObjectURL(mixedAudioBlob);
    };
    
    // Fire up the engine
    mediaRecorder.start();
}

// Stop recording and trigger the onstop event to finalize the audio file
function stopCapturingAudioTimeline() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
}