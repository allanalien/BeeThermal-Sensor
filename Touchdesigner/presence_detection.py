import argparse
from collections import namedtuple
from scipy import signal
import numpy as np

from ifxradarsdk import get_version_full
from ifxradarsdk.fmcw import DeviceFmcw
from ifxradarsdk.fmcw.types import FmcwSimpleSequenceConfig, FmcwSequenceChirp
from helpers.fft_spectrum import fft_spectrum


class PresenceAntiPeekingAlgo:
    def __init__(self, num_samples_per_chirp, num_chirps_per_frame):
        """Presence and Anti-Peeking Algorithm

        This is a simple use case of a presence detection and
        anti-peeking demo.

        Parameters:
            num_samples_per_chirp: Number of samples per chirp
            num_chirps_per_frame: Number of chirps per frame
        """
        self.num_samples_per_chirp = num_samples_per_chirp
        self.num_chirps_per_frame = num_chirps_per_frame

        # Algorithm Parameters
        self.detect_start_sample = num_samples_per_chirp // 8
        self.detect_end_sample = num_samples_per_chirp // 2
        self.peek_start_sample = num_samples_per_chirp // 2
        self.peek_end_sample = num_samples_per_chirp

        self.threshold_presence = 0.0007
        self.threshold_peeking = 0.0006

        self.alpha_slow = 0.001
        self.alpha_med = 0.05
        self.alpha_fast = 0.6

        # Initialize state
        self.presence_status = False
        self.peeking_status = False
        self.first_run = True

        # compute Blackman-Harris Window matrix over chirp samples(range)
        # Use try-except to cater Scipy versions issue for windowing function
        try:
            self.range_window = signal.blackmanharris(num_samples_per_chirp).reshape(1, num_samples_per_chirp)
        except AttributeError:
            self.range_window = signal.windows.blackmanharris(num_samples_per_chirp).reshape(1, num_samples_per_chirp)

    def presence(self, mat):
        """Run the presence and anti-peeking algorithm on the current frame.

        Parameters:
            - mat: Radar data for one antenna as returned by Frame.get_mat_from_antenna

        Returns:
            - Named tuple with presence and peeking booleans.
        """
        alpha_slow = self.alpha_slow
        alpha_med = self.alpha_med
        alpha_fast = self.alpha_fast

        # Compute range FFT
        range_fft = fft_spectrum(mat, self.range_window)

        # Average absolute FFT values over number of chirps
        fft_spec_abs = abs(range_fft)
        fft_norm = np.divide(fft_spec_abs.sum(axis=0), self.num_chirps_per_frame)

        # Presence sensing
        if self.first_run:  # initialize averages
            self.slow_avg = fft_norm
            self.fast_avg = fft_norm
            self.slow_peek_avg = fft_norm
            self.first_run = False

        if not self.presence_status:
            alpha_used = alpha_med
        else:
            alpha_used = alpha_slow

        self.slow_avg = self.slow_avg * (1 - alpha_used) + fft_norm * alpha_used
        self.fast_avg = self.fast_avg * (1 - alpha_fast) + fft_norm * alpha_fast
        data = self.fast_avg - self.slow_avg

        self.presence_status = np.max(data[self.detect_start_sample:self.detect_end_sample]) > self.threshold_presence

        # Peeking sensing
        if not self.peeking_status:
            alpha_used = alpha_med
        else:
            alpha_used = alpha_slow

        self.slow_peek_avg = self.slow_peek_avg * (1 - alpha_used) + fft_norm * alpha_used
        data_peek = self.fast_avg - self.slow_peek_avg

        self.peeking_status = np.max(data_peek[self.peek_start_sample:self.peek_end_sample]) > self.threshold_peeking

        return namedtuple("state", ["presence", "peeking"])(self.presence_status, self.peeking_status)


if __name__ == "__main__":

    # -----------------------------------------------------------
    # Arguments
    # -----------------------------------------------------------
    parser = argparse.ArgumentParser(
        description='Derives presence and peeking information from Radar Data')
    parser.add_argument('-n', '--nframes', type=int, default=100, help="number of frames, default 100")
    parser.add_argument('-f', '--frate', type=int, default=5, help="frame rate in Hz, default 5")
    args = parser.parse_args()

    config = FmcwSimpleSequenceConfig(
        frame_repetition_time_s=.5 / args.frate,  # Frame repetition time default 0.2s (frame rate of 5Hz)
        chirp_repetition_time_s=0.00070,  # Chirp repetition time of 700us
        num_chirps=32,  # 32 chirps per frame
        tdm_mimo=False,  # MIMO disabled
        chirp=FmcwSequenceChirp(
            start_frequency_Hz=58_000_000_000,  # start frequency: 58 GHz
            end_frequency_Hz=61_232_137_439,  # end frequency: ~61.2 GHz
            sample_rate_Hz=1e6,  # ADC sample rate of 1MHz
            num_samples=256,  # 256 samples per chirp
            rx_mask=1,  # RX antenna 1 activated
            tx_mask=1,  # TX antenna 1 activated
            tx_power_level=31,  # TX power level of 31
            lp_cutoff_Hz=500000,  # Anti-aliasing cutoff frequency 500kHz
            hp_cutoff_Hz=80000,  # High-pass filter cutoff 80kHz
            if_gain_dB=33,  # IF gain 33 dB
        )
    )

    with DeviceFmcw() as device:
        print(f"Radar SDK Version: {get_version_full()}")
        print("Sensor: " + str(device.get_sensor_type()))

        # set device config for presence sensing
        sequence = device.create_simple_sequence(config)
        device.set_acquisition_sequence(sequence)

        # initialize the algorithm
        algo = PresenceAntiPeekingAlgo(config.chirp.num_samples, config.num_chirps)

        for frame_number in range(args.nframes):
            # Get radar data for the first RX antenna
            frame_contents = device.get_next_frame()
            frame = frame_contents[0]

            # matrix of dimension num_chirps_per_frame x num_samples_per_chirp for RX1
            mat = frame[0, :, :]
            presence_status, peeking_status = algo.presence(mat)

            print(f"Presence: {presence_status}")
            print(f"Peeking: {peeking_status}")