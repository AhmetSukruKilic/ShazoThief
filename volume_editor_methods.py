import numpy as np
import librosa
from scipy.ndimage import maximum_filter

def get_peaks(S_db, threshold_db=-30, neighborhood_size=20):
    local_max = maximum_filter(S_db, size=neighborhood_size) == S_db
    detected_peaks = (S_db > threshold_db) & local_max
    return np.argwhere(detected_peaks)  

def generate_hashes(peaks, fan_value=5, max_delta_frames=200):
    peaks = np.array(sorted(peaks, key=lambda x: x[1]))
    hashes = []  # list of tuples (hash_val, anchor_time)
    num_peaks = peaks.shape[0]

    for i in range(num_peaks):
        f1, t1 = peaks[i]
        # Pair with the next fan_value peaks (or until time difference > max_delta_frames)
        for j in range(1, fan_value + 1):
            if i + j >= num_peaks:
                break
            f2, t2 = peaks[i + j]
            dt = t2 - t1
            if dt <= 0 or dt > max_delta_frames:
                continue
            # e.g.  hash_val = (f1 & 0xFFFF) << 48 | (f2 & 0xFFFF) << 32 | (dt & 0xFFFFFFFF)
            hash_val = (int(f1) << 48) | (int(f2) << 32) | (int(dt) & 0xFFFFFFFF)
            hashes.append((hash_val, int(t1)))
    return hashes


def hash_music(query_filepath):
    yq, srq = librosa.load(query_filepath, sr=None)
    Sq = librosa.stft(yq, n_fft=2048, hop_length=512)
    duration_secs = int(len(yq) / srq)
    S_db_q = librosa.amplitude_to_db(np.abs(Sq), ref=np.max)
    peaks_q = get_peaks(S_db_q, threshold_db=-30, neighborhood_size=15)
    hashes_q = generate_hashes(peaks_q, fan_value=5, max_delta_frames=200)
    
    return duration_secs, hashes_q