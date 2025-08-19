
#!/bin/bash
# CLI Usage Examples for Site A and Site B VxLAN Setup

echo "=== VxLAN Management CLI Examples ==="
echo "Site A and Site B Tunnel Configuration"
echo

# Site A CLI commands
echo "1. Site A Commands (run on Site A CPE):"
echo "   Create tunnel from Site A to Site B:"
echo "   python main.py cli tunnel add \\"
echo "     --vni 1001 \\"
echo "     --local-ip 203.0.113.10 \\"
echo "     --remote-ip 198.51.100.20 \\"
echo "     --interface vxlan1001 \\"
echo "     --bridge br-lan \\"
echo "     --label 'site-a-to-site-b'"
echo

# Site B CLI commands  
echo "2. Site B Commands (run on Site B CPE):"
echo "   Create tunnel from Site B to Site A:"
echo "   python main.py cli tunnel add \\"
echo "     --vni 1001 \\"
echo "     --local-ip 198.51.100.20 \\"
echo "     --remote-ip 203.0.113.10 \\"
echo "     --interface vxlan1001 \\"
echo "     --bridge br-lan \\"
echo "     --label 'site-b-to-site-a'"
echo

# Verification commands
echo "3. Verification Commands (run on both sites):"
echo "   List all tunnels:"
echo "   python main.py cli tunnel list"
echo
echo "   Show tunnel details:"
echo "   python main.py cli tunnel show vxlan1001"
echo
echo "   Get tunnel status:"
echo "   python main.py cli tunnel status vxlan1001"
echo

# Topology commands
echo "4. Topology Management:"
echo "   Create point-to-point topology:"
echo "   python main.py cli topology create point-to-point \\"
echo "     --config examples/site-a-site-b-config.yaml"
echo

# Cleanup commands
echo "5. Cleanup Commands:"
echo "   Delete tunnel (run on both sites):"
echo "   python main.py cli tunnel delete vxlan1001"
echo

echo "=== API Usage Examples ==="
echo

# API examples
echo "6. REST API Usage:"
echo "   Create tunnel via API (POST to /api/v1/tunnels):"
echo '   curl -X POST http://localhost:5000/api/v1/tunnels \'
echo '     -H "Content-Type: application/json" \'
echo '     -d "{'
echo '       \"vni\": 1001,'
echo '       \"local_ip\": \"203.0.113.10\",'
echo '       \"remote_ip\": \"198.51.100.20\",'
echo '       \"interface_name\": \"vxlan1001\",'
echo '       \"bridge_name\": \"br-lan\",'
echo '       \"label\": \"site-a-to-site-b\"'
echo '     }"'
echo
echo "   List tunnels via API:"
echo "   curl http://localhost:5000/api/v1/tunnels"
echo
echo "   Delete tunnel via API:"
echo "   curl -X DELETE http://localhost:5000/api/v1/tunnels/vxlan1001"
