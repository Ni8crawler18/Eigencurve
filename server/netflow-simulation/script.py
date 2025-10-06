#!/usr/bin/env python3
import sys
import asyncio
import json
import random
import socket
import struct
import time
import csv
import logging
import signal
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import configuration
from config import (
    NetFlowConfig, DEFAULT_CONFIG, SessionState,
    PROTOCOLS, NETFLOW_VERSION, TEMPLATE_FLOWSET_ID,FIELD_TYPES,ApplicationProfile,
)

# Flow key for tracking
FlowKey = namedtuple('FlowKey', [
    'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol'
])


@dataclass
class FlowRecord:
    """NetFlow v9 flow record with simplified fields."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    packets: int = 1
    bytes: int = 64
    first_switched: int = 0
    last_switched: int = 0
    flow_id: str = ""
    first_packet_time: float = 0.0

    def __post_init__(self):
        if self.first_switched == 0:
            self.first_switched = int(time.time() * 1000)
        if self.last_switched == 0:
            self.last_switched = self.first_switched
        if self.first_packet_time == 0.0:
            self.first_packet_time = time.time()

    def to_dict(self) -> dict:
        """Convert flow record to dictionary."""
        data = {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'packets': self.packets,
            'bytes': self.bytes,
            'first_switched': self.first_switched,
            'last_switched': self.last_switched,
            'flow_id': self.flow_id
        }

        # Calculate duration in milliseconds
        data['duration_ms'] = self.last_switched - self.first_switched

        return data


@dataclass
class NetworkSession:
    """Represents a realistic network session with multiple flows."""
    session_id: str
    src_ip: str
    dst_ip: str
    application: str
    profile: dict
    start_time: float
    state: SessionState = SessionState.SYN_SENT
    requests_sent: int = 0
    last_activity: float = 0
    total_requests: int = 0

    def __post_init__(self):
        if self.last_activity == 0:
            self.last_activity = self.start_time
        if self.total_requests == 0:
            min_req, max_req = self.profile['requests_per_session']
            self.total_requests = random.randint(min_req, max_req)


class FlowStreamer:
    """Async TCP server that broadcasts flow records as JSONL to connected clients."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9999):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.base_events.Server] = None
        self.clients: List[asyncio.StreamWriter] = []
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("FlowStreamer")
        self._serving_task: Optional[asyncio.Task] = None

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Accept client and keep the connection until it disconnects."""
        peer = writer.get_extra_info("peername")
        self.logger.info(f"Client connected: {peer}")
        async with self.lock:
            self.clients.append(writer)

        try:
            # Keep the connection open until the client closes.
            # We won't read from the client; just wait for EOF.
            await reader.read()  # returns b'' when client disconnects
        except Exception as e:
            self.logger.debug(f"Client {peer} read error: {e}")
        finally:
            async with self.lock:
                if writer in self.clients:
                    self.clients.remove(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            self.logger.info(f"Client disconnected: {peer}")

    async def start(self):
        """Start the TCP server."""
        if self.server:
            return
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        addr = ", ".join(str(sock.getsockname()) for sock in self.server.sockets or [])
        self.logger.info(f"FlowStreamer listening on {addr}")
        # Run server. Keep a background task so start() doesn't block (main loop will continue).
        self._serving_task = asyncio.create_task(self.server.serve_forever())

    async def stop(self):
        """Stop the server and close all client connections."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        if self._serving_task:
            self._serving_task.cancel()
            try:
                await self._serving_task
            except asyncio.CancelledError:
                pass
            self._serving_task = None

        async with self.lock:
            for w in list(self.clients):
                try:
                    w.close()
                    await w.wait_closed()
                except Exception:
                    pass
            self.clients.clear()
        self.logger.info("FlowStreamer stopped")

    async def broadcast(self, flows: List):
        """Broadcast a list of FlowRecord (or dicts) as JSONL to all connected clients."""
        if not flows:
            return

        # Convert flows to JSON lines
        lines = []
        for f in flows:
            if hasattr(f, "to_dict"):
                obj = f.to_dict()
            elif isinstance(f, dict):
                obj = f
            else:
                try:
                    obj = dict(f)
                except Exception:
                    obj = {"raw": str(f)}
            lines.append(json.dumps(obj))
        payload = ("\n".join(lines) + "\n").encode("utf-8")

        # Send to all clients concurrently, pruning dead ones
        async with self.lock:
            to_remove = []
            for w in self.clients:
                try:
                    w.write(payload)
                    await w.drain()
                except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
                    # mark for removal
                    to_remove.append(w)
                except Exception as e:
                    self.logger.debug(f"Broadcast write error: {e}")
                    to_remove.append(w)

            for w in to_remove:
                try:
                    if w in self.clients:
                        self.clients.remove(w)
                    w.close()
                    await w.wait_closed()
                except Exception:
                    pass


class FlowSampler:
    """Implements flow sampling based on configuration."""

    def __init__(self, config: NetFlowConfig):
        self.config = config
        self.sample_counter = 0
        self.total_flows = 0
        self.sampled_flows = 0

    def should_sample(self) -> bool:
        """Determine if the current flow should be sampled."""
        if not self.config.enable_sampling:
            return True

        self.total_flows += 1
        self.sample_counter += 1

        if self.sample_counter >= self.config.sampling_rate:
            self.sample_counter = 0
            self.sampled_flows += 1
            return True

        return False

    def get_stats(self) -> dict:
        """Get sampling statistics."""
        return {
            'total_flows': self.total_flows,
            'sampled_flows': self.sampled_flows,
            'sampling_rate': self.config.sampling_rate,
            'actual_ratio': self.sampled_flows / max(self.total_flows, 1)
        }


class FlowDataStorage:
    """Enhanced storage with flow sampling support."""

    def __init__(self, config: NetFlowConfig):
        self.config = config
        self.output_path = Path(config.output_dir)
        self.output_path.mkdir(exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if config.output_format == 'csv':
            self.flow_file = self.output_path / f"flows_{timestamp}.csv"
            self.csv_writer = None
            self.csv_file = None
        else:
            self.flow_file = self.output_path / f"flows_{timestamp}.jsonl"

        self.flows_written = 0

    def write_flows(self, flows: List[FlowRecord]):
        """Write flows to file."""
        if not flows:
            return

        if self.config.output_format == 'csv':
            self._write_csv(flows)
        else:
            self._write_jsonl(flows)

        self.flows_written += len(flows)

    def _write_jsonl(self, flows: List[FlowRecord]):
        """Write flows to JSONL file."""
        with open(self.flow_file, 'a') as f:
            for flow in flows:
                json.dump(flow.to_dict(), f)
                f.write('\n')

    def _write_csv(self, flows: List[FlowRecord]):
        """Write flows to CSV file."""
        if not flows:
            return

        # Initialize CSV writer if first time
        if not hasattr(self, 'csv_file') or self.csv_writer is None:
            self.csv_file = open(self.flow_file, 'w', newline='')
            fieldnames = list(flows[0].to_dict().keys())
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
            self.csv_writer.writeheader()

        # Write flow records
        for flow in flows:
            self.csv_writer.writerow(flow.to_dict())

        self.csv_file.flush()

    def close(self):
        """Close file handles."""
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()


class NetFlowV9Exporter:
    """NetFlow v9 packet exporter following RFC 3954."""

    def __init__(self, config: NetFlowConfig):
        self.config = config
        self.sequence = 0
        self.template_id = 256
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.template_sent = False
        self.packets_sent = 0
        self.logger = logging.getLogger('NetFlowExporter')

        # Initialize storage and sampler
        self.storage = FlowDataStorage(config) if config.save_flows else None
        self.sampler = FlowSampler(config)

        # optional streamer attribute — will be attached externally if streaming enabled
        self.streamer: Optional[FlowStreamer] = None

    def create_template_packet(self) -> bytes:
        """Create NetFlow v9 template packet."""
        # NetFlow v9 Header (20 bytes)
        version = NETFLOW_VERSION
        count = 1  # Number of flowsets
        sys_uptime = int(time.time() * 1000) & 0xFFFFFFFF
        unix_secs = int(time.time())
        sequence_number = self.sequence
        source_id = self.config.source_id

        header = struct.pack('!HHIIIII',
                             version, count, sys_uptime, unix_secs,
                             sequence_number, source_id, 0)

        # Template FlowSet Header (4 bytes)
        flowset_id = TEMPLATE_FLOWSET_ID
        flowset_length = 4 + 4 + (9 * 4)  # Header + template header + 9 fields

        flowset_header = struct.pack('!HH', flowset_id, flowset_length)

        # Template Header (4 bytes)
        template_header = struct.pack('!HH', self.template_id, 9)  # 9 fields

        # Template Fields (4 bytes each)
        fields = [
            (FIELD_TYPES['IPV4_SRC_ADDR'], 4),
            (FIELD_TYPES['IPV4_DST_ADDR'], 4),
            (FIELD_TYPES['L4_SRC_PORT'], 2),
            (FIELD_TYPES['L4_DST_PORT'], 2),
            (FIELD_TYPES['PROTOCOL'], 1),
            (FIELD_TYPES['IN_PKTS'], 4),
            (FIELD_TYPES['IN_BYTES'], 4),
            (FIELD_TYPES['FIRST_SWITCHED'], 4),
            (FIELD_TYPES['LAST_SWITCHED'], 4),
        ]

        field_data = b''
        for field_type, field_length in fields:
            field_data += struct.pack('!HH', field_type, field_length)

        return header + flowset_header + template_header + field_data

    def create_data_packet(self, flows: List[FlowRecord]) -> bytes:
        """Create NetFlow v9 data packet."""
        if not flows:
            return b''

        # NetFlow v9 Header
        version = NETFLOW_VERSION
        count = 1  # Number of flowsets
        sys_uptime = int(time.time() * 1000) & 0xFFFFFFFF
        unix_secs = int(time.time())
        sequence_number = self.sequence
        source_id = self.config.source_id

        header = struct.pack('!HHIIIII',
                             version, count, sys_uptime, unix_secs,
                             sequence_number, source_id, 0)

        # Data FlowSet Header
        flowset_id = self.template_id
        record_length = 4 + 4 + 2 + 2 + 1 + 4 + 4 + 4 + 4  # 29 bytes per record
        flowset_length = 4 + (len(flows) * record_length)

        flowset_header = struct.pack('!HH', flowset_id, flowset_length)

        # Flow Records
        records_data = b''
        for flow in flows:
            # Convert IP addresses to 32-bit integers
            src_ip_int = struct.unpack('!I', socket.inet_aton(flow.src_ip))[0]
            dst_ip_int = struct.unpack('!I', socket.inet_aton(flow.dst_ip))[0]

            # Convert timestamps to NetFlow format
            first_switched = flow.first_switched & 0xFFFFFFFF
            last_switched = flow.last_switched & 0xFFFFFFFF

            record = struct.pack('!IIHHBIIII',
                                 src_ip_int,           # IPV4_SRC_ADDR (4)
                                 dst_ip_int,           # IPV4_DST_ADDR (4)
                                 flow.src_port,        # L4_SRC_PORT (2)
                                 flow.dst_port,        # L4_DST_PORT (2)
                                 flow.protocol,        # PROTOCOL (1)
                                 flow.packets,         # IN_PKTS (4)
                                 flow.bytes,           # IN_BYTES (4)
                                 first_switched,       # FIRST_SWITCHED (4)
                                 last_switched)        # LAST_SWITCHED (4)
            records_data += record

        return header + flowset_header + records_data

    def send_template(self):
        """Send template packet to collector."""
        template_packet = self.create_template_packet()
        try:
            self.socket.sendto(template_packet, (self.config.collector_host, self.config.collector_port))
            self.template_sent = True
            self.logger.info(f"Sent template packet ({len(template_packet)} bytes)")
        except Exception as e:
            self.logger.error(f"Failed to send template: {e}")

    def send_flows(self, flows: List[FlowRecord]):
        """Send flow records to collector and save to file with sampling."""
        if not flows:
            return

        # Apply sampling
        sampled_flows = []
        for flow in flows:
            if self.sampler.should_sample():
                sampled_flows.append(flow)

        if not sampled_flows:
            return

        # Send template if needed
        if not self.template_sent or self.packets_sent % self.config.template_refresh == 0:
            self.send_template()

        # Send via UDP
        try:
            data_packet = self.create_data_packet(sampled_flows)
            self.socket.sendto(data_packet, (self.config.collector_host, self.config.collector_port))
            self.sequence += len(sampled_flows)
            self.packets_sent += 1
            self.logger.info(f"Sent {len(sampled_flows)} sampled flow records ({len(data_packet)} bytes)")
        except Exception as e:
            self.logger.error(f"Failed to send flows: {e}")

        # Save to file
        if self.storage:
            try:
                self.storage.write_flows(sampled_flows)
                self.logger.debug(f"Saved {len(sampled_flows)} flows to file")
            except Exception as e:
                self.logger.error(f"Failed to save flows: {e}")

        # Broadcast to connected TCP clients (JSONL) if streamer attached
        try:
            if getattr(self, "streamer", None):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop:
                    # Schedule broadcast in event loop
                    loop.create_task(self.streamer.broadcast(sampled_flows))
                else:
                    # Fallback: run broadcast synchronously (rare in async context)
                    asyncio.run(self.streamer.broadcast(sampled_flows))
        except Exception as e:
            self.logger.debug(f"Failed to broadcast flows to streamer: {e}")

    def close(self):
        """Close the UDP socket and storage."""
        try:
            self.socket.close()
        except Exception:
            pass

        if self.storage:
            self.storage.close()
            self.logger.info(f"Total flows written: {self.storage.flows_written}")
            print(f"Total flows written to {self.storage.flow_file}: {self.storage.flows_written}")

            # Print sampling statistics
            stats = self.sampler.get_stats()
            self.logger.info(f"Sampling stats: {stats}")
            print(f"Sampling: {stats['sampled_flows']}/{stats['total_flows']} flows "
                  f"(1:{self.config.sampling_rate} ratio)")


class FlowCache:
    """Enhanced flow cache with configurable timing."""

    def __init__(self, config: NetFlowConfig):
        self.config = config
        self.flows: Dict[FlowKey, FlowRecord] = {}
        self.flow_counter = 0

    def add_packet(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int,
                   protocol: int, packet_size: int, session_id: str = ""):
        """Add a packet to the flow cache."""
        key = FlowKey(src_ip, dst_ip, src_port, dst_port, protocol)
        current_time_ms = int(time.time() * 1000)

        if key in self.flows:
            # Update existing flow
            flow = self.flows[key]
            flow.packets += 1
            flow.bytes += packet_size

            # Add realistic delay between packets
            delay_ms = random.randint(self.config.min_packet_delay, self.config.max_packet_delay)
            new_last_switched = max(flow.last_switched + delay_ms, current_time_ms)
            flow.last_switched = new_last_switched
        else:
            # Create new flow with unique flow_id
            self.flow_counter += 1
            flow_id = f"flow_{self.flow_counter}_{int(time.time())}"

            flow = FlowRecord(
                src_ip, dst_ip, src_port, dst_port, protocol,
                1, packet_size, flow_id=flow_id
            )
            flow.first_switched = current_time_ms
            # Ensure new flows have initial duration
            initial_duration = random.randint(self.config.min_flow_duration,
                                              self.config.max_single_packet_duration)
            flow.last_switched = current_time_ms + initial_duration
            flow.first_packet_time = time.time()
            self.flows[key] = flow

    def get_expired_flows(self) -> List[FlowRecord]:
        """Get flows that have exceeded timeout limits."""
        now = int(time.time() * 1000)
        expired = []

        for key, flow in list(self.flows.items()):
            # Check for timeouts
            inactive_time = (now - flow.last_switched) / 1000
            active_time = (now - flow.first_switched) / 1000

            if inactive_time >= self.config.inactive_timeout or active_time >= self.config.active_timeout:
                # Ensure flow has realistic duration before expiring
                if flow.last_switched <= flow.first_switched:
                    # Force minimum duration if timestamps are equal
                    if flow.packets == 1:
                        # Single packet flows: configurable duration
                        duration = random.randint(self.config.min_flow_duration,
                                                  self.config.max_single_packet_duration)
                        flow.last_switched = flow.first_switched + duration
                    else:
                        # Multi-packet flows: duration based on packet count
                        min_duration, max_duration = self.config.duration_per_packet
                        duration_per_packet = random.randint(min_duration, max_duration)
                        total_duration = max(self.config.min_flow_duration,
                                             (flow.packets - 1) * duration_per_packet)
                        flow.last_switched = flow.first_switched + total_duration

                # Final check to ensure duration is never zero
                if flow.last_switched <= flow.first_switched:
                    flow.last_switched = flow.first_switched + self.config.min_flow_duration

                expired.append(flow)
                del self.flows[key]

        return expired

    def get_all_flows(self) -> List[FlowRecord]:
        """Get all flows and clear cache."""
        flows = list(self.flows.values())

        # Ensure all flows have proper duration before returning
        for flow in flows:
            if flow.last_switched <= flow.first_switched:
                if flow.packets == 1:
                    duration = random.randint(self.config.min_flow_duration,
                                              self.config.max_single_packet_duration)
                else:
                    min_dur, max_dur = self.config.duration_per_packet
                    duration = (flow.packets - 1) * random.randint(min_dur, max_dur)
                flow.last_switched = flow.first_switched + max(duration, self.config.min_flow_duration)

        self.flows.clear()
        return flows


class RealisticTrafficGenerator:
    """Generates realistic network traffic with proper session modeling."""

    def __init__(self, config: NetFlowConfig):
        self.config = config
        self.sessions: Dict[str, NetworkSession] = {}
        self.session_counter = 0

        # Get network topology from config
        self.internal_nets = config.get_internal_networks()
        self.external_nets = config.get_external_networks()

        # Get application profiles and weights from config
        self.app_profiles = config.get_application_profiles()
        self.app_weights = config.application_weights

    def random_ip_from_network(self, networks) -> str:
        """Get random IP from network list."""
        network = random.choice(networks)
        host_count = network.num_addresses - 2
        if host_count <= 0:
            return str(network.network_address)

        offset = random.randint(1, min(host_count, 254))
        return str(network.network_address + offset)

    def create_session(self) -> NetworkSession:
        """Create a new realistic network session."""
        self.session_counter += 1
        session_id = f"session_{self.session_counter}_{int(time.time())}"

        # Choose application type based on configured weights
        app_name = random.choices(
            list(self.app_weights.keys()),
            weights=list(self.app_weights.values())
        )[0]
        profile = self.app_profiles[app_name]

        # Choose source and destination
        src_ip = self.random_ip_from_network(self.internal_nets)

        # 70% external traffic, 30% internal
        if random.random() < 0.7:
            dst_ip = self.random_ip_from_network(self.external_nets)
        else:
            dst_ip = self.random_ip_from_network(self.internal_nets)

        session = NetworkSession(
            session_id=session_id,
            src_ip=src_ip,
            dst_ip=dst_ip,
            application=app_name,
            profile=profile,
            start_time=time.time()
        )

        self.sessions[session_id] = session
        return session

    def generate_session_packets(self, session: NetworkSession) -> List[Tuple]:
        """Generate realistic packets for a session."""
        packets = []
        now = time.time()

        # Check if session should be active
        session_duration = now - session.start_time
        max_duration = random.uniform(*session.profile['session_duration'])

        if session_duration > max_duration or session.requests_sent >= session.total_requests:
            # Session completed
            if session.session_id in self.sessions:
                del self.sessions[session.session_id]
            return packets

        # Generate packets for this session
        if session.state == SessionState.SYN_SENT:
            session.state = SessionState.ESTABLISHED

        # Check if it's time for next request
        time_since_last = now - session.last_activity
        min_delay, max_delay = session.profile['inter_request_delay']

        if time_since_last >= random.uniform(min_delay, max_delay):
            # Generate request/response pair
            dst_port = random.choice(session.profile['ports'])
            src_port = random.randint(1024, 65535)

            # Request packet (client to server)
            req_size = random.randint(*session.profile['request_size'])
            packets.append((
                session.src_ip, session.dst_ip, src_port, dst_port,
                PROTOCOLS['TCP'], req_size, session.session_id
            ))

            # Response packets (server to client) - if bidirectional
            if (self.config.enable_bidirectional and
                    random.random() < session.profile['bidirectional_ratio']):

                resp_size = random.randint(*session.profile['response_size'])

                # Split large responses into multiple packets
                mtu = 1500
                while resp_size > 0:
                    packet_size = min(resp_size, mtu)
                    packets.append((
                        session.dst_ip, session.src_ip, dst_port, src_port,
                        PROTOCOLS['TCP'], packet_size, session.session_id
                    ))
                    resp_size -= packet_size

            session.requests_sent += 1
            session.last_activity = now

        return packets

    def generate_packets(self) -> List[Tuple]:
        """Generate packets from all active sessions."""
        all_packets = []

        # Generate packets from existing sessions
        for session in list(self.sessions.values()):
            packets = self.generate_session_packets(session)
            all_packets.extend(packets)

        # Possibly create new session
        sessions_per_sec = self.config.sessions_per_minute / 60
        if random.random() < sessions_per_sec:
            new_session = self.create_session()
            packets = self.generate_session_packets(new_session)
            all_packets.extend(packets)

        # Add some background noise (ICMP, random UDP)
        if random.random() < 0.1:  # 10% chance of background traffic
            src_ip = self.random_ip_from_network(self.internal_nets)
            dst_ip = self.random_ip_from_network(self.external_nets)

            if random.random() < 0.5:
                # ICMP ping
                all_packets.append((
                    src_ip, dst_ip, 0, 0, PROTOCOLS['ICMP'], 64, "background"
                ))
            else:
                # Random UDP
                src_port = random.randint(1024, 65535)
                dst_port = random.randint(1024, 65535)
                all_packets.append((
                    src_ip, dst_ip, src_port, dst_port, PROTOCOLS['UDP'],
                    random.randint(64, 512), "background"
                ))

        return all_packets


def setup_logging(config: NetFlowConfig):
    """Setup logging based on configuration."""
    output_path = Path(config.output_dir)
    output_path.mkdir(exist_ok=True)

    # Convert log level string to logging level
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    level = log_levels.get(config.log_level, logging.INFO)

    # Setup handlers
    handlers = []
    if getattr(config, "file_logging", False):
        handlers.append(logging.FileHandler(output_path / config.log_file))
    if getattr(config, "console_logging", True):
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


async def main(config: NetFlowConfig):
    """Main simulation loop with realistic traffic generation."""

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger('NetFlowSimulator')

    # Create shutdown event
    shutdown_event = asyncio.Event()

    def signal_handler():
        logger.info("Received shutdown signal")
        shutdown_event.set()

    # Setup signal handlers for graceful shutdown
    try:
        loop = asyncio.get_running_loop()
        if hasattr(signal, 'SIGINT'):
            loop.add_signal_handler(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        logger.info("Signal handlers not supported on this platform")

    exporter = NetFlowV9Exporter(config)
    flow_cache = FlowCache(config)
    traffic_gen = RealisticTrafficGenerator(config)

    # Optionally start streamer
    streamer = None
    stream_enabled = getattr(config, "stream_enabled", True)
    stream_host = getattr(config, "stream_host", "0.0.0.0")
    stream_port = getattr(config, "stream_port", 9999)
    if stream_enabled:
        try:
            streamer = FlowStreamer(host=stream_host, port=stream_port)
            # attach streamer to exporter so send_flows can use it
            exporter.streamer = streamer
            await streamer.start()
            logger.info(f"Flow streamer started on {stream_host}:{stream_port}")
        except Exception as e:
            logger.error(f"Failed to start flow streamer: {e}")
            streamer = None

    logger.info("Starting Realistic NetFlow v9 simulator")
    logger.info(f"Collector: {config.collector_host}:{config.collector_port}")
    logger.info(f"Sessions per minute: {config.sessions_per_minute}")
    logger.info(f"Bidirectional flows: {config.enable_bidirectional}")
    logger.info(f"Sampling rate: 1:{config.sampling_rate}")
    logger.info(f"Output: {config.output_dir} ({config.output_format})")

    print(f"Starting Realistic NetFlow v9 simulator")
    print(f"Collector: {config.collector_host}:{config.collector_port}")
    print(f"Sessions/min: {config.sessions_per_minute}")
    print(f"Sampling: 1:{config.sampling_rate}")
    print(f"Bidirectional: {config.enable_bidirectional}")
    print(f"Output: {config.output_dir} ({config.output_format})")
    if streamer:
        print(f"Streaming JSONL flows to tcp://{stream_host}:{stream_port}")
    print("Press Ctrl+C to stop...")

    flow_export_counter = 0
    start_time = time.time()
    total_packets_generated = 0

    try:
        while not shutdown_event.is_set():
            loop_start = time.time()

            # Generate realistic traffic packets
            packets = traffic_gen.generate_packets()
            total_packets_generated += len(packets)

            # Add packets to flow cache with small delays
            for packet in packets:
                src_ip, dst_ip, src_port, dst_port, protocol, packet_size, session_id = packet
                flow_cache.add_packet(
                    src_ip, dst_ip, src_port, dst_port, protocol,
                    packet_size, session_id
                )

                # Small delay between processing packets for realistic timing
                if len(packets) > 1:
                    await asyncio.sleep(0.001)  # 1ms delay between packets

            # Check for expired flows and export them
            expired_flows = flow_cache.get_expired_flows()
            if expired_flows:
                exporter.send_flows(expired_flows)
                flow_export_counter += len(expired_flows)

            # Periodic status update
            elapsed = time.time() - start_time
            if elapsed > 0 and int(elapsed) % 30 == 0 and elapsed < 31:  # Every 30 seconds
                active_sessions = len(traffic_gen.sessions)
                packets_per_sec = total_packets_generated / elapsed
                flows_per_sec = flow_export_counter / elapsed
                sampling_stats = exporter.sampler.get_stats()

                logger.info(f"Status: {active_sessions} active sessions, "
                            f"{packets_per_sec:.1f} pkt/s, {flows_per_sec:.1f} flows/s, "
                            f"sampling: {sampling_stats['actual_ratio']:.3f}")
                print(f"Active sessions: {active_sessions}, "
                      f"Packets/sec: {packets_per_sec:.1f}, "
                      f"Flows/sec: {flows_per_sec:.1f}, "
                      f"Sampled: {sampling_stats['sampled_flows']}/{sampling_stats['total_flows']}")

            # Sleep to maintain realistic timing (1 second intervals)
            loop_duration = time.time() - loop_start
            sleep_time = max(0, 1.0 - loop_duration)
            await asyncio.sleep(sleep_time)

    except asyncio.CancelledError:
        logger.info("Main loop cancelled")
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Export any remaining flows
        remaining_flows = flow_cache.get_all_flows()
        if remaining_flows:
            exporter.send_flows(remaining_flows)
            flow_export_counter += len(remaining_flows)

        # Final statistics
        elapsed = time.time() - start_time
        sampling_stats = exporter.sampler.get_stats()

        logger.info("Simulation stopped")
        logger.info(f"Runtime: {elapsed:.1f} seconds")
        logger.info(f"Total packets generated: {total_packets_generated}")
        logger.info(f"Total flows exported: {flow_export_counter}")
        logger.info(f"Sampling statistics: {sampling_stats}")
        if elapsed > 0:
            logger.info(f"Average packets per second: {total_packets_generated/elapsed:.1f}")
            logger.info(f"Average flows per second: {flow_export_counter/elapsed:.1f}")

        print(f"\nSimulation Statistics:")
        print(f"Runtime: {elapsed:.1f} seconds")
        print(f"Total packets: {total_packets_generated}")
        print(f"Total flows: {flow_export_counter}")
        print(f"Sampling: {sampling_stats['sampled_flows']}/{sampling_stats['total_flows']} "
              f"(1:{config.sampling_rate} ratio, actual: {sampling_stats['actual_ratio']:.3f})")
        if elapsed > 0:
            print(f"Avg packets/sec: {total_packets_generated/elapsed:.1f}")
            print(f"Avg flows/sec: {flow_export_counter/elapsed:.1f}")

        # Clean up streamer first (if running)
        if streamer:
            try:
                await streamer.stop()
            except Exception as e:
                logger.debug(f"Error stopping streamer: {e}")

        # Clean up exporter and storage
        try:
            exporter.close()
        except Exception as e:
            logger.debug(f"Error closing exporter: {e}")


def parse_args() -> NetFlowConfig:
    """Parse command line arguments and return config."""
    import sys

    config = DEFAULT_CONFIG

    # default streaming options
    setattr(config, "stream_enabled", True)
    setattr(config, "stream_host", "0.0.0.0")
    setattr(config, "stream_port", 9999)
    setattr(config, "listen", False)  # default: don't run simple listener

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ['--help', '-h']:
            print_usage()
            sys.exit(0)
        elif arg == '--config' and i + 1 < len(args):
            # Load config from file
            config = NetFlowConfig.load_from_file(args[i + 1])
            i += 1
        elif arg == '--collector-host' and i + 1 < len(args):
            config.collector_host = args[i + 1]
            i += 1
        elif arg == '--collector-port' and i + 1 < len(args):
            config.collector_port = int(args[i + 1])
            i += 1
        elif arg == '--sessions-per-minute' and i + 1 < len(args):
            config.sessions_per_minute = int(args[i + 1])
            i += 1
        elif arg == '--sampling-rate' and i + 1 < len(args):
            config.sampling_rate = int(args[i + 1])
            i += 1
        elif arg == '--output-dir' and i + 1 < len(args):
            config.output_dir = args[i + 1]
            i += 1
        elif arg == '--output-format' and i + 1 < len(args):
            format_val = args[i + 1].lower()
            if format_val in ['jsonl', 'csv']:
                config.output_format = format_val
            else:
                print(f"Error: Invalid output format '{format_val}'. Use 'jsonl' or 'csv'.")
                sys.exit(1)
            i += 1
        elif arg == '--no-bidirectional':
            config.enable_bidirectional = False
        elif arg == '--no-sampling':
            config.enable_sampling = False
        elif arg == '--stream-host' and i + 1 < len(args):
            setattr(config, "stream_host", args[i + 1])
            i += 1
        elif arg == '--stream-port' and i + 1 < len(args):
            setattr(config, "stream_port", int(args[i + 1]))
            i += 1
        elif arg == '--no-stream':
            setattr(config, "stream_enabled", False)
        elif arg == '--listen':
            setattr(config, "listen", True)
        else:
            print(f"Error: Unknown argument '{arg}'")
            print_usage()
            sys.exit(1)

        i += 1

    return config


def print_usage():
    """Print usage information."""
    print("""
NetFlow v9 Realistic Traffic Simulator

Usage: python netflow_simulator.py [options]

Options:
  --config FILE            Load configuration from JSON file
  --collector-host HOST    NetFlow collector host (default: 127.0.0.1)
  --collector-port PORT    NetFlow collector port (default: 2055)
  --sessions-per-minute N  New sessions per minute (default: 30)
  --sampling-rate N        Sample 1 out of every N flows (default: 100)
  --output-dir DIR         Output directory (default: netflow_data)
  --output-format FORMAT   Output format: jsonl or csv (default: jsonl)
  --no-bidirectional       Disable bidirectional flows
  --no-sampling            Disable flow sampling
  --stream-host HOST       Host to bind TCP JSONL streamer (default: 0.0.0.0)
  --stream-port PORT       Port for TCP JSONL streamer (default: 9999)
  --no-stream              Disable streaming JSONL output
  --listen                 Run a very simple blocking listener (prints incoming JSONL) and exit
  --help                   Show this help message

Examples:
  python netflow_simulator.py
  python netflow_simulator.py --collector-host 192.168.1.100 --sessions-per-minute 60
  python netflow_simulator.py --sampling-rate 50 --output-format csv
  python netflow_simulator.py --stream-host 127.0.0.1 --stream-port 9999
  python netflow_simulator.py --listen --stream-host 127.0.0.1 --stream-port 9999
    """)


# Very small blocking listener (<=15 lines). Good for quick debugging.
def simple_listener(host: str = "127.0.0.1", port: int = 9999):
    """Simple blocking TCP JSONL listener that prints each incoming line."""
    import socket
    with socket.create_connection((host, port)) as s:
        with s.makefile('r', encoding='utf-8', errors='replace') as f:
            try:
                for line in f:
                    if not line:
                        break
                    print(line.rstrip())
            except KeyboardInterrupt:
                return


if __name__ == "__main__":
    try:
        # Parse command line arguments
        cfg = parse_args()

        # If user requested the tiny listener, run it and exit
        if getattr(cfg, "listen", False):
            host = getattr(cfg, "stream_host", "127.0.0.1")
            port = getattr(cfg, "stream_port", 9999)
            print(f"Running simple listener connecting to {host}:{port}. Ctrl+C to stop.")
            simple_listener(host, port)
            sys.exit(0)

        # Run the simulator with the parsed config
        asyncio.run(main(cfg))

    except KeyboardInterrupt:
        print("\nSimulator stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
