"""File output functionality for newear."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO, List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class TranscriptEntry:
    """Represents a single transcript entry."""
    timestamp: float
    text: str
    confidence: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class FileWriter:
    """Handles file output for transcripts."""
    
    def __init__(self, output_file: Optional[Path] = None, show_timestamps: bool = True):
        self.output_file = output_file
        self.show_timestamps = show_timestamps
        self.file_handle: Optional[TextIO] = None
        self.entries: List[TranscriptEntry] = []
        
    def open_file(self) -> bool:
        """Open the output file for writing."""
        if not self.output_file:
            return False
            
        try:
            self.file_handle = open(self.output_file, 'w', encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error opening output file: {e}")
            return False
    
    def close_file(self):
        """Close the output file."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
    
    def write_entry(self, text: str, confidence: Optional[float] = None, 
                   start_time: Optional[float] = None, end_time: Optional[float] = None):
        """Write a transcript entry."""
        timestamp = time.time()
        entry = TranscriptEntry(
            timestamp=timestamp,
            text=text,
            confidence=confidence,
            start_time=start_time,
            end_time=end_time
        )
        
        self.entries.append(entry)
        
        # Format the entry for file output
        if self.show_timestamps:
            timestamp_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            formatted_entry = f"[{timestamp_str}] {text}\n"
        else:
            formatted_entry = f"{text}\n"
        
        # Write to file if available
        if self.file_handle:
            self.file_handle.write(formatted_entry)
            self.file_handle.flush()
        
        # Always print to console
        print(formatted_entry.rstrip())
    
    def write_continuous(self, text: str):
        """Write text to continuous file without line breaks."""
        if self.file_handle:
            # Write with space separator, no newline
            self.file_handle.write(f"{text} ")
            self.file_handle.flush()
    
    def write_json(self, output_file: Path):
        """Write transcript as JSON."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([entry.to_dict() for entry in self.entries], f, indent=2)
            print(f"JSON transcript saved to: {output_file}")
        except Exception as e:
            print(f"Error writing JSON: {e}")
    
    def write_srt(self, output_file: Path):
        """Write transcript as SRT subtitles."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, entry in enumerate(self.entries, 1):
                    if entry.start_time is not None and entry.end_time is not None:
                        start = self._format_srt_time(entry.start_time)
                        end = self._format_srt_time(entry.end_time)
                        f.write(f"{i}\n{start} --> {end}\n{entry.text}\n\n")
            print(f"SRT transcript saved to: {output_file}")
        except Exception as e:
            print(f"Error writing SRT: {e}")
    
    def write_vtt(self, output_file: Path):
        """Write transcript as WebVTT format."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                for entry in self.entries:
                    if entry.start_time is not None and entry.end_time is not None:
                        start = self._format_vtt_time(entry.start_time)
                        end = self._format_vtt_time(entry.end_time)
                        f.write(f"{start} --> {end}\n{entry.text}\n\n")
            print(f"VTT transcript saved to: {output_file}")
        except Exception as e:
            print(f"Error writing VTT: {e}")
    
    def write_csv(self, output_file: Path):
        """Write transcript as CSV."""
        try:
            import csv
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'text', 'confidence', 'start_time', 'end_time'])
                for entry in self.entries:
                    writer.writerow([
                        entry.timestamp,
                        entry.text,
                        entry.confidence,
                        entry.start_time,
                        entry.end_time
                    ])
            print(f"CSV transcript saved to: {output_file}")
        except Exception as e:
            print(f"Error writing CSV: {e}")
    
    def write_all_formats(self, base_path: Path, formats: list = None):
        """Write transcript in multiple formats."""
        if formats is None:
            formats = ['txt', 'json', 'srt', 'vtt', 'csv', 'continuous']
        
        for format_name in formats:
            if format_name == 'txt':
                continue  # Already written as main file
            elif format_name == 'continuous':
                continue  # Handled separately
            elif format_name == 'json':
                self.write_json(base_path.with_suffix('.json'))
            elif format_name == 'srt':
                self.write_srt(base_path.with_suffix('.srt'))
            elif format_name == 'vtt':
                self.write_vtt(base_path.with_suffix('.vtt'))
            elif format_name == 'csv':
                self.write_csv(base_path.with_suffix('.csv'))
            else:
                print(f"Warning: Unknown format '{format_name}' ignored")
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format time for VTT format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            return f"{minutes:02d}:{secs:06.3f}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the transcript."""
        if not self.entries:
            return {"total_entries": 0, "total_text_length": 0}
        
        total_text_length = sum(len(entry.text) for entry in self.entries)
        first_timestamp = self.entries[0].timestamp
        last_timestamp = self.entries[-1].timestamp
        duration = last_timestamp - first_timestamp
        
        return {
            "total_entries": len(self.entries),
            "total_text_length": total_text_length,
            "first_entry": datetime.fromtimestamp(first_timestamp).isoformat(),
            "last_entry": datetime.fromtimestamp(last_timestamp).isoformat(),
            "duration_seconds": duration,
            "avg_text_length": total_text_length / len(self.entries) if self.entries else 0
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.open_file()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_file()