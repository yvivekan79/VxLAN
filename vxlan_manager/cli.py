"""
CLI interface for VxLAN tunnel management
"""

import click
import json
import yaml
from typing import Optional

from .core import VxLANManager, VxLANTunnel
from .topology import TopologyManager
from .logger import get_logger

logger = get_logger(__name__)

def print_json(data, indent=2):
    """Print data as formatted JSON"""
    click.echo(json.dumps(data, indent=indent, default=str))

def print_yaml(data):
    """Print data as formatted YAML"""
    click.echo(yaml.dump(data, default_flow_style=False, indent=2))

@click.group()
@click.option('--config', default='/etc/gind-vxlan/tunnels.yaml', 
              help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """VxLAN Tunnel Management CLI"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['manager'] = VxLANManager(config)

@cli.group()
@click.pass_context
def tunnel(ctx):
    """Tunnel management commands"""
    pass

@tunnel.command('add')
@click.option('--vni', required=True, type=int, help='VxLAN Network Identifier (4096-16777215)')
@click.option('--local-ip', required=True, help='Local IP address')
@click.option('--remote-ip', required=True, help='Remote IP address')
@click.option('--interface', default=None, help='Tunnel interface name (auto-generated if not specified)')
@click.option('--bridge', default='br-lan', help='Bridge name to attach tunnel')
@click.option('--physical-interface', default='eth0', help='Physical interface for tunnel')
@click.option('--mtu', default=1450, type=int, help='MTU size for tunnel')
@click.option('--port', default=4789, type=int, help='VxLAN port')
@click.option('--label', default='', help='Label for tunnel identification')
@click.option('--encryption', default='none', 
              type=click.Choice(['none', 'psk', 'ikev2']), help='Encryption type')
@click.option('--psk-key', default=None, help='Pre-shared key for PSK encryption')
@click.pass_context
def add_tunnel(ctx, vni, local_ip, remote_ip, interface, bridge, 
               physical_interface, mtu, port, label, encryption, psk_key):
    """Add a new VxLAN tunnel"""
    try:
        manager = ctx.obj['manager']
        
        # Generate interface name if not provided
        if not interface:
            interface = f"vxlan{vni}"
        
        # Create tunnel configuration
        tunnel = VxLANTunnel(
            vni=vni,
            local_ip=local_ip,
            remote_ip=remote_ip,
            interface_name=interface,
            bridge_name=bridge,
            physical_interface=physical_interface,
            mtu=mtu,
            port=port,
            label=label,
            encryption=encryption,
            psk_key=psk_key
        )
        
        tunnel_id = manager.create_tunnel(tunnel)
        click.echo(f"✓ Tunnel {tunnel_id} created successfully")
        
        # Display tunnel information
        tunnel_info = manager.get_tunnel(tunnel_id)
        if tunnel_info:
            click.echo("\nTunnel Configuration:")
            print_yaml({tunnel_id: manager.list_tunnels()[tunnel_id]})
            
    except Exception as e:
        click.echo(f"✗ Failed to create tunnel: {e}", err=True)
        raise click.Abort()

@tunnel.command('delete')
@click.option('--tunnel-id', required=True, help='Tunnel ID to delete')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete_tunnel(ctx, tunnel_id, confirm):
    """Delete a VxLAN tunnel"""
    try:
        manager = ctx.obj['manager']
        
        # Check if tunnel exists
        if not manager.get_tunnel(tunnel_id):
            click.echo(f"✗ Tunnel {tunnel_id} not found", err=True)
            raise click.Abort()
        
        # Confirmation prompt
        if not confirm:
            click.confirm(f"Are you sure you want to delete tunnel {tunnel_id}?", abort=True)
        
        manager.delete_tunnel(tunnel_id)
        click.echo(f"✓ Tunnel {tunnel_id} deleted successfully")
        
    except Exception as e:
        click.echo(f"✗ Failed to delete tunnel: {e}", err=True)
        raise click.Abort()

@tunnel.command('list')
@click.option('--format', default='yaml', type=click.Choice(['json', 'yaml', 'table']),
              help='Output format')
@click.option('--status', is_flag=True, help='Include runtime status')
@click.pass_context
def list_tunnels(ctx, format, status):
    """List all VxLAN tunnels"""
    try:
        manager = ctx.obj['manager']
        tunnels = manager.list_tunnels()
        
        if not tunnels:
            click.echo("No tunnels configured")
            return
        
        if format == 'json':
            print_json(tunnels)
        elif format == 'yaml':
            print_yaml(tunnels)
        elif format == 'table':
            # Print table format
            click.echo(f"{'Tunnel ID':<15} {'VNI':<8} {'Local IP':<15} {'Remote IP':<15} {'Status':<10}")
            click.echo("-" * 70)
            
            for tunnel_id, tunnel_data in tunnels.items():
                status_str = tunnel_data.get('status', {}).get('status', 'unknown') if status else 'n/a'
                click.echo(f"{tunnel_id:<15} {tunnel_data['vni']:<8} "
                          f"{tunnel_data['local_ip']:<15} {tunnel_data['remote_ip']:<15} "
                          f"{status_str:<10}")
                
    except Exception as e:
        click.echo(f"✗ Failed to list tunnels: {e}", err=True)
        raise click.Abort()

@tunnel.command('show')
@click.option('--tunnel-id', required=True, help='Tunnel ID to show')
@click.option('--format', default='yaml', type=click.Choice(['json', 'yaml']),
              help='Output format')
@click.pass_context
def show_tunnel(ctx, tunnel_id, format):
    """Show detailed tunnel information"""
    try:
        manager = ctx.obj['manager']
        tunnels = manager.list_tunnels()
        
        if tunnel_id not in tunnels:
            click.echo(f"✗ Tunnel {tunnel_id} not found", err=True)
            raise click.Abort()
        
        tunnel_data = {tunnel_id: tunnels[tunnel_id]}
        
        if format == 'json':
            print_json(tunnel_data)
        else:
            print_yaml(tunnel_data)
            
    except Exception as e:
        click.echo(f"✗ Failed to show tunnel: {e}", err=True)
        raise click.Abort()

@cli.group()
@click.pass_context
def topology(ctx):
    """Network topology management commands"""
    pass

@topology.command('create')
@click.option('--type', required=True, 
              type=click.Choice(['hub-spoke', 'full-mesh', 'partial-mesh']),
              help='Topology type')
@click.option('--config', required=True, help='Topology configuration file (YAML/JSON)')
@click.option('--dry-run', is_flag=True, help='Show what would be created without executing')
@click.pass_context
def create_topology(ctx, type, config, dry_run):
    """Create network topology"""
    try:
        manager = ctx.obj['manager']
        topo_manager = TopologyManager(manager)
        
        # Load topology configuration
        import yaml
        with open(config, 'r') as f:
            if config.endswith('.json'):
                topo_config = json.load(f)
            else:
                topo_config = yaml.safe_load(f)
        
        if dry_run:
            click.echo("Dry run - would create the following tunnels:")
            tunnels = topo_manager.plan_topology(type, topo_config)
            print_yaml(tunnels)
        else:
            result = topo_manager.create_topology(type, topo_config)
            click.echo(f"✓ Created {type} topology with {len(result)} tunnels")
            print_yaml(result)
            
    except Exception as e:
        click.echo(f"✗ Failed to create topology: {e}", err=True)
        raise click.Abort()

@cli.command('recover')
@click.pass_context
def recover_state(ctx):
    """Recover tunnel state from configuration"""
    try:
        manager = ctx.obj['manager']
        manager.recover_state()
        click.echo("✓ State recovery completed")
        
    except Exception as e:
        click.echo(f"✗ Failed to recover state: {e}", err=True)
        raise click.Abort()

@cli.command('status')
@click.pass_context
def system_status(ctx):
    """Show system status"""
    try:
        manager = ctx.obj['manager']
        tunnels = manager.list_tunnels()
        
        # System information
        status = {
            'total_tunnels': len(tunnels),
            'active_tunnels': sum(1 for t in tunnels.values() 
                                 if t.get('status', {}).get('status') == 'up'),
            'configuration_path': str(manager.config_path),
            'tunnels': tunnels
        }
        
        print_yaml(status)
        
    except Exception as e:
        click.echo(f"✗ Failed to get status: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
