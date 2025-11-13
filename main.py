import subprocess
from pathlib import Path
from tqdm import tqdm
import threading
import sys

# Function to prompt the user to enter a valid directory
# Will exit itself after 3 failed attempts
def prompt_directory(prompt_text: str, max_attempt: int = 2) -> Path:
  attempts: int = 0

  while attempts < max_attempt:
    user_input: str = input(prompt_text)

    if isinstance(user_input, str):
      user_input: str = user_input.strip()
      path: Path = Path(user_input).expanduser().resolve()

      if path.exists() and path.is_dir():
        return path
      else:
        print(f'{user_input} is not a valid directory path.')
    else:
      print('Input must be in string format')
    
    attempts += 1
  
  print('Too many invalid attempts... Exiting...')
  sys.exit(1)

# Prompt the user for input and output directories
input_directory: Path = prompt_directory('Enter input directory path (e.g., ./videos): ')
output_directory: Path = prompt_directory('Enter output directory path (e.g., ./videos_converted): ')
video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}

# Create the output directory if it doesn't already exist
output_directory.mkdir(parents=True, exist_ok=True)

# FFmpeg compression used to archiving
def high_compression(input_file, output_file):
  # Construct the FFmpeg command
  command = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx265',
    '-c:a', 'copy',
    '-crf', '28',
    output_file
  ]

  return command

# FFmpeg compression used for arching apple files natively
def regular_compression(input_file, output_file):
  # Construct the FFmpeg command
  command = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx264',
    '-c:a', 'copy',
    '-crf', '28',
    output_file
  ]

  return command

def stream_output(pipe):
  for line in iter(pipe.readline, b''):
    tqdm.write(line.decode('utf-8').strip())
  
  pipe.close()

def main():
  video_files = [f for f in input_directory.iterdir() if f.is_file() and f.suffix.lower() in video_extensions]
  apple_compatible = input('Do you want your file(s) to be apple compatible? (y/N): ')

  if not video_files:
    print('No video files found in the input directory')
    sys.exit(0)
  
  if apple_compatible.lower() not in ['y', 'yes']:
    with tqdm(total=len(video_files), desc='Processing Videos', unit='file') as progress_bar:
      # Iterate through files
      for file in video_files:
        output_file: Path = output_directory / file.with_suffix('.mp4').name
        cmd = high_compression(file, output_file)

        # Start FFmpeg process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Stream FFmpeg stderr (where progress info goes)
        stderr_thread = threading.Thread(target=stream_output, args=(process.stderr,))

        stderr_thread.start()
        process.wait()
        stderr_thread.join()

        if process.returncode == 0:
          progress_bar.set_postfix_str(f'{file.name}')

          try:
            file.unlink()
          except Exception as e:
            tqdm.write(f'Failed to delete {file.name}: {e}')
        else:
          progress_bar.set_postfix_str(f'Error: {file.name}')
        
        progress_bar.update(1)
  else:
    with tqdm(total=len(video_files), desc='Processing Videos', unit='file') as progress_bar:
      # Iterate through files
      for file in video_files:
        output_file: Path = output_directory / file.with_suffix('.mp4').name
        cmd = regular_compression(file, output_file)

        # Start FFmpeg process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Stream FFmpeg stderr (where progress info goes)
        stderr_thread = threading.Thread(target=stream_output, args=(process.stderr,))

        stderr_thread.start()
        process.wait()
        stderr_thread.join()

        if process.returncode == 0:
          progress_bar.set_postfix_str(f'{file.name}')

          try:
            file.unlink()
          except Exception as e:
            tqdm.write(f'Failed to delete {file.name}: {e}')
        else:
          progress_bar.set_postfix_str(f'Error: {file.name}')
        
        progress_bar.update(1)

if __name__ == '__main__':
  main()
