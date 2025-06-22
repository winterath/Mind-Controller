import time
import numpy as np
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes
from scipy.signal import welch
from pynput.keyboard import Controller, Key

# Define frequency bands and corresponding keys
bands = {
    'W': (2.5, 3.5),   # 3 Hz ± 0.5 Hz
    'A': (5.5, 6.5),   # 6 Hz ± 0.5 Hz
    'S': (8.5, 9.5),   # 9 Hz ± 0.5 Hz
    'D': (11.5, 12.5), # 12 Hz ± 0.5 Hz
    'Space': (14.5, 15.5) # 15 Hz ± 0.5 Hz
}

# Define power thresholds (adjust based on actual data)
thresholds = {
    'W': 1000,
    'A': 1000,
    'S': 1000,
    'D': 1000,
    'Space': 1000
}

# Map keys to pynput key objects
key_map = {
    'W': 'w',
    'A': 'a',
    'S': 's',
    'D': 'd',
    'Space': Key.space
}

# Initialize synthetic board
params = BrainFlowInputParams()
board = BoardShim(BoardIds.SYNTHETIC_BOARD.value, params)
board.prepare_session()
board.start_stream()

# Initialize keyboard controller
keyboard = Controller()

# Main processing loop
try:
    while True:
        # Get latest 256 samples
        data = board.get_current_board_data(256)
        if data.shape[1] < 256:
            continue

        # Extract first EEG channel
        eeg_channels = BoardShim.get_eeg_channels(BoardIds.SYNTHETIC_BOARD.value)
        signal = data[eeg_channels[0]]

        # Apply bandpass filter (1-20 Hz)
        sampling_rate = board.get_sampling_rate(BoardIds.SYNTHETIC_BOARD.value)
        DataFilter.perform_bandpass(signal, sampling_rate, 1.0, 20.0, 4, FilterTypes.BUTTERWORTH.value, 0)

        # Compute power spectral density
        freqs, psd = welch(signal, fs=sampling_rate, nperseg=256)

        # Check each frequency band
        for key, (low, high) in bands.items():
            indices = np.where((freqs >= low) & (freqs <= high))
            band_power = np.sum(psd[indices])
            if band_power > thresholds[key]:
                keyboard.press(key_map[key])
                keyboard.release(key_map[key])
                time.sleep(0.5)  # Debounce delay
                break  # Trigger only one key per cycle

        time.sleep(0.1)  # Control loop rate

except KeyboardInterrupt:
    # Clean up on exit
    board.stop_stream()
    board.release_session()
    print("Streaming stopped.")