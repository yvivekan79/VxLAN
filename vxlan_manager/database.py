
"""
Database models and schema for VxLAN management system
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Node(Base):
    """Node model for remote CPEs/servers"""
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True)
    node_id = Column(String(50), unique=True, nullable=False)
    hostname = Column(String(255), nullable=False)
    connection_type = Column(String(10), nullable=False)  # 'ssh' or 'http'
    port = Column(Integer, nullable=False)
    username = Column(String(50))
    ssh_key_path = Column(String(255))
    api_token = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tunnels_local = relationship("Tunnel", foreign_keys="Tunnel.local_node_id", back_populates="local_node")
    tunnels_remote = relationship("Tunnel", foreign_keys="Tunnel.remote_node_id", back_populates="remote_node")

class Tunnel(Base):
    """Tunnel model for VxLAN configurations"""
    __tablename__ = 'tunnels'
    
    id = Column(Integer, primary_key=True)
    tunnel_id = Column(String(50), unique=True, nullable=False)
    vni = Column(Integer, nullable=False)
    local_ip = Column(String(45), nullable=False)  # Support IPv6
    remote_ip = Column(String(45), nullable=False)
    interface_name = Column(String(50), nullable=False)
    bridge_name = Column(String(50), default='br-lan')
    physical_interface = Column(String(50), default='eth0')
    mtu = Column(Integer, default=1450)
    port = Column(Integer, default=4789)
    label = Column(String(255))
    encryption = Column(String(20), default='none')
    psk_key = Column(String(255))
    status = Column(String(20), default='created')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    local_node_id = Column(Integer, ForeignKey('nodes.id'))
    remote_node_id = Column(Integer, ForeignKey('nodes.id'))
    
    # Relationships
    local_node = relationship("Node", foreign_keys=[local_node_id], back_populates="tunnels_local")
    remote_node = relationship("Node", foreign_keys=[remote_node_id], back_populates="tunnels_remote")

class Topology(Base):
    """Topology model for network designs"""
    __tablename__ = 'topologies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    topology_type = Column(String(20), nullable=False)  # 'hub-spoke', 'full-mesh', 'partial-mesh'
    base_vni = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    topology_nodes = relationship("TopologyNode", back_populates="topology")

class TopologyNode(Base):
    """Association table for topology and nodes"""
    __tablename__ = 'topology_nodes'
    
    id = Column(Integer, primary_key=True)
    topology_id = Column(Integer, ForeignKey('topologies.id'))
    node_id = Column(Integer, ForeignKey('nodes.id'))
    role = Column(String(20))  # 'hub', 'spoke', 'member'
    
    # Relationships
    topology = relationship("Topology", back_populates="topology_nodes")
    node = relationship("Node")

# Database setup
def create_database(database_url="sqlite:///vxlan_tunnels.db"):
    """Create database and tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """Get database session"""
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
