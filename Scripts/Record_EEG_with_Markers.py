#!/usr/bin/env python3
"""
OpenBCI Cyton+Daisy EEG Data Streamer with Synchronized Video and Markers
Streams 16-channel EEG data via Bluetooth with MI cue markers synchronized to video playback
"""

import time
import csv
import numpy as np
import pandas as pd
from datetime import datetime
import threading
import signal
import sys
import subprocess
import os
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter

class EEGStreamerWithVideo:
    def __init__(self, serial_port='/dev/ttyUSB0', csv_filename=None, video_path=None, marker_csv='marker.csv'):
        self.serial_port = serial_port
        self.csv_filename = csv_filename or f"eeg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.video_path = video_path
        self.marker_csv = marker_csv
        
        # Board setup
        self.board_id = BoardIds.CYTON_DAISY_BOARD
        self.params = BrainFlowInputParams()
        self.params.serial_port = serial_port
        self.board = BoardShim(self.board_id, self.params)
        
        # Data tracking
        self.is_streaming = False
        self.sample_count = 0
        self.start_time = None
        self.recording_start_time = None
        self.csv_file = None
        self.csv_writer = None
        
        # Video and marker control
        self.video_process = None
        self.markers_df = None
        self.current_marker = ""
        self.marker_thread = None
        
        # Sampling rate monitoring
        self.last_sample_count = 0
        self.last_time = None
        self.sampling_rates = []
        
        # Load markers
        self.load_markers()
        
        # Setup signal handler for clean exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\nStopping data stream...")
        self.stop_streaming()
        sys.exit(0)
    
    def load_markers(self):
        """Load marker data from CSV file"""
        try:
            if os.path.exists(self.marker_csv):
                self.markers_df = pd.read_csv(self.marker_csv)
                print(f"Loaded {len(self.markers_df)} markers from {self.marker_csv}")
                print("Marker preview:")
                print(self.markers_df.head())
                print()
            else:
                print(f"Warning: Marker file {self.marker_csv} not found!")
                self.markers_df = pd.DataFrame(columns=['time_seconds', 'label'])
        except Exception as e:
            print(f"Error loading markers: {e}")
            self.markers_df = pd.DataFrame(columns=['time_seconds', 'label'])
    
    def get_video_path(self):
        """Get video path from user if not provided"""
        if self.video_path and os.path.exists(self.video_path):
            return self.video_path
            
        print("Please enter the path to your MI cue video file:")
        video_path = input("Video path: ").strip()
        
        if not os.path.exists(video_path):
            print(f"Error: Video file not found at {video_path}")
            return None
            
        return video_path
        
    def setup_csv(self):
        """Initialize CSV file with OpenBCI_GUI compatible headers"""
        headers = [
            'Sample Index',
            'EXG Channel 0', 'EXG Channel 1', 'EXG Channel 2', 'EXG Channel 3',
            'EXG Channel 4', 'EXG Channel 5', 'EXG Channel 6', 'EXG Channel 7',
            'EXG Channel 8', 'EXG Channel 9', 'EXG Channel 10', 'EXG Channel 11',
            'EXG Channel 12', 'EXG Channel 13', 'EXG Channel 14', 'EXG Channel 15',
            'Accel Channel 0', 'Accel Channel 1', 'Accel Channel 2',
            'Other', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other',
            'Other', 'Other', 'Timestamp', 'Marker Channel', 'Timestamp (Formatted)'
        ]
        
        self.csv_file = open(self.csv_filename, 'w', newline='', buffering=1)  # Line buffering for minimal latency
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(headers)
    
    def start_video_player(self, video_path):
        """Start video player (MPV prioritized)"""
        players = [
            # MPV (preferred - working on your system)
            {
                'cmd': ['mpv', video_path, '--fullscreen', '--no-terminal'],
                'name': 'MPV'
            },
            # VLC (fallback)
            {
                'cmd': ['vlc', video_path, '--fullscreen', '--no-video-title-show', '--quiet'],
                'name': 'VLC'
            },
            # GNOME Videos (Totem)
            {
                'cmd': ['totem', video_path, '--fullscreen'],
                'name': 'GNOME Videos'
            },
            # FFplay (minimal)
            {
                'cmd': ['ffplay', video_path, '-fs', '-autoexit', '-loglevel', 'quiet'],
                'name': 'FFplay'
            }
        ]
        
        for player in players:
            try:
                print(f"Trying to start {player['name']} with video: {video_path}")
                self.video_process = subprocess.Popen(player['cmd'])
                print(f"Successfully started {player['name']}")
                return True
            except FileNotFoundError:
                print(f"{player['name']} not found, trying next player...")
                continue
            except Exception as e:
                print(f"Error starting {player['name']}: {e}")
                continue
        
        print("No video player found! Please install MPV:")
        print("- MPV: sudo apt install mpv")
        return False
    
    def marker_control_thread(self):
        """Thread to control markers based on timing"""
        if self.markers_df.empty:
            return
            
        print("Marker control thread started")
        marker_index = 0
        
        while self.is_streaming and marker_index < len(self.markers_df):
            if self.recording_start_time is None:
                time.sleep(0.01)
                continue
                
            # Calculate elapsed time since recording started
            elapsed_time = time.time() - self.recording_start_time
            
            # Check if it's time for the next marker
            marker_time = self.markers_df.iloc[marker_index]['time_seconds']
            
            if elapsed_time >= marker_time:
                marker_label = self.markers_df.iloc[marker_index]['label']
                self.current_marker = marker_label
                print(f"\n[MARKER] Time: {elapsed_time:.2f}s - {marker_label}")
                
                # Clear marker after a short duration (adjust as needed)
                threading.Timer(0.1, self.clear_current_marker).start()
                
                marker_index += 1
            
            time.sleep(0.01)  # Check every 10ms for precise timing
    
    def clear_current_marker(self):
        """Clear the current marker"""
        self.current_marker = ""
    
    def countdown(self, seconds=15):
        """Countdown before starting"""
        print(f"\nPreparing to start in {seconds} seconds...")
        for i in range(seconds, 0, -1):
            print(f"Starting in: {i} seconds", end='\r', flush=True)
            time.sleep(1)
        print("\nStarting NOW!")
        
    def start_streaming(self):
        """Start the EEG data streaming with video"""
        try:
            # Get video path
            video_path = self.get_video_path()
            if not video_path:
                return
            
            print(f"Connecting to OpenBCI board on {self.serial_port}...")
            self.board.prepare_session()
            
            print("Setting up CSV file...")
            self.setup_csv()
            
            # Countdown
            self.countdown(15) #### Time delay change garne yeha samaye
            
            # Start video and EEG simultaneously
            print("Starting video playback...")
            if not self.start_video_player(video_path):
                print("Failed to start video. Continuing with EEG only.")
            
            print("Starting EEG data stream...")
            self.board.start_stream()
            self.is_streaming = True
            self.start_time = time.time()
            self.recording_start_time = time.time()  # Record the exact start time
            self.last_time = self.start_time
            
            # Start marker control thread
            if not self.markers_df.empty:
                self.marker_thread = threading.Thread(target=self.marker_control_thread, daemon=True)
                self.marker_thread.start()
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_sampling_rate, daemon=True)
            monitor_thread.start()
            
            print(f"Recording EEG data to: {self.csv_filename}")
            print("Video and EEG recording synchronized!")
            print("Press Ctrl+C to stop recording\n")
            
            # Main data collection loop
            while self.is_streaming:
                # Get data from board
                data = self.board.get_board_data()
                
                if data.shape[1] > 0:  # If we have new data
                    self.process_data(data)
                
                time.sleep(0.001)  # Small sleep to prevent excessive CPU usage
                
        except Exception as e:
            print(f"Error during streaming: {e}")
            self.stop_streaming()
            
    def process_data(self, data):
        """Process and save the EEG data with markers"""
        # Get channel information
        eeg_channels = BoardShim.get_eeg_channels(self.board_id)
        accel_channels = BoardShim.get_accel_channels(self.board_id)
        timestamp_channel = BoardShim.get_timestamp_channel(self.board_id)
        
        # Process each sample
        for i in range(data.shape[1]):
            self.sample_count += 1
            
            # Prepare row data
            row = [self.sample_count]  # Sample Index
            
            # EEG channels (16 channels for Cyton+Daisy)
            for ch in range(16):
                if ch < len(eeg_channels):
                    row.append(data[eeg_channels[ch]][i])
                else:
                    row.append(0.0)  # Fill with zeros if channel doesn't exist
            
            # Accelerometer channels
            for ch in accel_channels:
                row.append(data[ch][i])
            
            # Fill remaining 'Other' columns with zeros
            for _ in range(10):
                row.append(0.0)
            
            # Timestamp (board timestamp)
            board_timestamp = data[timestamp_channel][i]
            row.append(board_timestamp)
            
            # Marker Channel - use current marker
            row.append(self.current_marker)
            
            # Formatted timestamp
            formatted_time = datetime.fromtimestamp(board_timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            row.append(formatted_time)
            
            # Write to CSV
            self.csv_writer.writerow(row)
            
    def monitor_sampling_rate(self):
        """Monitor and display real-time sampling rate"""
        while self.is_streaming:
            time.sleep(1.0)  # Update every second
            
            current_time = time.time()
            current_sample_count = self.sample_count
            
            if self.last_time is not None:
                samples_in_interval = current_sample_count - self.last_sample_count
                time_interval = current_time - self.last_time
                
                if time_interval > 0:
                    current_rate = samples_in_interval / time_interval
                    self.sampling_rates.append(current_rate)
                    
                    # Keep only last 10 readings for average calculation
                    if len(self.sampling_rates) > 10:
                        self.sampling_rates.pop(0)
                    
                    avg_rate = np.mean(self.sampling_rates)
                    
                    # Display sampling rate info with recording time
                    elapsed_time = current_time - self.start_time
                    recording_time = current_time - self.recording_start_time if self.recording_start_time else 0
                    
                    print(f"\rSamples: {current_sample_count:6d} | "
                          f"Rate: {current_rate:6.1f} Hz | "
                          f"Avg Rate: {avg_rate:6.1f} Hz | "
                          f"Recording: {recording_time:6.1f}s", end='', flush=True)
            
            self.last_time = current_time
            self.last_sample_count = current_sample_count
            
    def stop_streaming(self):
        """Stop streaming and cleanup"""
        if self.is_streaming:
            self.is_streaming = False
            
            # Stop video player
            if self.video_process:
                try:
                    self.video_process.terminate()
                    self.video_process.wait(timeout=5)
                except:
                    try:
                        self.video_process.kill()
                    except:
                        pass
            
            # Stop board
            try:
                self.board.stop_stream()
                self.board.release_session()
            except:
                pass
                
            if self.csv_file:
                self.csv_file.close()
                
            print(f"\n\nStreaming stopped.")
            print(f"Total samples collected: {self.sample_count}")
            print(f"Data saved to: {self.csv_filename}")
            
            if self.sampling_rates:
                avg_rate = np.mean(self.sampling_rates)
                print(f"Average sampling rate: {avg_rate:.1f} Hz")

def main():
    """Main function"""
    print("OpenBCI Cyton+Daisy EEG Streamer with Video Synchronization")
    print("=" * 60)
    
    # Configuration milaune kura
    serial_port = '/dev/ttyUSB0'  
    csv_filename = f"Subject_XX_eeg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"  # Will auto-generate timestamp-based filename if None
    video_path = "Time_corrected_elbow_knee_mi_cue.mp4"  # VIDEO PATH in the same directory
    marker_csv = 'marker.csv'  # Marker file in same directory
    
    # Create and start streamer
    streamer = EEGStreamerWithVideo(
        serial_port=serial_port, 
        csv_filename=csv_filename,
        video_path=video_path,
        marker_csv=marker_csv
    )
    
    try:
        streamer.start_streaming()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received.")
    finally:
        streamer.stop_streaming()

if __name__ == "__main__":      
    main()