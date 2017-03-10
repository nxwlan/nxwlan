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

//Controls
control ingress {
    //perform switching
    if ((valid(radiotap)) and (valid(dot11_frame_control))) {
        apply(table_switch_da);
    }
}

control egress {
    //add/remove ethernet header
    apply(table_modify_ethernet_header);  
}