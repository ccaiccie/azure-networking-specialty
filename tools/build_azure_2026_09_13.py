from pathlib import Path
import json,re,html,os,textwrap
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'; IMAGES=DOCS/'images'
IMAGES.mkdir(parents=True,exist_ok=True)
STAMP='2026-09-13-08-00'
REPORT=f'Azure_Networking_Specialty_Daily_Study_Quiz_{STAMP}.html'
URL=f'https://ccaiccie.github.io/azure-networking-specialty/{REPORT}'
CERT='https://learn.microsoft.com/en-us/credentials/certifications/azure-network-engineer-associate/'
GUIDE='https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/az-700'

D_H='Hybrid connectivity and architecture'; D_C='Core networking infrastructure'; D_R='Routing and traffic management'; D_S='Security, monitoring, and private service access'

def lesson(title,domain,slug,primary,scenario,why,arch,impl,extra_title,extra,verify_cmd,verify_out,verify_text,trouble_cmd,trouble_out,trouble_text,diagram_nodes):
    return dict(title=title,domain=domain,slug=slug,primary=primary,scenario=scenario,why=why,arch=arch,impl=impl,extra_title=extra_title,extra=extra,verify_cmd=verify_cmd,verify_out=verify_out,verify_text=verify_text,trouble_cmd=trouble_cmd,trouble_out=trouble_out,trouble_text=trouble_text,diagram_nodes=diagram_nodes)

lessons=[
lesson(
'ExpressRoute Direct provisioning and VLAN encapsulation: QinQ versus Dot1Q',D_H,'expressroute-direct-qinq-dot1q',
'https://learn.microsoft.com/en-us/azure/expressroute/how-to-expressroute-direct-portal','https://learn.microsoft.com/en-us/azure/expressroute/expressroute-erdirect-about',
'''ExpressRoute Direct is the model to understand when an enterprise wants dedicated physical ports into the Microsoft global network and wants direct control over how ExpressRoute circuits are carved across those ports. The important early decision is not only bandwidth. It is the Layer-2 encapsulation model used for every circuit on the Direct resource. Microsoft supports QinQ and Dot1Q. With QinQ, Azure assigns an outer S-tag per circuit and the customer uses C-tags for the peerings inside that circuit. With Dot1Q, the customer manages VLAN identifiers directly across the Direct resource. That changes the operational burden on the switching team, the way circuit isolation is represented, and the kind of tagging mistake that can affect multiple peerings. Encapsulation is chosen when the Direct resource is created and cannot later be changed in place, so this belongs in the architecture decision record rather than a last-minute turn-up checklist.''',
'''A Direct deployment consists of two physical customer-facing ports at a supported peering location, normally connected to separate Microsoft edge devices. The customer router or switch must support the selected tagging model, multiple VLAN subinterfaces, and multiple BGP sessions. In QinQ mode Microsoft dynamically assigns the S-tag for each circuit; private and Microsoft peering use C-tags inside that circuit. C-tags need to be unique within the circuit, while the S-tag isolates different circuits. In Dot1Q mode the customer must maintain C-tag uniqueness across the entire Direct resource. The two physical links are redundant paths, not members of LACP or MLAG. Azure Resource Manager owns the Direct port, circuit, and peering objects; Ethernet tagging must work before BGP can establish; BGP must work before application prefixes can pass. A green provisioning state therefore cannot prove that both physical forwarding paths are usable.''',
'''Before ordering cross-connects, confirm that the peering location has the requested bandwidth and that the subscription is enabled for ExpressRoute Direct. The Direct resource and circuits created on it must be in the same subscription. Confirm optics, physical handoff, and router capabilities with the connectivity provider. Decide QinQ versus Dot1Q before deployment and assign ownership for the VLAN registry. Use the location query to confirm available capacity, then create the Direct resource with explicit encapsulation. Replace the placeholders with your resource group, Direct name, peering location, and Azure resource region. After Microsoft and the provider report the physical ports ready, create circuits against the Direct port resource and record circuit-to-VLAN mappings in the enterprise network source of truth. For QinQ, record the assigned S-tag and the C-tags for each peering. For Dot1Q, reject automation that tries to reuse a VLAN already allocated anywhere on the Direct resource.''',
'Circuit isolation, port redundancy, and acceptance testing',
'''A Direct port pair can host multiple circuits, so circuit lifecycle and physical-port lifecycle are deliberately separate. Creating a circuit does not mean the cross-connect is lit, and enabling a port does not mean the circuit is correctly tagged. Maintain a table mapping circuit name, owner, bandwidth, S-tag where applicable, private-peering C-tag, Microsoft-peering C-tag, router subinterface, and both physical interfaces. QinQ is useful when a separate service tag per circuit simplifies isolation; Dot1Q is simpler on equipment that does not support stacked tags but shifts uniqueness enforcement to the customer. Acceptance testing should isolate each port in turn. First prove optical state, Ethernet counters, expected tags, BGP on both paths, and actual application traffic. Then administratively remove path A and prove path B carries the required prefixes and load; repeat in the opposite direction. This exposes hidden dependence on one customer switch, one carrier device, one power feed, or one copied VLAN template.''',
'''az network express-route port location show -l "<peering-location>"
az network express-route port create -n <direct-port> -g <rg> --bandwidth 100 gbps --encapsulation QinQ --peering-location "<peering-location>" -l <azure-region>
az network express-route port show -g <rg> -n <direct-port> -o jsonc''',
'''{
  "encapsulation": "QinQ",
  "provisioningState": "Succeeded",
  "bandwidthInGbps": 100
}
CircuitState: Enabled
Path A BGP: Established
Path B BGP: Established''',
'''Successful verification is layered. The Direct resource must be provisioned with the intended encapsulation, the circuit must be enabled, and both independent BGP paths must be established. Compare Azure-assigned tags with the customer subinterfaces and capture counters while representative traffic is running. If only one BGP adjacency is established, the service is not fully redundant even though the ARM resource is healthy.''',
'''az network express-route port show -g <rg> -n <direct-port> -o jsonc
az network express-route peering list -g <rg> --circuit-name <circuit> -o table''',
'''provisioningState: Succeeded
encapsulation: QinQ
Path A: BGP Established
Path B: BGP Idle
Router: no ARP for Microsoft peer / unexpected VLAN tag''',
'''This output isolates the fault below routing policy. The Azure resource exists, but one Layer-2 path is not carrying the peering correctly. Compare S-tag and C-tag configuration, subinterface encapsulation, and the physical path before changing prefixes or route maps. If both paths fail after adding a Dot1Q circuit, check for a reused C-tag across the Direct resource.''',
['Customer Router A','QinQ / Dot1Q VLANs','ExpressRoute Direct Port Pair','Microsoft Edge / Circuits']),
lesson(
'ExpressRoute scalable gateway (ErGwScale): fixed capacity and autoscaling',D_H,'expressroute-ergwscale-autoscaling',
'https://learn.microsoft.com/en-us/azure/expressroute/scalable-gateway','https://learn.microsoft.com/en-us/azure/expressroute/expressroute-howto-scalable-portal',
'''ErGwScale changes how an ExpressRoute virtual network gateway is sized. Traditional gateway SKUs require selection of a fixed capacity tier and later SKU work when throughput or route scale changes. The scalable gateway uses scale units from 1 through 40 and can operate with fixed capacity or autoscaling. If minimum and maximum are equal, capacity is fixed. Autoscaling requires a minimum of at least two units and a maximum greater than the minimum. This is useful for variable aggregate traffic, changing circuit counts, and networks that want a larger growth ceiling without repeatedly redesigning the gateway. Autoscaling is not always the best choice: Microsoft recommends fixed scaling for workloads that include Private Link traffic. Treat the minimum as required always-on capacity and the maximum as an explicit performance and cost ceiling, not as arbitrary defaults.''',
'''The scalable gateway sits between ExpressRoute circuit connections and the virtual network routing domain. The Microsoft edge terminates circuit BGP sessions; the managed virtual network gateway forwards between those circuits and VNet resources. ErGwScale represents forwarding capability in scale units. Control-plane state includes gateway SKU, minimum and maximum scale units, circuit connections, and learned/advertised routes. The data plane is the actual packet flow through the gateway. Autoscaling changes serving capacity inside the managed gateway without changing customer BGP peerings. Fixed scaling pins the unit count. Published capacity guidance includes throughput and packet-rate behavior, so sizing should consider aggregate bits per second, packets per second, route scale, flow count, and failure conditions rather than circuit bandwidth alone. A 10-Gbps circuit does not automatically mean a single workload needs a 10-Gbps gateway at all times.''',
'''Use a Standard public IP resource and a supported ExpressRoute gateway deployment. Existing ErGw1Az, ErGw2Az, and ErGw3Az gateways have a documented direct upgrade path to ErGwScale; legacy Standard, HighPerformance, and UltraPerformance gateways use the migration process instead. For a new gateway, set the type to ExpressRoute, select ErGwScale, and specify minimum and maximum units. The example below creates fixed capacity at four units; use a minimum of at least two and a larger maximum when autoscaling is actually desired. Validate regional availability and current limitations before a production migration. Microsoft currently lists IPsec over ExpressRoute as unsupported with ErGwScale, so a design that depends on that overlay should not migrate merely for additional throughput. Capture current route counts, circuit connections, gateway metrics, and application baselines before changing the SKU or capacity.''',
'Capacity engineering and migration behavior',
'''Start with measured traffic instead of the largest circuit SKU. Multiple circuits can converge on one VNet gateway, and packet-per-second pressure can be more important than raw gigabits. Size the minimum so normal production and expected failure traffic fit without depending on an immediate scale event. Use the maximum as a deliberate ceiling. If the gateway spends most of its time near maximum, increase the baseline or redesign capacity rather than treating autoscale as a permanent saturation mechanism. During migration, verify every circuit connection separately and exercise a representative application from each on-premises path. Fail one redundant circuit path and confirm the gateway remains within capacity while routes reconverge. For legacy non-AZ gateways, use the documented migration tool rather than attempting an unsupported direct SKU update. For Private Link-heavy workloads, prefer a fixed unit count according to Microsoft guidance so capacity remains deterministic.''',
'''az network vnet-gateway create --name <ergw> --resource-group <rg> --vnet <vnet> --public-ip-addresses <gateway-pip> --gateway-type ExpressRoute --sku ErGwScale --min-scale-unit 4 --max-scale-unit 4
az network vnet-gateway update --name <ergw> --resource-group <rg> --min-scale-unit 2 --max-scale-unit 10
az network vnet-gateway show -g <rg> -n <ergw> --query "{sku:sku.name,min:minScaleUnit,max:maxScaleUnit,state:provisioningState}" -o json''',
'''{
  "sku": "ErGwScale",
  "min": 2,
  "max": 10,
  "state": "Succeeded"
}
ExpressRoute connections: Connected
Gateway metrics: below configured capacity ceiling''',
'''The SKU confirms that the scalable gateway family is active. Minimum and maximum reveal whether the design is fixed or autoscaling. Provisioning success is only the control-plane check; verify every ExpressRoute connection, learned prefixes, and real traffic after the change. The capacity range should match the approved design record and the observed gateway metrics should leave headroom for a circuit or path failure.''',
'''az network vnet-gateway show -g <rg> -n <ergw> -o jsonc
az network express-route list -g <rg> -o table''',
'''sku.name: ErGwScale
provisioningState: Succeeded
minScaleUnit: 2
maxScaleUnit: 2
Observed: sustained packet loss during peak
Private Link traffic is present''',
'''The gateway is technically healthy but fixed at two units. Increase fixed capacity if measurements show saturation, especially when Private Link traffic makes fixed scaling the documented preference. If autoscaling is appropriate for the workload, the maximum must be greater than the minimum. Do not troubleshoot BGP policy when route adjacencies are stable and the evidence points to forwarding capacity.''',
['On-premises / ER Circuits','ExpressRoute Connections','ErGwScale Gateway','Azure VNets']),
lesson(
'NVA forwarding in Azure: NIC IP forwarding, guest forwarding, and UDR insertion',D_H,'nva-ip-forwarding-udr-insertion',
'https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface','https://learn.microsoft.com/en-us/azure/virtual-network/tutorial-create-route-table',
'''A network virtual appliance can be a firewall, router, WAN optimizer, or custom Linux appliance, but Azure does not turn an ordinary VM into a transit router merely because it has multiple NICs. Forwarding requires cooperation between the Azure fabric and the guest. The NIC `enableIPForwarding` setting permits the interface to receive traffic not addressed to its own IP configuration and to transmit traffic whose source may differ from its configured IPs. The guest operating system or appliance must separately forward packets. Finally, user-defined routes must actually steer traffic to the appliance private IP. These are independent gates. A correct UDR still fails if NIC forwarding is disabled; Azure forwarding enabled does nothing if Linux `net.ipv4.ip_forward` is zero; a correctly forwarding appliance sees no traffic when the source subnet follows a direct system route. This three-layer model is the fastest way to troubleshoot NVA insertion.''',
'''Consider an application subnet, an NVA subnet, and a destination subnet. The application subnet has a route table containing the destination prefix with next-hop type `VirtualAppliance` and the NVA private IP. Azure sends the packet to the NVA even though the original IP destination is not the NVA itself. NIC IP forwarding allows that transit behavior. Inside the VM, the kernel or firewall process routes and inspects the packet before transmitting it toward the destination. A stateful design normally requires the return path to traverse the same appliance or a synchronized peer. The Azure control plane owns route tables, subnet associations, effective routes, and NIC forwarding state; the guest owns kernel forwarding, NAT, firewall policy, and session state. No platform mechanism automatically keeps those layers consistent, so an ARM deployment can be successful while transit traffic is still dropped inside the appliance.''',
'''Enable IP forwarding on every NVA NIC that participates in transit, then enable forwarding in the guest operating system. Microsoft’s tutorial uses Run Command to set Linux forwarding persistently. Create a route table, add the inspected destination prefix with next-hop type VirtualAppliance, and associate that route table to the source subnet. Replace the placeholders with your NVA NIC, VM, destination CIDR, NVA private IP, and subnet. If the appliance is stateful, design the return route explicitly rather than assuming Azure automatically reverses the UDR. Decide whether the appliance preserves source IP or performs SNAT and document that choice because it affects return routing, logs, and security policy. For multi-NIC appliances, verify forwarding on every participating NIC and follow the vendor’s supported interface and clustering model rather than applying a generic Linux pattern to a proprietary firewall image.''',
'Symmetry, NAT, and fault isolation',
'''A route table controls traffic leaving the subnet to which it is associated. Stateful inspection usually requires reverse traffic to return through the same appliance session. If the destination subnet follows a system route directly to the source, a SYN can arrive through the NVA while the SYN-ACK bypasses it. SNAT can force replies back to the appliance but changes source identity, so use it only when it is part of the intended design. Troubleshoot from outside inward: first prove the source NIC effective route resolves the destination to the expected VirtualAppliance address. Then show the NVA NIC forwarding flag. Next query guest forwarding or the vendor forwarding state. Finally inspect appliance policy, session tables, and packet captures on ingress and egress. That sequence prevents broad NSG edits when the packet never reached the firewall and prevents route changes when the packet is already visible on NVA ingress but not egress.''',
'''az network nic update --name <nva-nic> --resource-group <rg> --ip-forwarding true
az vm run-command invoke --resource-group <rg> --name <nva-vm> --command-id RunShellScript --scripts "sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf" "sudo sysctl -p"
az network route-table route create -g <rg> --route-table-name <rt> -n to-inspected --address-prefix <destination-cidr> --next-hop-type VirtualAppliance --next-hop-ip-address <nva-private-ip>
az network nic show-effective-route-table -g <rg> -n <source-nic> -o table''',
'''enableIpForwarding: true
User Active 10.60.0.0/16 VirtualAppliance 10.20.0.4
net.ipv4.ip_forward = 1
NVA session: established on forward and reverse path''',
'''These states prove three independent gates: Azure permits transit on the appliance NIC, the source workload actually sends the destination prefix to the NVA, and the guest is configured to forward IPv4. The NVA session or packet counters then prove that appliance policy allows the representative flow. Verify the reverse path separately for stateful designs.''',
'''az network nic show -g <rg> -n <nva-nic> --query enableIpForwarding
az network nic show-effective-route-table -g <rg> -n <source-nic> -o table
az vm run-command invoke -g <rg> -n <nva-vm> --command-id RunShellScript --scripts "sysctl net.ipv4.ip_forward"''',
'''enableIpForwarding: true
Effective route: 10.60.0.0/16 -> VirtualAppliance 10.20.0.4
net.ipv4.ip_forward = 0
NVA ingress: SYN seen
NVA egress: no packet''',
'''Azure routing and NIC state are correct, but the guest is not forwarding. Enable guest forwarding or correct the appliance forwarding configuration, then repeat the packet test. Do not change the UDR: it already delivered the packet to the appliance. If guest forwarding becomes 1 but traffic still stops, move to firewall policy, NAT, and return-path evidence.''',
['Application Subnet','UDR -> Virtual Appliance','NVA NIC + Guest Forwarding','Destination Subnet']),
lesson(
'Azure Public IP Prefix: stable contiguous Microsoft-owned address blocks',D_C,'public-ip-prefix-lifecycle',
'https://learn.microsoft.com/en-us/azure/virtual-network/ip-services/public-ip-address-prefix','https://learn.microsoft.com/en-us/azure/virtual-network/ip-services/create-public-ip-prefix-cli',
'''A Public IP Prefix reserves a contiguous block of Microsoft-owned public addresses for one Azure subscription and region. It is useful when external partners, SaaS platforms, allowlists, or enterprise firewalls need a predictable range instead of an expanding collection of unrelated public IP addresses. The prefix is an allocation resource, not a forwarding appliance. You create Standard static Public IP resources from the reserved block and attach those addresses to supported services. If an individual Public IP is deleted, the address returns to the reserved range while the prefix still exists. This is different from Bring Your Own IP: a normal Public IP Prefix is allocated from Microsoft address space, whereas a Custom IP Prefix represents externally owned address space onboarded to Azure. The lifecycle benefit is stability: the entire Azure-owned block stays reserved for the subscription until the prefix itself is deleted.''',
'''The prefix has a CIDR size, region, SKU, IP version, and optional zone model. Microsoft documents common IPv4 sizes /28, /29, /30, and /31, with corresponding IPv6 sizes. A /28 reserves sixteen addresses. Regional public-IP quota is consumed by the full prefix size even if only a few individual Public IP resources have been created. Data-plane packets still enter or leave through ordinary Public IP resources associated with load balancers, NAT Gateway, NICs, or other supported services. The prefix never becomes a next hop. Every Public IP created from the prefix must satisfy the documented region, subscription, SKU, and version constraints. That architecture separates address governance from forwarding configuration: a stable prefix can simplify external allowlists, but it cannot fix an unhealthy load-balancer rule, a missing NAT association, or an NSG deny.''',
'''Create the prefix with an intentional size and zone model. The example reserves a zone-redundant Standard IPv4 /28 in a region that supports availability zones. Then create a static Standard Public IP from the range and attach that Public IP through the owning service’s normal configuration. Keep the prefix and the child Public IP resources as separate infrastructure-as-code objects so one application can release an address without destroying the enterprise reservation. Azure normally chooses an available address from the prefix; if a specific address is required, use the documented IP-address parameter rather than assuming allocation is sequential. You cannot delete the prefix while Public IP resources still depend on it. Maintain IPAM metadata for address owner, attached service, environment, partner allowlists, and retirement status because Azure’s resource graph is not a replacement for business ownership records.''',
'Quota, zones, and lifecycle controls',
'''Prefix size should reflect a real allocation plan. Creating many /28 ranges can consume regional public-IP quota even when most child addresses are unused. When an application is decommissioned, detach and delete the child Public IP only after verifying no frontend, NAT Gateway, or NIC still references it; the address then becomes reusable inside the prefix. Deleting the prefix is a broader external change because the reserved range is released and cannot be assumed to return if a similarly named resource is recreated. Match zone behavior to the services that will consume addresses. A zone-redundant prefix can support resilient designs in appropriate regions; a zonal prefix intentionally ties allocation to one zone. Routing preference and StandardV2 options have separate constraints, so do not mix flags across SKU generations without checking current documentation. During incidents, if the Public IP still exists and belongs to the correct prefix, troubleshoot the attached forwarding service before blaming the allocation block.''',
'''az network public-ip prefix create --length 28 --name <prefix> --resource-group <rg> --sku standard --location <region> --version IPv4 --zone 1 2 3
az network public-ip create --name <pip> --resource-group <rg> --allocation-method Static --public-ip-prefix <prefix> --sku Standard --version IPv4
az network public-ip prefix show -g <rg> -n <prefix> -o jsonc
az network public-ip show -g <rg> -n <pip> --query "{ip:ipAddress,prefix:publicIPPrefix.id,sku:sku.name,state:provisioningState}" -o json''',
'''prefixLength: 28
provisioningState: Succeeded
{
  "ip": "203.0.113.10",
  "prefix": ".../publicIPPrefixes/<prefix>",
  "sku": "Standard",
  "state": "Succeeded"
}''',
'''The prefix is provisioned and the child Public IP explicitly references the prefix. Confirm that the assigned address falls inside the reserved CIDR and record it in the enterprise IPAM/allowlist system. A successful prefix does not prove the service using the address is reachable, so validate the associated frontend or NAT resource separately.''',
'''az network public-ip prefix delete -g <rg> -n <prefix>''',
'''PublicIpPrefixCannotBeDeleted:
Public IP address resources are still allocated from this prefix.''',
'''This failure is protective. Enumerate Public IP resources that reference the prefix, detach or delete them through their owning services, and then retry prefix deletion. Do not force a replacement prefix and assume Azure will return the same CIDR. If a partner allowlists the block, prefix deletion must be treated as an externally visible change.''',
['Reserved Public IP Prefix','Static Public IP Resources','Load Balancer / NAT / NIC','External Partners / Internet']),
lesson(
'Standard Load Balancer health probes: application-aware backend eligibility',D_C,'load-balancer-health-probes',
'https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-custom-probe-overview','https://learn.microsoft.com/en-us/azure/load-balancer/components',
'''Health probes tell Azure Load Balancer whether a backend instance should receive new flows. Probe design is therefore part of application availability, not a cosmetic monitoring setting. Standard Load Balancer supports TCP, HTTP, and HTTPS probes. TCP proves a listener accepts a connection. HTTP or HTTPS can test a purpose-built application path and use the response as a readiness signal. The probe should represent whether the instance can safely serve traffic, not merely whether the operating system is alive. Probe state also has nuanced flow behavior. When one backend becomes unhealthy, new flows stop going to it while established TCP connections can continue until the application ends them, an idle timeout occurs, or the VM shuts down. UDP behavior differs. When every Standard Load Balancer backend probe is down, existing TCP flows have documented behavior that differs from the retired Basic SKU. Maintenance and troubleshooting should be designed around those semantics.''',
'''The frontend receives client traffic and a load-balancing rule selects a healthy backend pool member. Each rule references a health probe. Azure sends the probe from the platform health-probe source, associated with 168.63.129.16 and the AzureLoadBalancer service tag. The backend must permit and answer the probe on the interface and port where it arrives. For HTTP/HTTPS, the health path should be cheap, deterministic, and return success only when the instance can actually serve the rule. A health path that performs an expensive database transaction can create its own outage; a path that always returns 200 even when dependencies are broken keeps failed servers in rotation. Multi-NIC appliances must return the probe through the correct interface. Microsoft warns against translating a probe through an NVA to some other backend because one downstream failure can falsely mark the appliance unhealthy and cause cascading removal.''',
'''Create the health endpoint in the application first, then configure the probe with protocol, port, path, interval, and threshold appropriate to the service. The example probes HTTP `/health` on port 8080 every five seconds with threshold two. Associate it with the relevant load-balancing rule and ensure the backend NSG allows the Azure Load Balancer health-probe source. A probe resource has value only when a rule actually uses it. During planned maintenance, intentionally make the health endpoint fail before stopping the VM, wait for the instance to be removed from new-flow distribution, and observe that remaining backends can carry the load. For HTTPS probes, use a server certificate chain compatible with documented probe behavior; do not design the health endpoint around mutual TLS because the platform probe does not present a client certificate. For an NVA, use a vendor-supported health signal that represents appliance forwarding readiness rather than a proxied application behind it.''',
'Maintenance, threshold behavior, and probe selection',
'''Probe protocol should reflect what “ready” means. TCP is appropriate when listener availability is enough. HTTP or HTTPS is better when the application can expose a safe readiness URL. The threshold controls consecutive success/failure handling, but explicit HTTP responses can have immediate health meaning while timeouts follow documented threshold rules. The health endpoint should not depend on a noncritical remote service whose brief failure would drain every backend simultaneously. During maintenance, remove one backend by health, verify new connections move to the surviving instances, and check whether those instances have sufficient CPU and connection capacity. Existing TCP sessions to the draining unhealthy backend can continue, so a client capture can show old sessions on one server and new sessions on another without indicating inconsistent probe state. If local `/health` returns 200 while Azure reports the instance unhealthy, investigate NSG, return path, interface binding, and platform probe reachability rather than changing the load-balancing hash.''',
'''az network lb probe create -g <rg> --lb-name <lb> --name app-health --protocol http --port 8080 --path /health --interval 5 --threshold 2
az network lb probe show -g <rg> --lb-name <lb> -n app-health -o jsonc''',
'''{
  "protocol": "Http",
  "port": 8080,
  "requestPath": "/health",
  "intervalInSeconds": 5,
  "numberOfProbes": 2,
  "provisioningState": "Succeeded"
}
Backend-01: Healthy
Backend-02: Healthy''',
'''The probe definition and backend health agree. A stronger acceptance test deliberately returns failure from backend-01 and confirms that new connections stop arriving there while backend-02 continues serving. That test validates the control’s effect, not just its existence.''',
'''curl -i http://127.0.0.1:8080/health
az network lb probe show -g <rg> --lb-name <lb> -n app-health -o jsonc''',
'''HTTP/1.1 503 Service Unavailable
Probe provisioningState: Succeeded
Backend-01: Unhealthy
Backend-02: Healthy
New connections: backend-02 only''',
'''The probe resource is healthy; the application readiness signal is not. Investigate the dependency that caused `/health` to return 503 instead of recreating the Load Balancer. If local curl returns 200 but Azure still reports Unhealthy, inspect the NSG, multi-NIC return path, interface binding, and whether the service listens on the expected probe port.''',
['Client / Frontend','Load Balancer Rule','Health Probe Decision','Backend Pool']),
lesson(
'Application Gateway connection draining: graceful backend removal during deployments',D_R,'application-gateway-connection-draining',
'https://learn.microsoft.com/en-us/azure/application-gateway/configuration-http-settings','https://learn.microsoft.com/en-us/azure/application-gateway/features',
'''Connection draining gives Application Gateway a controlled way to stop sending new requests to a backend instance that is being removed while allowing established connections to finish for a configured period. This is important during rolling deployments, scale-in events, and planned maintenance. Without draining, removing a backend can terminate long downloads, uploads, API calls, or WebSocket sessions and produce intermittent gateway errors that appear only during deployment windows. Draining is configured on the backend HTTP setting rather than the listener, so different applications can have different timeout requirements. Microsoft documents a user-defined timeout from 1 through 3,600 seconds; zero disables draining. The right value should exceed the longest legitimate transaction that must survive backend removal, but it should not be inflated without reason. Connection draining is a transition-state control, not a mechanism that migrates an active TCP session to another server.''',
'''Client traffic enters a listener, matches a routing rule, selects a backend pool, and uses a backend setting that defines protocol, port, timeout, cookie affinity, and draining behavior. When a backend is deregistered, Application Gateway stops selecting it for new work while preserving eligible existing connections until completion or the drain timeout. Health probes are a different state machine: a backend can be healthy but deliberately draining because deployment automation is removing it, and an unhealthy server can be excluded due to probe failure without a graceful maintenance workflow. The diagram therefore includes the temporary “draining” state between active membership and shutdown. Gateway-managed session affinity and long-lived connections require specific testing because sticky sessions and WebSockets can behave differently from stateless short requests. A configuration update can terminate connections after the drain timeout, so the timeout has to be designed with the real application transfer duration.''',
'''Update the backend HTTP setting used by the application and set an intentional draining timeout. The CLI uses the existing HTTP-settings resource. Five minutes is appropriate only when it exceeds the measured transaction duration for that service. Integrate the setting into deployment automation: first add the replacement backend and wait for healthy probe state; then remove the old backend from active membership; observe active connections trend down; only after completion or timeout should the old instance be stopped or patched. For large-file services, measure real transfer time rather than choosing a round number. Microsoft documents a limitation where configuration updates terminate ongoing connections after the configured drain timeout; intermittent deployment-time 502 symptoms can therefore be caused by a timeout shorter than client transfers. Keep health probes and connection draining conceptually separate: health says whether a server can take work, while draining controls graceful removal of a server that might still be healthy.''',
'Rolling deployment and session behavior',
'''A safe blue/green deployment creates a reversible intermediate state. Backend B enters the pool and becomes healthy. New traffic can use B. Backend A is removed and begins draining, so no new sessions should start there while existing sessions finish. If B becomes unhealthy during that interval, automation can restore A instead of rebuilding it. Cookie affinity should be tested because gateway-managed affinity can keep some traffic associated with a deregistering instance according to documented behavior. WebSocket clients also need retry logic because draining does not transfer a socket. Observe gateway access logs and backend connection counts during the rollout; the expected pattern is declining active sessions on A and new-session growth on B. If clients reset precisely at the configured timeout, that is strong evidence for drain-duration mismatch rather than DNS, WAF, or certificate failure. Choose the timeout from the longest accepted transaction and document why that number is safe.''',
'''az network application-gateway http-settings update -g <rg> --gateway-name <appgw> -n <backend-setting> --connection-draining-timeout 300
az network application-gateway http-settings show -g <rg> --gateway-name <appgw> -n <backend-setting> -o jsonc
az network application-gateway show-backend-health -g <rg> -n <appgw> -o jsonc''',
'''connectionDraining:
  enabled: true
  drainTimeoutInSec: 300
Backend-B: Healthy
Deployment observation:
  new requests -> Backend-B
  existing request on Backend-A -> completes before 300s''',
'''The backend setting proves that draining is enabled with the intended duration, and backend health proves the replacement server is ready. Validate with a controlled long-running request: start it on backend A, remove A, and confirm it completes while new requests are sent to B. This verifies real draining behavior rather than a configuration property alone.''',
'''az network application-gateway http-settings show -g <rg> --gateway-name <appgw> -n <backend-setting> -o jsonc
az network application-gateway show-backend-health -g <rg> -n <appgw> -o jsonc''',
'''connectionDraining.enabled: true
drainTimeoutInSec: 30
Backend-B: Healthy
Expected download duration: ~180s
Observed: connection reset at ~30s; intermittent 502 during deployment''',
'''The timeout is shorter than a legitimate transaction. Increase `--connection-draining-timeout` above the measured maximum transfer duration and repeat the rollout test. Do not change the listener certificate, DNS, or WAF policy when the reset consistently aligns with the draining timer and replacement backend is healthy.''',
['Client Sessions','Application Gateway','Backend A: Draining','Backend B: Healthy']),
lesson(
'Network Watcher VPN troubleshoot: diagnostic runs for gateways and connections',D_S,'network-watcher-vpn-troubleshoot',
'https://learn.microsoft.com/en-us/azure/network-watcher/vpn-troubleshoot-overview','https://learn.microsoft.com/en-us/azure/network-watcher/vpn-troubleshoot-cli',
'''VPN incidents often start with an imprecise symptom: a tunnel is down, intermittent, or carrying only one direction. Network Watcher VPN troubleshoot provides a platform diagnostic workflow for Azure VPN virtual network gateways and their connections. It differs from packet capture. You start a long-running troubleshooting request against a gateway or a specific VPN connection, provide a Storage account/container for diagnostic output, and Azure returns a health result plus action guidance when it detects an issue. Detailed logs are written to the specified storage path. The tool is valuable because it examines Azure platform state that cannot be inferred from one client ping. It does not replace on-premises firewall evidence, but it can narrow whether the Azure gateway or connection has a known problem before administrators make broad changes to IPsec policy, BGP, NSGs, or route tables.''',
'''Network Watcher must be enabled in the virtual network gateway region. The target can be the gateway resource or an individual VPN connection. The diagnostic service reads platform state, executes its checks, and writes artifacts to Azure Storage. A gateway-level run is appropriate when several connections fail or the shared gateway appears unhealthy. A connection-level run is more precise when one branch fails while other tunnels on the same gateway work. The result is control-plane and platform diagnostic evidence; it does not generate representative application traffic for every learned prefix. Therefore a Healthy result clears the VPN troubleshoot checks for the selected target but does not prove that an application route, on-premises ACL, or destination listener is correct. Store diagnostic output with the incident timeline so Azure and peer logs can be compared at the same timestamps.''',
'''Select or create a Storage account and container for the diagnostic output. Retrieve the Storage resource ID and start the troubleshooting run. The documented CLI supports `vnetGateway` and `vpnConnection` targets. Use the gateway target when symptoms affect the shared service and the connection target when one site is isolated. The request can take several minutes; preserve the final health status, action text, and log path. If the gateway has multiple connections, do not use a healthy unrelated site as evidence that the affected connection is healthy. After remediation, rerun the exact same target and retain the before/after outputs. This gives change control objective evidence that the condition moved from unhealthy to healthy. If Azure reports Healthy but one workload prefix remains unreachable, move next to BGP/static route evidence, effective routes, peer firewall policy, and application diagnostics rather than restarting the gateway repeatedly.''',
'Choosing the right diagnostic boundary',
'''The diagnostic target should match the failure boundary. Use the gateway when multiple VPN connections fail together, gateway provisioning is abnormal, or maintenance affected the shared instances. Use a connection when one branch or partner fails while other connections remain stable. That reduces noise in the generated logs and makes action guidance more relevant. Treat Storage logging as a dependency of the diagnostic workflow, not the VPN forwarding path: a permissions error writing the diagnostic container does not mean the tunnel itself is down. Pair the Network Watcher result with the peer’s IKE/IPsec logs. If both report negotiation failure at the same time, investigate crypto/authentication or peer reachability. If Network Watcher returns Healthy and IPsec counters increase but the application fails, the fault domain has moved above the tunnel into routes, NAT, security policy, or the workload. This disciplined handoff prevents one tool from being expected to diagnose every network layer.''',
'''storageId=$(az storage account show --name <storage-account> --resource-group <rg> --query id -o tsv)
az network watcher troubleshooting start --resource-group <rg> --resource <connection-name> --resource-type vpnConnection --storage-account "$storageId" --storage-path "https://<storage-account>.blob.core.windows.net/<container>"''',
'''status: Healthy
action: No action required
detailed logs: written to the specified Storage container
Azure connection: Connected
Peer IKE/IPsec SA: established''',
'''A Healthy result plus connected peer state clears the Azure VPN connection itself as the immediate fault. If users still fail, preserve the logs and move to route and security evidence for the exact application prefixes. The diagnostic should narrow the investigation rather than trigger an unnecessary tunnel restart.''',
'''az network watcher troubleshooting start --resource-group <rg> --resource <connection-name> --resource-type vpnConnection --storage-account "$storageId" --storage-path "https://<storage-account>.blob.core.windows.net/<container>"''',
'''status: UnHealthy
action: Review VPN connection configuration and diagnostic logs
Azure connection: NotConnected
Peer log: IKE negotiation failure''',
'''Use the detailed Network Watcher logs and the peer’s IKE log to identify the failing negotiation or reachability cause. Correct that specific cause and rerun the same connection-level diagnostic. Do not simultaneously edit routes, NSGs, and cryptographic proposals because multiple uncontrolled changes destroy the diagnostic value of the before/after evidence.''',
['On-premises VPN Device','Azure VPN Connection','Network Watcher Troubleshoot','Storage Diagnostic Logs']),
lesson(
'Azure Firewall threat intelligence: pre-rule malicious IP and domain filtering',D_S,'azure-firewall-threat-intelligence',
'https://learn.microsoft.com/en-us/azure/firewall-manager/threat-intelligence-settings','https://learn.microsoft.com/en-us/azure/firewall/firewall-azure-policy',
'''Azure Firewall threat intelligence uses Microsoft threat-intelligence feeds to identify high-confidence malicious IP addresses and domains and can alert or block traffic. The feature matters because its decision is made before normal NAT, network, and application rule processing. A connection can therefore be denied by threat intelligence even when an ordinary rule would otherwise allow it. Understanding that precedence prevents wasted troubleshooting in rule collections that never evaluate the packet. The feature can be configured off, alert-only, or alert-and-deny. Alert-only is useful during introduction because it reveals what enforcement would affect without immediately changing connectivity. Alert-and-deny turns reputation into a blocking control. An allowlist handles false positives or approved exceptions, but that bypass must be narrowly governed. Threat-intelligence allowlisting is not an ordinary allow rule and should never become a convenient way to bypass investigation of a potentially compromised endpoint.''',
'''Routing first sends the packet to Azure Firewall. Before NAT, network, and application rule collections evaluate it, threat intelligence compares source or destination indicators with Microsoft’s feed. In deny mode a high-confidence match is blocked and logged without proceeding to an ordinary allow rule. Firewall Policy hierarchy adds another governance layer: threat-intelligence settings can be inherited from parent to child, and child configurations must respect the parent’s enforcement posture. Allowlist entries can also have broad organizational effect when inherited. The architecture therefore places threat-intelligence evaluation ahead of the ordinary rule engine and shows logging as evidence of the early decision. This is an important troubleshooting model: when the log operation is `AzureFirewallThreatIntelLog`, changing a later application rule cannot override the result. The team must investigate the indicator, endpoint, and exception policy instead.''',
'''Set threat-intelligence mode explicitly after an alert-only observation period. For a firewall resource managed directly, Azure CLI exposes the threat-intelligence mode. If a verified false positive requires an exception, update the allowlist with the narrow FQDN or address/range and record an owner, business justification, and expiration. For enterprise Firewall Policy deployments, use Azure Policy to prevent project teams from creating policies that disable threat intelligence. Microsoft provides a controlled outbound test FQDN, `testmaliciousdomain.eastus.cloudapp.azure.com`, that can trigger a threat-intelligence alert for validation. Route test traffic through the firewall, first in alert mode and then in deny mode during an approved test window. Keep normal application/network rules in place: an allowlist only bypasses the reputation filter; it does not grant connectivity when ordinary policy still denies the destination.''',
'Testing, logs, and exception governance',
'''A successful rollout is observable. Send a controlled request from a test subnet to the Microsoft malicious-test FQDN and inspect firewall logs for the threat-intelligence operation, source, destination, action, and threat category. In alert mode the event should be visible without reputation enforcement; in deny mode the request should be blocked. If a legitimate production destination is flagged, investigate the source host and destination reputation before adding an exception. Prefer the narrowest FQDN or IP scope that solves the verified business case; never allowlist an entire CDN or cloud provider range simply to remove one alert. After adding an exception, prove that only the intended destination bypasses threat intelligence and that normal firewall rule evaluation still applies. Review parent-policy inheritance before troubleshooting a child policy because a stricter parent can explain behavior that is not visible in the child’s local settings.''',
'''az network firewall update -g <rg> -n <firewall> --threat-intel-mode Deny
az network firewall show -g <rg> -n <firewall> --query "{mode:threatIntelMode,state:provisioningState}" -o json''',
'''{
  "mode": "Deny",
  "state": "Succeeded"
}
ThreatIntel log:
destination: testmaliciousdomain.eastus.cloudapp.azure.com
Action: Deny
ThreatIntel: high-confidence indicator''',
'''The control plane shows enforcement enabled and the controlled test produces the expected threat-intelligence log on the actual data path. This is stronger evidence than the setting alone. Preserve the test timestamp so it can be correlated with the firewall log and confirm that unrelated permitted traffic is not affected.''',
'''az network firewall show -g <rg> -n <firewall> --query threatIntelMode -o tsv
# Query firewall logs for the reported destination and time.''',
'''Deny
ThreatIntel log:
source: 10.20.1.15
destination: business-partner.example
Action: Deny
Application rule would otherwise allow the FQDN''',
'''The application rule is not the failing layer because threat intelligence evaluates first. Investigate whether the destination is truly malicious and whether the source host is compromised. If a verified false positive requires business access, create a narrow threat-intelligence allowlist entry and retain the ordinary rule. Do not disable threat intelligence globally to solve one exception.''',
['Workload Traffic','Threat Intelligence Feed','Azure Firewall Pre-Rule Check','NAT / Network / App Rules']),
lesson(
'Azure Front Door WAF rate limiting: fixed-window protection at the edge',D_S,'front-door-waf-rate-limiting',
'https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-rate-limit','https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-rate-limit-configure',
'''Azure Front Door WAF rate limiting is a custom-rule control that limits how many matching requests a client socket IP can send during a fixed one- or five-minute interval. It is useful for login paths, promotion URLs, expensive APIs, and endpoints where syntactically valid traffic can still exhaust origin or application capacity. It is not a replacement for authentication, application quotas, or DDoS controls. The counting model matters: limits are evaluated by client socket IP across Front Door infrastructure. A client can occasionally reach different Front Door servers, so very low thresholds can permit a small amount of traffic beyond the nominal number before counters converge. Microsoft notes that larger windows and thresholds tend to produce more accurate enforcement. Once the threshold is breached, subsequent matching requests are blocked for the remainder of the fixed window; this is not a continuously sliding token bucket.''',
'''The client reaches the Front Door edge and the WAF custom rule evaluates its match conditions, such as Request URI or headers. A `RateLimitRule` counts matching requests for the client socket IP within the configured fixed interval. Requests below the threshold continue through later WAF and routing processing. Requests after the threshold are blocked at the edge until the window resets, so the origin never sees them. Every rate-limit rule needs at least one match condition. A narrow rule can protect `/promo` or `/api/login` without throttling static content; a broad condition can intentionally cover nearly all requests. Because clients behind enterprise NAT can share one socket IP, per-IP rate limits must account for legitimate aggregation. The data plane after an allowed decision is still normal Front Door routing; rate limiting does not create a separate origin connection or modify backend health.''',
'''Create or select a Front Door WAF policy, add a custom RateLimitRule, and add at least one match condition. The example protects requests whose URI contains `/promo` with a threshold of 1,000 per one-minute window. The rule is created with `--defer`, then the match condition completes the rule. Associate the WAF policy with the intended Front Door domain/security policy using the current Standard/Premium configuration model. Choose the threshold from observed legitimate per-client behavior and a documented safety margin. Do not use a tiny number merely because testing is easier. Explicitly consider corporate NAT, carrier-grade NAT, and shared proxies where hundreds of users can appear from one socket IP. Test with controlled traffic: remain below the threshold and confirm success, exceed it and confirm edge blocks, then wait for the fixed window boundary and prove automatic recovery. Compare WAF logs with origin metrics to verify the blocked requests never consumed origin capacity.''',
'Window design, NAT aggregation, and observability',
'''A one-minute window reacts quickly but can be more sensitive to bursty clients and distributed edge counters. A five-minute window can provide steadier protection for sustained abuse. When the threshold is very low, requests routed to another Front Door server can temporarily pass because counters may not yet reflect the first server’s observations. Treat the threshold as a security control rather than a billing-grade exact meter. NAT aggregation is equally important: an office, school, or mobile carrier can put many legitimate clients behind one public socket IP, so a limit designed for an individual residential user may throttle an entire organization. Narrow match conditions and application-specific thresholds reduce that risk. Operationally, correlate WAF action, client socket IP, rule name, RequestUri, response status, and origin request volume. If origin load continues rising while the rule appears enabled, first confirm the requests actually match the rule and that the policy is associated with the active domain.''',
'''az network front-door waf-policy create --name <waf-policy> --resource-group <rg> --sku Standard_AzureFrontDoor
az network front-door waf-policy rule create --name rateLimitPromo --policy-name <waf-policy> --resource-group <rg> --rule-type RateLimitRule --rate-limit-duration 1 --rate-limit-threshold 1000 --action Block --priority 1 --defer
az network front-door waf-policy rule match-condition add --match-variable RequestUri --operator Contains --values "/promo" --name rateLimitPromo --policy-name <waf-policy> --resource-group <rg>''',
'''ruleType: RateLimitRule
rateLimitDurationInMinutes: 1
rateLimitThreshold: 1000
action: Block
match: RequestUri Contains /promo
Observed after threshold: matching requests blocked at edge
Next fixed window: matching requests allowed again''',
'''Configuration and controlled traffic should agree. Verify the rule type, threshold, interval, action, and match condition, then exceed the threshold from one controlled source IP. Confirm WAF logs show the rule and origin metrics do not count blocked requests. Also test an unrelated path to prove the scope is narrow enough.''',
'''az network front-door waf-policy rule show -g <rg> --policy-name <waf-policy> -n rateLimitPromo -o jsonc
# Compare WAF logs with the exact RequestUri used in the load test.''',
'''rule: Enabled
condition: RequestUri Contains /promo
Test traffic: /api/login
WAF log: rateLimitPromo not matched
Origin request count continues rising''',
'''The rule is healthy but the test traffic is outside its scope. Change the match condition only if `/api/login` is the endpoint you intended to protect. Lowering the threshold or recreating the policy will not make a `/promo` rule match `/api/login`. After correcting scope, repeat the fixed-window load test and confirm origin protection.''',
['Client Socket IP','Front Door Edge','WAF RateLimitRule','Allowed -> Origin / Blocked at Edge']),
lesson(
'Azure Virtual Network Manager Network Verifier: static reachability analysis as code',D_S,'avnm-network-verifier-reachability',
'https://learn.microsoft.com/en-us/azure/virtual-network-manager/concept-virtual-network-verifier','https://learn.microsoft.com/en-us/azure/virtual-network-manager/how-to-verify-reachability-with-virtual-network-verifier',
'''Network Verifier in Azure Virtual Network Manager answers a different question from packet capture or Connection Troubleshoot: given the Azure network configuration and supported policies, should a precisely defined source be able to reach a precisely defined destination? It performs static reachability analysis across the Network Manager scope and produces a modeled path plus blocking reason when traffic is not reachable. This is useful before deployment for proving intended segmentation and after deployment for locating a policy or route that contradicts the design. Current documentation lists support for NSGs, application security groups, Virtual Network Manager security admin rules, connected groups, VNet peering, route tables, service endpoints and access controls, private endpoints, Virtual WAN, and static Layer-4 Azure Firewall behavior. It is not packet capture and does not prove that an application process is listening. Unsupported services or dynamic NVA behavior can make runtime traffic differ from the static model.''',
'''A verifier workspace is a child of an Azure Virtual Network Manager and contains reachability analysis intents and run results. An intent defines source resource, destination resource, IPs, ports, and protocol. An analysis run evaluates that intent against supported resources and policy inside the parent manager scope. Results show whether packets are expected to reach and list the path or blocking step. The workspace also creates a delegation boundary: a central network team can give a troubleshooting or application team access to one verifier workspace without giving that team ownership of the entire Network Manager. That enables repeatable controls such as “web subnet must reach SQL private endpoint TCP/1433” and “internet must never reach management subnet TCP/22.” Positive and negative intents can be rerun after policy changes, turning reachability into auditable design evidence instead of a one-time portal screenshot.''',
'''Use the `virtual-network-manager` Azure CLI extension. Create a verifier workspace under an existing Network Manager in a currently supported region. Then create a reachability intent with exact source and destination resource IDs and an `ip-traffic` object. Start an analysis run by passing the intent resource ID. Keep each intent narrow enough that its result has business meaning. One exact web-to-API TCP/443 intent is more useful than a wildcard covering every protocol. The CLI command surface is GA in the current extension, but the feature has region availability constraints; validate the Network Manager and workspace region before deployment. Integrate the run into change validation by saving the JSON result and comparing it after NSG, UDR, peering, Private Endpoint, Virtual WAN, or security-admin changes. If the model says Reachable but users still fail, transition to runtime diagnostics rather than forcing Network Verifier to answer application-layer questions it does not observe.''',
'Positive/negative intents and runtime boundaries',
'''Create paired intents. Positive intents describe flows that must work, such as an application subnet to a database endpoint on the required port. Negative intents represent isolation controls that must remain blocked. After a routing or security change, run both sets so a repair for one outage cannot silently broaden access somewhere else. A result that says `NoPacketsReached` can therefore be a success when the intent is a negative security assertion. The result path can identify an NSG, security admin rule, route, peering, or other supported control that blocks the modeled packet. It cannot prove guest firewall, process listener, certificate validation, or dynamic third-party appliance decisions. When static policy says the path is reachable but the service is down, use Connection Troubleshoot, packet capture, workload logs, or appliance telemetry. When static analysis identifies a specific deny step, fix that resource and rerun the identical intent before changing unrelated network layers.''',
'''az network manager verifier-workspace create --name <workspace> --network-manager-name <network-manager> --resource-group <rg> --description "Production reachability validation" --location <supported-region>
az network manager verifier-workspace reachability-analysis-intent create --name web-to-api-443 --workspace-name <workspace> --network-manager-name <network-manager> --resource-group <rg> --source-resource-id <source-vm-id> --destination-resource-id <dest-vm-id> --ip-traffic "{source-ips:['10.10.1.4'],destination-ips:['10.20.1.4'],source-ports:['1024-65535'],destination-ports:['443'],protocols:['TCP']}"
INTENT_ID=$(az network manager verifier-workspace reachability-analysis-intent show --name web-to-api-443 --workspace-name <workspace> --network-manager-name <network-manager> --resource-group <rg> --query id -o tsv)
az network manager verifier-workspace reachability-analysis-run create --name validation-001 --workspace-name <workspace> --network-manager-name <network-manager> --resource-group <rg> --intent-id "$INTENT_ID"''',
'''provisioningState: Succeeded
result.outcome: Reachable / AllPacketsReached
path: source VM -> route/peering -> destination subnet
blockingStep: none''',
'''The run itself completed and the modeled TCP/443 path is permitted by supported Azure policy. Preserve the JSON as design evidence. If the requirement is real service availability, follow with a runtime connection test because static reachability cannot prove that the destination process accepts TCP/443.''',
'''az network manager verifier-workspace reachability-analysis-run show --name validation-001 --workspace-name <workspace> --network-manager-name <network-manager> --resource-group <rg> -o jsonc''',
'''provisioningState: Succeeded
result.outcome: NoPacketsReached
blockingStep:
  resource: <nsg-or-security-admin-rule>
  action: Deny
  destinationPort: 443''',
'''The analysis service succeeded; the modeled packet did not. If this is a required positive flow, fix the specific rule identified at the blocking step and rerun the same intent. Do not widen unrelated routes or disable security globally. If the intent was deliberately negative, preserve this result as evidence that segmentation is working.''',
['Verifier Workspace','Reachability Intent','Static Policy Analysis','Reachable Path / Blocking Step']),
lesson(
'Azure Load Balancer administrative state: controlled backend maintenance overrides',D_R,'load-balancer-admin-state',
'https://learn.microsoft.com/en-us/azure/load-balancer/admin-state-overview','https://learn.microsoft.com/en-us/azure/load-balancer/manage-admin-state-how-to',
'''Administrative state gives Azure Load Balancer operators an explicit per-backend override of normal health-probe behavior. The values are Up, Down, and None. `None` means ordinary probe behavior decides eligibility. `Down` prevents new connections even if the probe says the instance is healthy, which is useful for maintenance, patching, and controlled tests. `Up` forces the backend to remain eligible even if the probe reports unhealthy, which can be useful in tightly controlled scenarios but is risky if used to mask a real application failure. Admin state is not simply another health status; it is an operator override. That distinction matters in troubleshooting because an instance can have a healthy application endpoint yet receive no new traffic when its admin state is Down, or it can receive traffic despite a failed probe when forced Up. The setting applies per backend pool instance and has documented protocol behavior for existing TCP and UDP flows.''',
'''The load-balancing rule still references its health probe, but admin state changes how the backend’s eligibility is interpreted. With None, probe state is authoritative. With Down, the load balancer stops new connections to that backend; established TCP connections can persist while existing UDP flows can move according to documented behavior. With Up, the load balancer ignores the failing probe for eligibility and treats the backend as available. The override is associated with a backend pool instance, not globally with the VM. A VM that participates in multiple backend pools can therefore have different admin state in each pool. A backend pool used by multiple load-balancing rules carries the override into those associated rules. Admin state only has effect when the load-balancing rule has a health probe. It is not supported for inbound NAT rules and has limitations with certain backend configuration models, so the maintenance design must match the documented pool type.''',
'''Use admin state as a planned operational action with a runbook, not a permanent workaround. Before patching a backend, set that pool instance Down, observe that new flows stop, and allow existing TCP sessions to drain according to application requirements. Then patch or restart the server. After local health is restored, set the state back to None so normal probe behavior resumes. Reserve Up for deliberate tests or special cases and set an expiration/removal action; leaving a broken server forced Up defeats the purpose of health probes. The portal, PowerShell, and Azure CLI can manage the setting. Because backend representations differ between NIC-based and IP-based pools, use the current documented command for the pool model deployed in your environment. Record the backend instance, previous state, new state, operator, and maintenance ticket. Health Probe Status metrics and Load Balancer Insights reflect admin-state changes, giving the operations team an external view of the override.''',
'Maintenance workflow and safety controls',
'''A good maintenance sequence separates traffic drain from server shutdown. Set one backend Down and prove new sessions move to healthy peers. Watch connection counts until the application’s acceptable drain point, then patch the server. Verify the service locally before returning the backend to `None`, which hands eligibility back to the health probe. Do not set the state to Up merely to make a dashboard green. If the health probe is failing for a real reason, forced Up can send new users to a broken instance. Admin state is especially useful for testing pool resilience because it creates an intentional backend exclusion without changing probe endpoint code or manipulating an NSG. Test one member at a time and confirm the remaining pool has enough capacity. For UDP-heavy services, account for the documented behavior that flows can move when a backend is forced Down; for long TCP sessions, allow time for existing connections to complete or use application-level draining as well.''',
'''# Inspect the current backend pool and admin-state capable entries.
az network lb address-pool show -g <rg> --lb-name <lb> -n <backend-pool> -o jsonc
# Apply Up/Down/None using the current Azure CLI backend-address command documented for your pool model.
# Then re-read the pool and Load Balancer Insights/health metrics.''',
'''backendAddress: 10.20.1.4
adminState: Down
probeSignal: Healthy
newConnectionsToBackend: 0
existingTcpConnections: draining/persisting
otherBackend: Healthy and receiving new flows''',
'''The key success condition is intentional disagreement: the probe may remain healthy while admin state Down removes the backend from new-flow eligibility. That proves the maintenance override, rather than a probe failure, is controlling distribution. Before returning service, restore the state to None and verify the health probe becomes authoritative again.''',
'''az network lb address-pool show -g <rg> --lb-name <lb> -n <backend-pool> -o jsonc
# Compare adminState with health-probe metrics and backend application health.''',
'''backendAddress: 10.20.1.4
adminState: Up
probeSignal: Unhealthy
new connections continue reaching backend
application /health: 503''',
'''A forced Up state is overriding a real health failure. Do not modify the probe to hide the symptom. Remove the override by returning admin state to None or deliberately set Down, then repair the application. Use Up only when the operational risk is explicitly accepted and the reason for ignoring probe state is documented.''',
['Load Balancer Rule','Health Probe Signal','Admin State Override','Backend Instance']),
lesson(
'Application Gateway custom error pages: controlled gateway-generated failure responses',D_R,'application-gateway-custom-error-pages',
'https://learn.microsoft.com/en-us/azure/application-gateway/custom-error','https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-components',
'''Application Gateway can return custom HTML for gateway-generated errors instead of the default pages. This matters for planned maintenance, user guidance, security branding, and incident communication. Supported gateway response codes include 400, 403, 405, 408, 500, 502, 503, and 504; 404 is not currently supported. The page is used only when Application Gateway itself generates the relevant error. If a backend application returns its own 502 or 503, the gateway passes that backend response rather than replacing it with the gateway custom page. This boundary is crucial during testing: a team can correctly configure a custom 502 page and still see the application’s unbranded 502 because the error originated behind the gateway. Custom pages can be configured globally or at listener scope. Listener configuration overrides applicable global settings, so multi-site gateways need explicit ownership of which audience sees which failure content.''',
'''Application Gateway downloads the configured HTML page from a publicly accessible URL and caches it locally. The source must meet documented requirements: the file is HTML/HTM, under the size limit, reachable publicly, and returns HTTP 200 when Application Gateway fetches it. If Azure Blob Storage hosts the file, network access must allow the gateway to retrieve it according to current requirements; a CDN-fronted-only Blob path is not supported for this purpose. When a gateway-generated error occurs, the gateway returns the cached HTML and the corresponding error status to the client. External CSS, images, or scripts referenced by that HTML are fetched by the client, so they also need absolute publicly reachable URLs. The gateway does not continuously poll the source for changed content. A configuration update is needed to refresh the cached copy. This makes the error page a deployment artifact whose version should be tracked, not a live website that operators edit without gateway refresh.''',
'''Host a small static error page at a stable HTTPS URL and verify it returns HTTP 200 directly. Keep the page self-contained when possible so a gateway failure does not also depend on several third-party assets. Configure a global or listener-level custom error according to the audience. Microsoft documents Azure PowerShell for this configuration. For a global 502 page, retrieve the Application Gateway, add the custom error object, and then apply the updated gateway. For a listener-specific page, retrieve the listener, add the listener custom-error setting, and commit the gateway. Store the public page URL and the expected status code in infrastructure source control. After changing the source HTML, force the documented configuration refresh; do not assume the gateway periodically reloads it. Test both a gateway-generated failure and a backend-generated failure so operators learn which response is supposed to be branded and which should pass through unchanged.''',
'Caching, scope precedence, and incident use',
'''Global custom pages apply broadly, but a listener-specific custom error configuration replaces relevant global behavior for that listener. On a gateway hosting multiple applications, use listener scope when business units require different branding or support contacts. Keep all required status-code URLs explicit when combining scopes so a listener override does not unintentionally remove a global custom page you expected to remain. Cache behavior is another operational trap: editing `maintenance.html` in Storage does not guarantee Application Gateway immediately fetches the new version. Use a controlled configuration update and then trigger the intended error to prove the cached copy changed. For incident response, keep pages lightweight and avoid embedding diagnostic details that reveal internal hosts, backend addresses, or security policy. A 403 page used for WAF prevention can provide a correlation/reference instruction without exposing the exact managed rule. A 502/503 maintenance page can direct users to a status site while the backend pool is unavailable.''',
'''$appgw = Get-AzApplicationGateway -Name <appgw> -ResourceGroupName <rg>
$updated = Add-AzApplicationGatewayCustomError -ApplicationGateway $appgw -StatusCode HttpStatus502 -CustomErrorPageUrl "https://<public-host>/errors/502.html"
Set-AzApplicationGateway -ApplicationGateway $appgw
# Listener scope uses Get-AzApplicationGatewayHttpListener and Add-AzApplicationGatewayHttpListenerCustomError.''',
'''Source page GET: HTTP 200
Application Gateway update: ProvisioningState Succeeded
Controlled gateway-generated backend failure:
HTTP/1.1 502 Bad Gateway
Body contains: company-branded maintenance page
Backend-originated 502 test:
Body remains backend response, demonstrating pass-through boundary''',
'''Success requires more than a configured URL. Application Gateway must be able to retrieve and cache the source page, the gateway update must succeed, and a gateway-generated error must return the expected custom HTML. A backend-generated error should remain unchanged; that negative test proves the team understands the origin boundary instead of assuming every matching status code is rewritten.''',
'''curl -I https://<public-host>/errors/502.html
# Trigger the controlled gateway-generated error and inspect response headers/body.
# If content was updated, perform the documented gateway configuration refresh and retest.''',
'''Source page: HTTP 403 Forbidden
Gateway configuration references the URL
Client during backend outage: default Application Gateway 502 page
Or:
Source page HTTP 200, but cached body is the previous version after file edit''',
'''If the source page is not publicly retrievable with HTTP 200, fix its hosting/network access before changing listeners or backend pools. If the old page remains cached after a source-file edit, perform a gateway configuration update that refreshes the custom-error cache and retest. Do not troubleshoot DNS to the application origin when the failing dependency is the separate public URL used to fetch the custom page.''',
['Client','Application Gateway Error Decision','Cached Custom HTML','Public Error Page Source'])
]

# ---------- rendering helpers ----------
def esc(s): return html.escape(s,quote=True)
def prose(s):
    return ''.join(f'<p>{html.escape(p.strip())}</p>' for p in s.strip().split('\n\n') if p.strip())
def code(s,cls=''):
    c=f' class="{cls}"' if cls else ''
    return f'<pre{c}><code>{html.escape(s.strip())}</code></pre>'

def diagram_assets(i,l):
    base=f'{STAMP}-L{i:02d}-{l["slug"]}'
    draw=IMAGES/(base+'.drawio'); svg=IMAGES/(base+'.svg')
    labels=l['diagram_nodes']; xs=[55,360,665,970]; cols=['#e6f2ff','#fff4ce','#e9f7ef','#f5e9ff']
    cells=[]
    for n,(x,label,col) in enumerate(zip(xs,labels,cols),2):
        shape=['virtual_networks','virtual_machine','load_balancer','application_gateway'][n-2]
        cells.append(f'<mxCell id="{n}" value="{esc(label)}" style="shape=mxgraph.azure2.{shape};whiteSpace=wrap;html=1;fillColor={col};strokeColor=#0078d4;fontSize=13;" vertex="1" parent="1"><mxGeometry x="{x}" y="105" width="210" height="95" as="geometry"/></mxCell>')
    edges=[]
    for n in range(2,5):
        edges.append(f'<mxCell id="e{n}" value="flow / control" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=3;endArrow=block;strokeColor=#3b6ea8;" edge="1" parent="1" source="{n}" target="{n+1}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml=f'''<mxfile host="app.diagrams.net" modified="2026-09-13T15:00:00.000Z" agent="ChatGPT" version="24.7.17"><diagram id="{base}" name="Architecture"><mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" page="1" pageWidth="1400" pageHeight="650"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{''.join(cells)}{''.join(edges)}</root></mxGraphModel></diagram></mxfile>'''
    draw.write_text(xml)
    boxes=[]
    for x,label,col in zip(xs,labels,cols):
        boxes.append(f'<rect x="{x}" y="105" width="210" height="95" rx="15" fill="{col}" stroke="#0078d4" stroke-width="2"/><text x="{x+105}" y="145" text-anchor="middle" font-family="Segoe UI,Arial" font-size="16" fill="#17324d">{esc(label)}</text><text x="{x+105}" y="170" text-anchor="middle" font-family="Segoe UI,Arial" font-size="12" fill="#5b6d7d">Azure architecture component</text>')
    arrows=[]
    for x1,x2 in zip([265,570,875],[360,665,970]):
        arrows.append(f'<path d="M{x1} 152 C{x1+28} 120 {x2-28} 120 {x2} 152" fill="none" stroke="#3b6ea8" stroke-width="4" marker-end="url(#a)"/><text x="{(x1+x2)//2}" y="118" text-anchor="middle" font-family="Segoe UI,Arial" font-size="12" fill="#3b6ea8">flow / control</text>')
    svg.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="330" viewBox="0 0 1240 330" role="img" aria-labelledby="t d"><title id="t">{esc(l['title'])}</title><desc id="d">Full-width Azure architecture diagram.</desc><defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#3b6ea8"/></marker></defs><rect width="1240" height="330" fill="#f8fbfd"/><text x="40" y="52" font-family="Segoe UI,Arial" font-size="24" font-weight="600" fill="#0a3558">{esc(l['title'])}</text>{''.join(boxes)}{''.join(arrows)}<text x="40" y="285" font-family="Segoe UI,Arial" font-size="13" fill="#5b6d7d">Control and packet-flow relationships — editable Azure-stencil source provided in draw.io format.</text></svg>''')
    return base

css='''
:root{--az:#0078d4;--ink:#172b3d;--muted:#5b6d7d;--line:#ccd8e2;--paper:#fff;--bg:#eef3f8;--code:#071d2e;--ok:#107c41;--bad:#a4262c}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14.5px/1.56 "Segoe UI",Arial,sans-serif}main{width:1320px;max-width:calc(100% - 64px);margin:24px auto 70px}header,.toc,.lesson,.quiz{background:var(--paper);border:1px solid var(--line);padding:24px 30px;margin-bottom:22px;box-shadow:0 5px 18px rgba(20,55,80,.06)}header{border-top:6px solid var(--az)}h1{font-size:30px;line-height:1.18;color:#0a3558;margin:.15em 0 .45em}h2{font-size:23px;line-height:1.23;color:#0a3558;margin:.2em 0 .8em}h3{font-size:18px;line-height:1.3;color:#075a9c;margin:1.35em 0 .45em;border-bottom:1px solid #dce6ed;padding-bottom:.25em}p,li{max-width:116ch}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.05em;font-weight:700;color:var(--az)}.architecture-diagram{display:block;width:100%;margin:14px 0 20px;background:#f8fbfd;border:1px solid #b7d4e8;padding:12px}.architecture-diagram img{display:block;width:100%;height:auto}.architecture-diagram figcaption,.meta{font-size:12.5px;color:var(--muted);margin-top:7px}.diagram-links{font-size:12.5px;margin-top:5px}pre{background:var(--code);color:#edf8ff;padding:14px 16px;overflow:auto;font:13px/1.48 Consolas,"Courier New",monospace}pre.output{background:#f7f9fb;color:#163047;border:1px solid #cbd8e2}.lab{border:1px solid #9ac9e6;background:#f3f9fd;padding:14px 16px}.ok{border-left:4px solid var(--ok);background:#f1f8f3;padding:10px 14px}.bad{border-left:4px solid var(--bad);background:#fff1f1;padding:10px 14px}.sources{font-size:12.5px;background:#f5f7f9;border-top:1px solid var(--line);padding:10px 12px;margin-top:18px}.toc ol{columns:2}.q{border:1px solid var(--line);padding:12px 14px;margin:12px 0}.choice{display:block;padding:5px 8px;background:#f7fafc;margin:5px 0}button{background:var(--az);color:#fff;border:0;padding:7px 11px;cursor:pointer;margin-right:6px}.result{white-space:pre-wrap;background:#eef7f1;padding:12px;margin-top:12px}a{color:#005ea8}'''

parts=[f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Azure Networking Specialty Daily Study — September 13, 2026</title><style>{css}</style></head><body><main><header><div class="eyebrow">Azure Networking Specialty · September 13, 2026</div><h1>Daily Interactive Study Report</h1><p><strong>Current alignment:</strong> Microsoft Certified: Azure Network Engineer Associate remains active (Microsoft credential page last updated July 29, 2026). The current AZ-700 study guide measures skills as of July 27, 2026.</p><p class="meta"><a href="{CERT}">Credential</a> · <a href="{GUIDE}">AZ-700 study guide</a></p></header><section class="toc"><h2>Today’s 12 lessons</h2><ol>''']
for i,l in enumerate(lessons,1): parts.append(f'<li><a href="#l{i}">{esc(l["title"])}</a></li>')
parts.append('</ol></section>')
asset_bases=[]
for i,l in enumerate(lessons,1):
    b=diagram_assets(i,l); asset_bases.append(b)
    parts.append(f'<section class="lesson" id="l{i}" data-domain="{esc(l["domain"])}"><div class="eyebrow">Lesson {i} · {esc(l["domain"])}</div><h2>{esc(l["title"])}</h2><h3>Why it matters</h3>{prose(l["why"])}<h3>Architecture</h3>{prose(l["arch"])}<figure class="architecture-diagram"><img src="images/{b}.svg" alt="{esc(l["title"])} architecture"><figcaption>Full-width architecture and control/data-flow view.</figcaption><div class="diagram-links"><a href="images/{b}.drawio">Editable draw.io source</a> · <a href="images/{b}.svg">Open SVG</a></div></figure><h3>Prerequisites and implementation</h3>{prose(l["impl"])}<div class="lab">{code(l["verify_cmd"])}</div><h3>{esc(l["extra_title"])}</h3>{prose(l["extra"])}<h3>Verification</h3>{code(l["verify_cmd"])}<div class="ok"><strong>Representative successful state</strong>{code(l["verify_out"],"output")}{prose(l["verify_text"])}</div><h3>Troubleshooting</h3>{code(l["trouble_cmd"])}<div class="bad"><strong>Representative failure state</strong>{code(l["trouble_out"],"output")}{prose(l["trouble_text"])}</div><div class="sources"><strong>Primary:</strong> <a href="{l["primary"]}">{l["primary"]}</a><br><strong>Scenario / implementation:</strong> <a href="{l["scenario"]}">{l["scenario"]}</a></div></section>')

# Questions: exact domain distribution 15/13/10/12. Choices deliberately concrete and unique.
Q=[]
def q(domain,lesson_no,text,correct,*wrong): Q.append(dict(domain=domain,lesson=lesson_no,text=text,correct=correct,options=[correct,*wrong],explanation=f'Lesson {lesson_no} establishes this as the relevant Azure behavior.',source=lessons[lesson_no-1]['primary']))
# Hybrid 15: 5 each lessons 1-3
q(D_H,1,'Which ExpressRoute Direct encapsulation uses a Microsoft-assigned outer service tag per circuit?','QinQ','Dot1Q','GRE','VXLAN')
q(D_H,1,'In Dot1Q mode, where must the customer keep C-tags unique?','Across the entire ExpressRoute Direct resource','Only inside one BGP session','Only on Microsoft peering','Only on one physical port')
q(D_H,1,'Can Direct encapsulation be changed in place after creation?','No','Yes, with a route-map update','Yes, after BGP reset','Yes, only for 100-Gbps ports')
q(D_H,1,'What evidence proves both Direct redundant paths are operational?','Independent BGP establishment and traffic on both physical paths','ProvisioningState alone','One circuit resource exists','One optical link is up')
q(D_H,1,'What should be checked before changing BGP policy when one Direct path is Idle after a VLAN change?','Layer-2 S-tag/C-tag and subinterface encapsulation','DNS TTL','WAF rules','Public IP quota')
q(D_H,2,'What does minScaleUnit equal to maxScaleUnit mean on ErGwScale?','Fixed scaling','BGP disabled','Private peering disabled','Autoscale to forty units')
q(D_H,2,'What is required for ErGwScale autoscaling?','Minimum at least two and maximum greater than minimum','Minimum equal to maximum','Basic public IP','A VPN gateway type')
q(D_H,2,'What scaling mode does Microsoft recommend for Private Link workloads on ErGwScale?','Fixed scaling','Always autoscaling','Scale-to-zero','No gateway')
q(D_H,2,'Which older ExpressRoute gateway family requires the migration tool rather than the direct AZ-SKU upgrade path?','Legacy Standard/HighPerformance/UltraPerformance','ErGw1Az/2Az/3Az','ErGwScale itself','VpnGw2AZ')
q(D_H,2,'What is a current ErGwScale limitation called out by Microsoft?','IPsec over ExpressRoute is not supported','Private peering is not supported','BGP is not supported','Multiple circuits are not supported')
q(D_H,3,'Which Azure NIC property must be enabled for a VM to forward transit packets?','IP forwarding','Accelerated networking only','Primary IP dynamic allocation','DNS proxy')
q(D_H,3,'What guest Linux setting must also permit IPv4 forwarding?','net.ipv4.ip_forward=1','rp_filter=2 only','tcp_syncookies=0','ip_local_port_range=443')
q(D_H,3,'What UDR next-hop type steers traffic to an NVA IP?','VirtualAppliance','Internet','VnetLocal','None')
q(D_H,3,'If the effective route points to the NVA and Azure NIC forwarding is true but the guest sysctl is zero, where is the fault?','Guest forwarding configuration','Azure DNS','ExpressRoute peering','Load Balancer probe')
q(D_H,3,'Why must the return path be designed explicitly for a stateful NVA?','Session symmetry may be required','Azure automatically reverses every UDR','DNSSEC requires it','Public IP Prefix requires it')
# Core 13: lesson 4 =7, lesson5=6
q(D_C,4,'What does an Azure Public IP Prefix reserve?','A contiguous block of Microsoft-owned public IP addresses','A private RFC1918 subnet','A BGP ASN range','A DNS suffix')
q(D_C,4,'What is the largest normal Microsoft-owned IPv4 Public IP Prefix size listed in the overview?','/28','/16','/24','/32')
q(D_C,4,'What SKU/allocation is required for a Public IP created from a normal prefix?','Standard static Public IP','Basic dynamic Public IP','Private IP only','Classic reserved IP')
q(D_C,4,'Does the prefix itself act as a packet next hop?','No','Yes, for all Internet traffic','Only for UDP','Only for IPv6')
q(D_C,4,'What happens to an individual address when its child Public IP resource is deleted but the prefix remains?','It returns to the reserved prefix for reuse','It is immediately allocated to another tenant','The entire prefix is deleted','It becomes a private address')
q(D_C,4,'Why can a /28 prefix consume quota before all child addresses are used?','The full reserved block counts toward public-IP capacity','Only active TCP flows count','DNS records reserve quota','BGP routes reserve quota')
q(D_C,4,'Can a prefix be deleted while child Public IP resources still reference it?','No','Yes, children are silently moved','Yes, only in East US','Yes, for zonal prefixes')
q(D_C,5,'What does a Standard Load Balancer health probe control?','Eligibility for new flows to backend instances','DNS resolution for clients','BGP advertisement','Public IP allocation')
q(D_C,5,'Which probe types are supported by Standard Load Balancer?','TCP, HTTP, and HTTPS','ICMP only','BGP and OSPF','SMTP only')
q(D_C,5,'What should an HTTP health endpoint return when the instance is ready?','HTTP 200 success','Always HTTP 503','A DNS NXDOMAIN','A BGP UPDATE')
q(D_C,5,'What normally happens to established TCP sessions when one backend probe goes down?','They can persist until app end, idle timeout, or VM shutdown','They always reset instantly','They are converted to UDP','They move to DNS')
q(D_C,5,'Why should an NVA health probe test the appliance itself instead of proxying through it to another VM?','Proxying can create misleading or cascading health failures','It disables Azure DNS','It consumes Public IP Prefix quota','It changes ExpressRoute tags')
q(D_C,5,'If local /health returns 200 but Azure reports Unhealthy, what should be investigated next?','Probe reachability, NSG, interface binding, and return path','Create a new Public IP Prefix','Change DNSSEC DS','Disable BGP')
# Routing 10: L6=4, L11=3, L12=3
q(D_R,6,'Where is Application Gateway connection draining configured?','Backend HTTP setting','DNS zone','WAF managed rule set','Public IP Prefix')
q(D_R,6,'What value disables Application Gateway connection draining?','0 seconds','1 second','300 seconds','3600 seconds')
q(D_R,6,'What should the drain timeout exceed for a download service?','The longest legitimate transfer duration to preserve','DNS TTL','BGP hold timer','NSG rule priority')
q(D_R,6,'During a rolling deployment, what should happen to new requests after backend A begins draining?','They should go to other eligible backends','They must remain on A forever','They are sent to DNS','They bypass Application Gateway')
q(D_R,11,'What does Load Balancer admin state Down do?','Prevents new connections to that backend even if the probe is healthy','Forces the probe to report healthy','Deletes the backend pool','Changes the frontend IP')
q(D_R,11,'What does admin state None mean?','Normal health-probe behavior decides eligibility','Backend is permanently down','Backend is forced up','Health probe is deleted')
q(D_R,11,'Why is forcing admin state Up risky on an unhealthy backend?','It can keep sending new traffic to a broken instance','It changes DNSSEC signing','It deletes TCP sessions automatically','It disables the frontend')
q(D_R,12,'Which Application Gateway error is currently not supported for custom error pages?','404','502','503','403')
q(D_R,12,'What must the remote custom error page return when Application Gateway retrieves it?','HTTP 200','HTTP 404','HTTP 502','TCP reset')
q(D_R,12,'Does a custom gateway 502 page replace a 502 generated by the backend application?','No, backend-originated responses pass through','Yes, always','Only with DNSSEC','Only when no listener exists')
# Security 12: L7-L10 3 each
q(D_S,7,'What two resource types can Network Watcher VPN troubleshoot target?','Virtual network gateway and VPN connection','DNS zone and record set','NIC and Public IP Prefix','WAF policy and rule')
q(D_S,7,'Where are detailed VPN troubleshoot logs stored?','The specified Azure Storage container','Key Vault only','DNS zone metadata','ExpressRoute route filter')
q(D_S,7,'If VPN troubleshoot returns Healthy but one application prefix fails, what is the best next direction?','Investigate prefix routing, security, and workload state','Recreate the gateway immediately','Disable the VPN','Change Front Door WAF')
q(D_S,8,'When does Azure Firewall threat intelligence evaluate relative to ordinary NAT/network/application rules?','Before those rule collections','After every application rule','Only after DNAT','Only after DNS fails')
q(D_S,8,'What is a safe rollout path for threat intelligence enforcement?','Observe in alert mode, then move to deny with controlled testing','Disable logs first','Allowlist all destinations','Delete application rules')
q(D_S,8,'What does a threat-intelligence allowlist do?','Bypasses threat-intelligence filtering for the specified indicator scope','Creates a normal application allow rule','Changes a UDR','Creates a VPN tunnel')
q(D_S,9,'Front Door WAF rate limiting is counted primarily by what client identity?','Client socket IP','Authenticated username automatically','DNS zone name','BGP ASN')
q(D_S,9,'What fixed windows are supported by Front Door WAF rate limiting?','One or five minutes','One second only','One hour only','Twenty-four hours only')
q(D_S,9,'Why can very low Front Door rate thresholds be less exact?','A client can reach different Front Door servers before counters converge','DNSSEC rewrites the source IP','BGP changes the WAF rule','The origin always resets the counter')
q(D_S,10,'What type of analysis does AVNM Network Verifier perform?','Static reachability analysis of supported Azure configuration','Full packet capture','TLS decryption','BGP route advertisement')
q(D_S,10,'What resource contains reachability intents and analysis runs?','Verifier workspace','Public IP Prefix','Load Balancer frontend','DNS zone')
q(D_S,10,'If Network Verifier says Reachable but the service still fails, what should you use next?','Runtime diagnostics such as Connection Troubleshoot, packet capture, or application logs','Broaden every NSG','Delete the verifier workspace','Change ExpressRoute encapsulation')

assert len(Q)==50
assert Counter(x['domain'] for x in Q)==Counter({D_H:15,D_C:13,D_R:10,D_S:12})

# deterministic option shuffle at runtime
qjson=json.dumps(Q,ensure_ascii=False)
quiz=f'''<section class="quiz" id="quiz"><h2>50-question interactive quiz</h2><p>Distribution: 15 Hybrid · 13 Core · 10 Routing · 12 Security/monitoring/private access.</p><div id="questions"></div><p><button onclick="gradeAll()">Finish and grade</button><button onclick="resetQuiz()">Reset</button></p><div id="result" class="result">Not graded yet.</div></section><script>const questions={qjson};function seeded(seed){{let x=seed>>>0;return function(){{x=(x*1664525+1013904223)>>>0;return x/4294967296}}}}function shuffle(a,s){{a=[...a];let r=seeded(s);for(let i=a.length-1;i>0;i--){{let j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]]}}return a}}function render(){{let root=document.getElementById('questions');questions.forEach((q,i)=>{{let d=document.createElement('div');d.className='q';let opts=shuffle(q.options,20260913+i*37);d.innerHTML=`<div class="eyebrow">Q${{i+1}} · ${{q.domain}} · Lesson ${{q.lesson}}</div><p><strong>${{q.text}}</strong></p>`+opts.map(o=>`<label class="choice"><input type="radio" name="q${{i}}" value="${{encodeURIComponent(o)}}"> ${{o}}</label>`).join('')+`<button onclick="check(${{i}})">Check answer</button><div id="f${{i}}"></div>`;root.appendChild(d)}})}}function selected(i){{let e=document.querySelector(`input[name="q${{i}}"]:checked`);return e?decodeURIComponent(e.value):null}}function check(i){{let q=questions[i],v=selected(i),f=document.getElementById('f'+i);if(v===null){{f.textContent='Choose an answer first.';return}}let ok=v===q.correct;f.style.color=ok?'#107c41':'#a4262c';f.innerHTML=(ok?'Correct. ':'Incorrect. Correct answer: '+q.correct+'. ')+q.explanation+` <a href="${{q.source}}" target="_blank">Source</a>`}}function gradeAll(){{let c=0,u=0,b={{}},review=[];questions.forEach((q,i)=>{{b[q.domain]??=[0,0];b[q.domain][1]++;let v=selected(i);if(v===null){{u++;review.push(`Q${{i+1}} unanswered — ${{q.correct}}`);return}}if(v===q.correct){{c++;b[q.domain][0]++}}else review.push(`Q${{i+1}} selected “${{v}}”; correct “${{q.correct}}”`);check(i)}});let lines=Object.entries(b).map(([k,v])=>`${{k}}: ${{v[0]}}/${{v[1]}}`);document.getElementById('result').textContent=`Score: ${{c}}/50 (${{(c*2).toFixed(0)}}%)\nUnanswered: ${{u}}\n\nDomain breakdown\n${{lines.join('\n')}}\n\nAnswer review\n${{review.length?review.join('\n'):'All answered correctly.'}}`}}function resetQuiz(){{document.querySelectorAll('input[type=radio]').forEach(x=>x.checked=false);document.querySelectorAll('.q div[id^=f]').forEach(x=>x.textContent='');document.getElementById('result').textContent='Not graded yet.'}}render();</script>'''
parts.append(quiz+'</main></body></html>')
report=''.join(parts)
(DOCS/REPORT).write_text(report)

# Update index to exact Pages URL
(DOCS/'index.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Azure Networking Specialty Daily Study</title><style>body{{font:14.5px/1.55 "Segoe UI",Arial,sans-serif;max-width:900px;margin:48px auto;color:#172b3d}}a{{color:#005ea8;font-weight:700}}</style></head><body><h1>Azure Networking Specialty daily study</h1><p>Latest validated report:</p><p><a href="{URL}">{URL}</a></p><p>Microsoft Certified: Azure Network Engineer Associate / AZ-700 alignment verified September 13, 2026.</p></body></html>''')

# ----- hard validation -----
assert report.count('<section class="lesson"')==12
assert '<h3>Summary</h3>' not in report and 'Exam and interview takeaways' not in report
assert '.architecture-diagram img{display:block;width:100%;height:auto}' in report
assert 'font:14.5px/1.56' in report and 'font-size:30px' in report and 'font-size:23px' in report and 'font-size:18px' in report and 'font:13px/1.48' in report
sections=re.findall(r'<section class="lesson".*?</section>',report,re.S)
counts=[]
for sec in sections:
    txt=re.sub(r'<pre.*?</pre>',' ',sec,flags=re.S)
    txt=re.sub(r'<div class="sources".*?</div>',' ',txt,flags=re.S)
    txt=re.sub(r'<[^>]+>',' ',txt)
    counts.append(len(re.findall(r"\b[\w'’/-]+\b",html.unescape(txt))))
if min(counts)<700:
    raise SystemExit(f'WORD COUNT FAILURE {counts}')
# near duplicate paragraph gate
paras=[]
for sec in sections:
    title=re.search(r'<h2>(.*?)</h2>',sec).group(1)
    for p in re.findall(r'<p>(.*?)</p>',sec,re.S):
        t=re.sub('<[^>]+>',' ',p); t=' '.join(html.unescape(t).lower().split())
        if len(t.split())>=25: paras.append((title,t))
seen={}
for title,t in paras:
    key=re.sub(r'[^a-z0-9 ]','',t)
    if key in seen: raise SystemExit(f'DUPLICATE PARAGRAPH: {title} and {seen[key]}')
    seen[key]=title
assert len(asset_bases)==12 and len(set(asset_bases))==12
for b in asset_bases:
    assert '<svg' in (IMAGES/(b+'.svg')).read_text()
    assert 'mxgraph.azure2' in (IMAGES/(b+'.drawio')).read_text()
assert len(Q)==50 and Counter(x['domain'] for x in Q)==Counter({D_H:15,D_C:13,D_R:10,D_S:12})
assert 'function check' in report and 'function gradeAll' in report and 'function resetQuiz' in report
# current source-role URLs are unique in this run
urls=[u for l in lessons for u in (l['primary'],l['scenario'])]
assert len(urls)==len(set(urls))
validation={'report':REPORT,'url':URL,'lesson_count':12,'lesson_substantive_word_counts':counts,'minimum_substantive_words':min(counts),'questions':50,'distribution':dict(Counter(x['domain'] for x in Q)),'drawio_svg_pairs':12,'full_width_diagrams':'PASS','compact_desktop_typography':'PASS','implementation':'PASS','verification_expected_output':'PASS','troubleshooting_failure_output':'PASS','nonredundancy':'PASS','source_role_separation':'PASS','certification_verified':'2026-09-13'}
(DOCS/'.azure-study-2026-09-13-validation.json').write_text(json.dumps(validation,indent=2)+'\n')

# Ledger entry payload is written now, but the workflow appends it only after repo fetch-back succeeds.
entry={'run_id':'azure-networking-study-2026-09-13-08-00-pacific','date':'2026-09-13','timestamp_pacific':'2026-09-13T08:00:00-07:00','report_file':'docs/'+REPORT,'report_url':URL,'topic_fingerprints':[l['slug'] for l in lessons],'source_case_fingerprints':[l['slug']+'-implementation-verification-case' for l in lessons],'lessons':[{'lesson':i,'title':l['title'],'topic_fingerprint':l['slug'],'source_case_fingerprint':l['slug']+'-implementation-verification-case','primary_url':l['primary'],'scenario_url':l['scenario'],'substantive_words':counts[i-1]} for i,l in enumerate(lessons,1)],'validation':validation|{'rolling_30_day_uniqueness':'PASS','report_fetch_back':'PENDING','index_fetch_back':'PENDING','asset_fetch_back':'PENDING'}}
(DOCS/'.azure-ledger-entry-20260913.json').write_text(json.dumps(entry,indent=2)+'\n')
print('BUILT',REPORT,'COUNTS',counts,'QUESTIONS',len(Q))
