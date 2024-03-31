import requests
from openai import OpenAI
import sys
from flask_socketio import SocketIO

socketio = SocketIO(message_queue='redis://localhost:6379')

def process_image(url):
    print(f"Processing image URL: {url}")
    # Add your image processing logic here

if __name__ == '__main__':
    if len(sys.argv) > 1:
        image_url = sys.argv[1]
        process_image(image_url)
    else:
        print("No image URL provided.")

def call_apis_and_generate_image(astica_key, image_url):
    face_detection_response = requests.post(
        "https://ivladmin-face-detection.p.rapidapi.com/faceSearch/detectFaces",
        data={'objecturl': image_url},
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": "c8026097d9msh012eea28002f6d4p12c7ddjsn45f3cac68c2a",
            "X-RapidAPI-Host": "ivladmin-face-detection.p.rapidapi.com"
        }
    ).json()

    astica_response = requests.post(
        'https://vision.astica.ai/describe',
        json={
            'tkn': astica_key,
            'modelVersion': '2.1_full',
            'visionParams': 'gpt_detailed,describe,faces',
            'gpt_prompt': "Describe the head, race, eyes & face in detail to allow a GPT to recreate skull and facial muscle.",
            'input': image_url,
        },
        headers={'Content-Type': 'application/json'}
    ).json()

    prompt = f"Facial landmark data and descriptive date about the face: {face_detection_response}, Astica data: {astica_response}"
    return prompt

def generate_complete_prompt(astica_key, image_url):
    dynamic_prompt = call_apis_and_generate_image(astica_key, image_url)
    instructions = "Describe the face you have details on in the prose style of author Mary Shelley "
    complete_prompt = instructions + dynamic_prompt
    return complete_prompt

if __name__ == "__main__":
    image_url = sys.argv[1]  # This line defines image_url based on the command-line argument
    astica_key = "F7C51C17-7085-471E-BACF-5E0C72E62E15FB9C938F-B250-462B-9935-9391D6EEF16E"

    complete_prompt = generate_complete_prompt(astica_key, image_url)

def generate_complete_prompt(astica_key, image_url):
    dynamic_prompt = call_apis_and_generate_image(astica_key, image_url)
    instructions = "Describe the face you have details on in the prose style of author Mary Shelley. "
    complete_prompt = instructions + dynamic_prompt
    return complete_prompt

client = OpenAI()
complete_prompt = generate_complete_prompt(astica_key, image_url)

stream = client.chat.completions.create(
    model='gpt-4-0125-preview',
    messages=[
        {"role": "system", "content": "Frankenstein Author Mary Shelley"},
        {"role": "user", "content": complete_prompt}
    ],
    stream=True,
    max_tokens=2500,
)

word_buffer = ""  # Initialize a word buffer to accumulate characters into words.

for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content

        # Add new content to the existing word buffer.
        word_buffer += content

        # Process the buffer, emitting when full words are detected.
        while " " in word_buffer:
            # Split the buffer at the first space to extract the word.
            word, _, remainder = word_buffer.partition(" ")
            
            # If the word ends with punctuation, it's considered a complete sentence part, emit it and reset buffer.
            if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                print(f"Emitting: {word + ' '}")  # Add logging statement
                socketio.emit('stream_data', {'content': word + ' '})
                word_buffer = remainder  # Update the word buffer with the remaining content.
            else:
                # For words without punctuation, emit the word followed by a space.
                print(f"Emitting: {word + ' '}")  # Add logging statement
                socketio.emit('stream_data', {'content': word + ' '})
                word_buffer = remainder  # Update the word buffer with the remaining content.

# After the loop, emit any remaining content in the word buffer.
if word_buffer.strip():
    print(f"Emitting remaining content: {word_buffer.strip()}")  # Add logging statement
    socketio.emit('stream_data', {'content': word_buffer.strip()})