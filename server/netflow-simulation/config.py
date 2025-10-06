#!/usr/bin/env python3
"""
NetFlow v9 Simulator Configuration

This file contains all configuration settings for the NetFlow simulator including
sampling rates, network topology, application profiles, and output settings.
"""

import ipaddress
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class SessionState(Enum):
    """TCP session states for realistic modeling."""
    SYN_SENT = 1
    ESTABLISHED = 2
    FIN_WAIT = 3
    CLOSED = 4


class ApplicationProfile:
    """Defines realistic traffic patterns for different applications."""
    
    # Web browsing (HTTP/HTTPS)
    WEB = {
        'ports': [80, 443, 8080, 8443],
        'session_duration': (1, 30),      # 1-30 seconds
        'request_size': (100, 2000),      # Request sizes
        'response_size': (500, 50000),    # Response sizes  
        'requests_per_session': (1, 20),  # Pages/resources per session
        'inter_request_delay': (0.1, 3),  # Delay between requests
        'bidirectional_ratio': 0.8,       # 80% bidirectional traffic
    }
    
    # File transfer (FTP, SFTP)
    FILE_TRANSFER = {
        'ports': [21, 22, 990, 989],
        'session_duration': (10, 300),     # 10s - 5min
        'request_size': (100, 500),
        'response_size': (1000, 1000000),  # Large file downloads
        'requests_per_session': (1, 5),
        'inter_request_delay': (1, 10),
        'bidirectional_ratio': 0.9,
    }
    
    # Email (SMTP, IMAP, POP3)
    EMAIL = {
        'ports': [25, 110, 143, 993, 995],
        'session_duration': (5, 60),
        'request_size': (200, 1000),
        'response_size': (500, 10000),
        'requests_per_session': (1, 10),
        'inter_request_delay': (1, 5),
        'bidirectional_ratio': 0.7,
    }
    
    # DNS queries
    DNS = {
        'ports': [53],
        'session_duration': (0.1, 1),      # Very short
        'request_size': (50, 200),
        'response_size': (100, 500),
        'requests_per_session': (1, 3),
        'inter_request_delay': (0.01, 0.1),
        'bidirectional_ratio': 0.95,       # Almost always bidirectional
    }
    
    # Video streaming
    VIDEO = {
        'ports': [1935, 8080, 443],
        'session_duration': (60, 3600),    # 1min - 1hour
        'request_size': (100, 500),
        'response_size': (5000, 100000),   # Large video chunks
        'requests_per_session': (100, 3000),
        'inter_request_delay': (0.1, 2),
        'bidirectional_ratio': 0.9,
    }


@dataclass
class NetFlowConfig:
    """Configuration for realistic NetFlow v9 simulator."""
    
    # NetFlow Collector Settings
    collector_host: str = '127.0.0.1'
    collector_port: int = 2055
    source_id: int = 1
    
    # Sampling Configuration
    sampling_rate: int = 10          # Sample 1 out of every N flows (1:N ratio)
    enable_sampling: bool = True      # Enable/disable flow sampling
    
    # Traffic Generation Settings
    sessions_per_minute: int = 80     # New sessions started per minute
    packets_per_second: int = 200      # Target packets per second
    
    # Flow Timeout Settings
    active_timeout: int = 300         # Active flow timeout in seconds (5 minutes)
    inactive_timeout: int = 15        # Inactive flow timeout in seconds
    
    # NetFlow Export Settings
    template_refresh: int = 20        # Send template every N packets
    max_flows_per_packet: int = 50    # Maximum flows per NetFlow packet
    
    # Realism Settings
    enable_bidirectional: bool = True         # Enable bidirectional flows
    realistic_timing: bool = True             # Use realistic packet timing
    variable_packet_sizes: bool = True        # Use variable packet sizes
    enable_flow_fragmentation: bool = True    # Split large flows into multiple records
    
    # Timing Configuration (milliseconds)
    min_packet_delay: int = 1         # Minimum delay between packets (1ms)
    max_packet_delay: int = 100       # Maximum delay between packets (100ms)
    min_flow_duration: int = 1        # Minimum flow duration (1ms)
    max_single_packet_duration: int = 10      # Max duration for single packet flows (10ms)
    duration_per_packet: tuple = (10, 100)    # Duration range per packet (10-100ms)
    
    # Network Topology
    internal_networks: List[str] = None
    external_networks: List[str] = None
    
    # Application Traffic Distribution
    application_weights: Dict[str, float] = None
    
    # Storage Options
    output_dir: str = "netflow_data"
    log_file: str = "netflow_simulator.log"
    save_flows: bool = True
    output_format: str = "jsonl"      # "jsonl" or "csv"
    
    # Logging Configuration
    log_level: str = "INFO"           # DEBUG, INFO, WARNING, ERROR
    console_logging: bool = True      # Enable console output
    file_logging: bool = True         # Enable file logging
    
    # Performance Settings
    batch_size: int = 300             # Process flows in batches
    memory_limit_mb: int = 512        # Memory limit for flow cache
    
    def __post_init__(self):
        """Initialize default values for complex fields."""
        
        if self.internal_networks is None:
            self.internal_networks = [
                '192.168.1.0/24',     # Common home network
                '10.0.0.0/24',        # Corporate network
                '172.16.0.0/24',      # Private network
                '192.168.100.0/24',   # DMZ network
            ]
        
        if self.external_networks is None:
            self.external_networks = [
                '8.8.8.0/24',         # Google DNS
                '1.1.1.0/24',         # Cloudflare
                '151.101.0.0/24',     # Reddit/Fastly
                '104.244.42.0/24',    # Twitter
                '31.13.64.0/24',      # Facebook
                '13.107.42.0/24',     # Microsoft
                '172.217.0.0/24',     # Google services
                '52.84.0.0/24',       # AWS CloudFront
            ]
        
        if self.application_weights is None:
            self.application_weights = {
                'web': 0.45,          # 45% web traffic
                'video': 0.25,        # 25% video streaming  
                'dns': 0.15,          # 15% DNS queries
                'email': 0.10,        # 10% email traffic
                'file_transfer': 0.05  # 5% file transfers
            }
    
    def get_internal_networks(self) -> List[ipaddress.IPv4Network]:
        """Convert internal network strings to IPv4Network objects."""
        return [ipaddress.ip_network(net) for net in self.internal_networks]
    
    def get_external_networks(self) -> List[ipaddress.IPv4Network]:
        """Convert external network strings to IPv4Network objects."""
        return [ipaddress.ip_network(net) for net in self.external_networks]
    
    def get_application_profiles(self) -> Dict[str, dict]:
        """Get application profiles dictionary."""
        return {
            'web': ApplicationProfile.WEB,
            'file_transfer': ApplicationProfile.FILE_TRANSFER,
            'email': ApplicationProfile.EMAIL,
            'dns': ApplicationProfile.DNS,
            'video': ApplicationProfile.VIDEO,
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate sampling rate
        if self.sampling_rate < 1:
            errors.append("Sampling rate must be >= 1")
        
        # Validate timeouts
        if self.active_timeout <= 0:
            errors.append("Active timeout must be > 0")
        if self.inactive_timeout <= 0:
            errors.append("Inactive timeout must be > 0")
        
        # Validate application weights
        if self.application_weights:
            total_weight = sum(self.application_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"Application weights must sum to 1.0, got {total_weight}")
        
        # Validate timing settings
        if self.min_packet_delay >= self.max_packet_delay:
            errors.append("min_packet_delay must be < max_packet_delay")
        
        if self.duration_per_packet[0] >= self.duration_per_packet[1]:
            errors.append("duration_per_packet range is invalid")
        
        # Validate networks
        try:
            self.get_internal_networks()
            self.get_external_networks()
        except Exception as e:
            errors.append(f"Invalid network configuration: {e}")
        
        # Validate output format
        if self.output_format not in ['jsonl', 'csv']:
            errors.append("output_format must be 'jsonl' or 'csv'")
        
        # Validate log level
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append("log_level must be DEBUG, INFO, WARNING, or ERROR")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        config_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool, list, dict)):
                config_dict[key] = value
            else:
                config_dict[key] = str(value)
        return config_dict
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        import json
        from pathlib import Path
        
        config_dict = self.to_dict()
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'NetFlowConfig':
        """Load configuration from JSON file."""
        import json
        
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        return cls(**config_dict)


# Protocol numbers constants
PROTOCOLS = {'TCP': 6, 'UDP': 17, 'ICMP': 1}

# NetFlow v9 Constants
NETFLOW_VERSION = 9
TEMPLATE_FLOWSET_ID = 0
DATA_FLOWSET_ID = 256

# Field Type IDs (NetFlow v9 standard)
FIELD_TYPES = {
    'IPV4_SRC_ADDR': 8,      # Source IP address
    'IPV4_DST_ADDR': 12,     # Destination IP address  
    'L4_SRC_PORT': 7,        # Source port number
    'L4_DST_PORT': 11,       # Destination port number
    'PROTOCOL': 4,           # Layer 3 protocol type
    'IN_PKTS': 2,            # Packet count
    'IN_BYTES': 1,           # Byte count
    'FIRST_SWITCHED': 22,    # First packet timestamp
    'LAST_SWITCHED': 21,     # Last packet timestamp
}


# Default configuration instance
DEFAULT_CONFIG = NetFlowConfig()


def create_custom_config() -> NetFlowConfig:
    """Create a custom configuration with specific settings."""
    return NetFlowConfig(
        # High traffic simulation
        sessions_per_minute=120,
        packets_per_second=200,
        sampling_rate=50,  # 1:50 sampling ratio
        
        # Shorter timeouts for faster flow cycling
        active_timeout=60,
        inactive_timeout=5,
        
        # More aggressive timing
        min_packet_delay=1,
        max_packet_delay=50,
        duration_per_packet=(5, 50),
        
        # Custom application mix
        application_weights={
            'web': 0.5,
            'video': 0.3,
            'dns': 0.1,
            'email': 0.07,
            'file_transfer': 0.03
        }
    )


def create_minimal_config() -> NetFlowConfig:
    """Create a minimal configuration for testing."""
    return NetFlowConfig(
        sessions_per_minute=10,
        packets_per_second=20,
        sampling_rate=10,  # 1:10 sampling ratio
        save_flows=True,
        output_format='jsonl',
        log_level='DEBUG'
    )


if __name__ == "__main__":
    # Test configuration validation
    config = DEFAULT_CONFIG
    errors = config.validate()
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
        print(f"Sampling rate: 1:{config.sampling_rate}")
        print(f"Sessions per minute: {config.sessions_per_minute}")
        print(f"Internal networks: {len(config.internal_networks)}")
        print(f"External networks: {len(config.external_networks)}")
        print(f"Application weights: {config.application_weights}")