/*
Copyright 2016-present Piotr Gawlowicz, TUB

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include "constants.p4"
#include "ethernet_header.p4"
#include "radiotap_header.p4"
#include "dot11_header.p4"
#include "parsers.p4"

header_type intrinsic_metadata_t {
    fields {
        bit<4> mcast_grp;
        bit<4> egress_rid;
        bit<16> mcast_hash;
        bit<32>  lf_field_list;
    }
}


//Actions
action _drop() {
    drop();
}

action _nop() {
}

action send_to_port (in bit<8> out_port) {
    modify_field(standard_metadata.egress_spec, out_port);
}

action add_eth_header () {
    add_header(ethernet);
    modify_field(ethernet.dstAddr, dot11_fc_metadata.da);
    modify_field(ethernet.srcAddr, dot11_fc_metadata.sa);
    modify_field(ethernet.etherType, CRAN_RADIO_TAP);
}

action remove_eth_header () {
    remove_header(ethernet);
}

//Tables


table table_modify_ethernet_header {
    reads {
        standard_metadata.egress_port : exact;
    }
    actions {
        add_eth_header;
        remove_eth_header;
        _nop;
        _drop;
    }
    size : 128;
}

table table_switch_da {
    reads {
        standard_metadata.ingress_port : exact;
        dot11_fc_metadata.da : exact;
    }
    actions {
        send_to_port;
        _drop;
    }
    size : 16384;
}

table table_drop_tx_frames_from_monitor {
    reads {
        standard_metadata.ingress_port : exact;
        radiotap_metadata.rx : exact;
    }
    actions {
        _drop;
        _nop;
    }
    size : 32;
}

table table_wire_ports {
    reads {
        standard_metadata.ingress_port : exact;
    }
    actions {
        send_to_port;
        _drop;
    }
    size : 32;
}

//drop beacons received on monitor interface
table table_drop_rx_beacons {
    reads {
        standard_metadata.ingress_port : exact;
        dot11_fc_metadata.Type : exact;
        dot11_fc_metadata.Subtype : exact;
    }
    actions {
        _nop;
        _drop;
    }
    size : 2;
}

table table_drop_control_frames {
    reads {
        dot11_fc_metadata.Type : exact;
    }
    actions {
        _nop;
        _drop;
    }
    size : 2;
}

//Controls
control ingress {
    //perform switching
    if ((valid(radiotap)) and (valid(dot11_frame_control))) {
        //apply(table_switch_da);
        apply(table_wire_ports);
        apply(table_drop_tx_frames_from_monitor);
        apply(table_drop_rx_beacons);
        apply(table_drop_control_frames);
    }
}

#define BROADCAST_SESSION_ID                  255

field_list broadcast_pkt_copy_fields {
    standard_metadata.instance_type;
}

action clone_broadcast_packet() {
    clone_egress_pkt_to_egress(BROADCAST_SESSION_ID, broadcast_pkt_copy_fields);
}

table table_serve_broadcast {
    reads {
        standard_metadata.ingress_port : exact;
        dot11_fc_metadata.da : exact;
    }
    actions {
        clone_broadcast_packet;
        _nop;
    }
    size : 1;
}

control egress {
    //drop packets, unless RH is allowed to receive it

    //add/remove ethernet header if going to tunnel/monitor interface
    apply(table_modify_ethernet_header);
}