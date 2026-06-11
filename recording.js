let mediaRecorder;
let recordedChunks = [];

function startCapturingAudioTimeline(audioElementsList) {
    recordedChunks = [];
    
    // 1. Create a centralized audio routing manager
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // 2. Set up an internal recording destination node (bypasses system mic inputs)
    const recordDestination = audioContext.createMediaStreamDestination();
    
    // 3. Route every audio element into our recorder AND the user's speakers
    audioElementsList.forEach(audioObj => {
        // Intercept the element's audio output path
        const source = audioContext.createMediaElementSource(audioObj);
        
        source.connect(recordDestination);             // Route to the recorder
        source.connect(audioContext.destination);       // Route to speakers so user still hears it
    });
    
    // 4. Bind the internal stream directly into a MediaRecorder engine
    mediaRecorder = new MediaRecorder(recordDestination.stream);
    
    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };
    
    mediaRecorder.onstop = () => {
        // Compile all streaming data pieces together natively into a standard OGG/WebM file
        const mixedAudioBlob = new Blob(recordedChunks, { type: 'audio/ogg; codecs=opus' });
        
        // Expose the temporary link globally so PyScript can read or download it
        window.latestCombinedAudioUrl = URL.createObjectURL(mixedAudioBlob);
        console.log("Audio combined successfully! Link ready.");
    };
    
    // Fire up the engine
    mediaRecorder.start();
}

function stopCapturingAudioTimeline() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }

    // Disconnect all audio nodes to clean up resources
    mediaRecorder = null;
}