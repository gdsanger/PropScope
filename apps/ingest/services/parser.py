"""
Parser for WSJT-X ALL.TXT log files.
"""

import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ParsedWsjtxLine:
    """Represents a parsed line from WSJT-X ALL.TXT"""
    timestamp: datetime
    frequency_mhz: float
    mode: str
    snr: int
    dt: float
    audio_frequency: int
    message: str
    raw_line: str
    is_cq: bool = False
    callsign: Optional[str] = None
    locator: Optional[str] = None
    cq_target: Optional[str] = None


class WsjtxLineParser:
    """
    Parser for WSJT-X ALL.TXT log file lines.

    Example line format:
    260419_185200     7.074 Rx FT8    -19  0.3 1133 CQ EX7CQ MN72
    |              |      |  |       |    |    |    |
    |              |      |  |       |    |    |    +-- Message
    |              |      |  |       |    |    +------- Audio frequency
    |              |      |  |       |    +------------ DT (time offset)
    |              |      |  |       +----------------- SNR
    |              |      |  +------------------------- Mode
    |              |      +---------------------------- Rx/Tx
    |              +----------------------------------- Frequency
    +-------------------------------------------------- Timestamp (YYMMDD_HHMMSS)
    """

    # CQ target prefixes that should be recognized
    CQ_TARGETS = {
        'DX', 'NA', 'SA', 'EU', 'AS', 'AF', 'OC',
        'RU', 'JA', 'CA'
    }

    # Pattern for standard ALL.TXT line
    LINE_PATTERN = re.compile(
        r'^(\d{6}_\d{6})\s+'  # timestamp
        r'([\d.]+)\s+'         # frequency
        r'(Rx|Tx)\s+'          # direction
        r'(\w+)\s+'            # mode (FT8, FT4, etc.)
        r'([+-]?\d+)\s+'       # SNR
        r'([+-]?[\d.]+)\s+'    # DT
        r'(\d+)\s+'            # audio frequency
        r'(.+)$'               # message
    )

    # Pattern for CQ messages
    CQ_PATTERN = re.compile(
        r'\bCQ\b\s+([A-Z0-9/]+)(?:\s+([A-Z0-9]{4,6}))?'
    )

    def parse_line(self, line: str) -> Optional[ParsedWsjtxLine]:
        """
        Parse a single line from ALL.TXT.

        Args:
            line: Raw line from the file

        Returns:
            ParsedWsjtxLine object or None if parsing fails
        """
        line = line.strip()
        if not line:
            return None

        match = self.LINE_PATTERN.match(line)
        if not match:
            return None

        try:
            timestamp_str = match.group(1)
            frequency_str = match.group(2)
            direction = match.group(3)
            mode = match.group(4)
            snr_str = match.group(5)
            dt_str = match.group(6)
            audio_freq_str = match.group(7)
            message = match.group(8).strip()

            # Parse timestamp: YYMMDD_HHMMSS
            timestamp = self._parse_timestamp(timestamp_str)
            if not timestamp:
                return None

            # Only process received messages (Rx)
            if direction != 'Rx':
                return None

            # Parse numeric values
            frequency_mhz = float(frequency_str)
            snr = int(snr_str)
            dt = float(dt_str)
            audio_frequency = int(audio_freq_str)

            # Check if this is a CQ message
            is_cq, callsign, locator, cq_target = self._parse_cq_message(message)

            return ParsedWsjtxLine(
                timestamp=timestamp,
                frequency_mhz=frequency_mhz,
                mode=mode,
                snr=snr,
                dt=dt,
                audio_frequency=audio_frequency,
                message=message,
                raw_line=line,
                is_cq=is_cq,
                callsign=callsign,
                locator=locator,
                cq_target=cq_target
            )

        except (ValueError, IndexError) as e:
            # Parsing failed, return None
            return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp from YYMMDD_HHMMSS format.

        Args:
            timestamp_str: Timestamp string (e.g., "260419_185200")

        Returns:
            datetime object in UTC, or None if parsing fails
        """
        try:
            # YYMMDD_HHMMSS
            dt = datetime.strptime(timestamp_str, "%y%m%d_%H%M%S")
            # Add UTC timezone
            dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None

    def _parse_cq_message(self, message: str) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Parse a message to check if it's a CQ and extract callsign, locator, and CQ target.

        Handles CQ messages with optional target prefixes:
        - CQ CALLSIGN LOCATOR
        - CQ TARGET CALLSIGN LOCATOR

        where TARGET can be: DX, NA, SA, EU, AS, AF, OC, RU, JA, CA

        Args:
            message: The decoded message

        Returns:
            Tuple of (is_cq, callsign, locator, cq_target)
        """
        if not message.startswith('CQ '):
            return (False, None, None, None)

        # Split message into tokens
        tokens = message.split()

        if len(tokens) < 2:
            return (False, None, None, None)

        # Start parsing after "CQ"
        index = 1
        cq_target = None

        # Check if next token is a CQ target prefix
        if len(tokens) > index and tokens[index].upper() in self.CQ_TARGETS:
            cq_target = tokens[index].upper()
            index += 1

        # Extract callsign (next token after CQ or CQ TARGET)
        callsign = tokens[index] if len(tokens) > index else None

        # Extract locator (token after callsign)
        locator = tokens[index + 1] if len(tokens) > index + 1 else None

        return (True, callsign, locator, cq_target)

    def is_cq_line(self, line: str) -> bool:
        """
        Quick check if a line contains a CQ call.

        Args:
            line: Raw line from file

        Returns:
            True if line contains "CQ"
        """
        return 'CQ' in line.upper()
