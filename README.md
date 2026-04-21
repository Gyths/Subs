# Subs
Local live audio translation/transcription tool for Eng<->Spa powered by whisper and helsinki-NLP<br/>

## Demo
<img width="496" height="1225" alt="image" src="https://github.com/user-attachments/assets/ca345499-9cab-4368-941d-7bdc0536111f" />

## Features
- Bidirectional - Transcribes and translates both languages simultaneously
- Persistent text - Text wont disapear until cleared
- Virtual cable ready — Capture desktop or window audio via virtual audio devices
- Noise gate — Simple speech detection filters silence and reduces hallucinations

## Architecture
Mic/Virtual cable -> Captures audio segment<br/>
webcrtvad -> Detects if a segment contains speech<br/>
whisper turbo -> Transcribes segment, detects language<br/>
helsinki ML -> Translates into target language<br/>

## Setup
1. Clone the repo and install dependencies
2. Configure your mic in whisper_to_text.py parameters
`DEVICE=your mic number`
3. Run the bot

## Usage
Press start to start listening<br/>
Transcriptions and translations detected as english will pop up on the english box, same with spanish<br/>
To capture desktop audio or a specific application, route it through a virtual audio cable (e.g. VB-Cable) and set that as your DEVICE<br/>
There are clear buttons for each box<br/>

## Known Issues
Occasionally hangs and requires a restart — a proper reset button is on the roadmap<br/>

## Roadmap
- Fine tuning whisper for accents
- Fine tuning helsinki or other ML model for domain specific translations
- Consider local LLM context translation
- Better UI
- Reset button
