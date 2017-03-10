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

//Version
#define DOT11_VERSION 0x0

//Types
#define DOT11_TYPE_MGMT     0x0
#define DOT11_TYPE_CTRL     0x1
#define DOT11_TYPE_DATA     0x2
#define DOT11_TYPE_RESERVED 0x3

//Subtypes of MGMT
#define DOT11_SUBTYPE_ASSOC_REQ     0x0
#define DOT11_SUBTYPE_ASSOC_RESP    0x1
#define DOT11_SUBTYPE_REASOC_REQ    0x2
#define DOT11_SUBTYPE_REASOC_RESP   0x3
#define DOT11_SUBTYPE_PROBE_REQ     0x4
#define DOT11_SUBTYPE_PROBE_RESP    0x5
#define DOT11_SUBTYPE_BEACON        0x8
#define DOT11_SUBTYPE_ATIM          0x9
#define DOT11_SUBTYPE_DISASSOC      0xA
#define DOT11_SUBTYPE_AUTH          0xB
#define DOT11_SUBTYPE_DEAUTH        0xC

//Subtypes of CTRL
#define DOT11_SUBTYPE_PS_POLL       0xA
#define DOT11_SUBTYPE_RTS           0xB
#define DOT11_SUBTYPE_CTS           0xC
#define DOT11_SUBTYPE_ACK           0xD
#define DOT11_SUBTYPE_CF_END        0xE
#define DOT11_SUBTYPE_CF_END_CF_ACK 0xF

//Subtypes of DATA
#define DOT11_SUBTYPE_DATA                    0x0
#define DOT11_SUBTYPE_DATA_CF_ACK             0x1
#define DOT11_SUBTYPE_DATA_CF_POLL            0x2
#define DOT11_SUBTYPE_DATA_CF_ACK_CF_POLL     0x3
#define DOT11_SUBTYPE_NULL                    0x4
#define DOT11_SUBTYPE_CF_ACK_NO_DATA          0x5
#define DOT11_SUBTYPE_CF_POLL_NO_DATA         0x6
#define DOT11_SUBTYPE_CF_ACK_CF_POLL_NO_DATA  0x7

// Frame definition
// http://flylib.com/books/en/2.799.1.29/1/

header_type dot11_frame_control_t {
    fields {
        bit<8> Type;
        bit<8> Flags;
    }
}

header_type dot11_fc_metadata_t {
    fields {
        bit<8> Version;
        bit<8> Type;
        bit<8> Subtype;
        bit<8> toDS;
        bit<8> fromDS;
        bit<8> mf;
        bit<8> retry;
        bit<8> pwr_mgnt;
        bit<8> md;
        bit<8> wep;
        bit<8> order;
        bit<48> sa;
        bit<48> da;
        bit<48> bssid;
    }
}

//Mgmt frames
header_type dot11_mgmt_frame_t {
    fields {
        bit<16> duration;
        bit<48> da;
        bit<48> sa;
        bit<48> bssid;
        bit<16> sc;
        //frame body
        //fcs
    }
}


//Control frames
header_type dot11_ps_poll_t {
    fields {
        bit<16> aid;
        bit<48> bssid;
        bit<48> ta;
        bit<32> fcs;
    }
}

header_type dot11_rts_t {
    fields {
        bit<16> duration;
        bit<48> ra;
        bit<48> ta;
        bit<32> fcs;
    }
}

header_type dot11_cts_t {
    fields {
        bit<16> duration;
        bit<48> ra;
        bit<32> fcs;
    }
}

header_type dot11_ack_t {
    fields {
        bit<16> duration;
        bit<48> ra;
        bit<32> fcs;
    }
}

header_type dot11_cf_end_t {
    fields {
        bit<16> duration;
        bit<48> ra;
        bit<48> bssid;
        bit<32> fcs;
    }
}

header_type dot11_cf_end_cf_ack_t {
    fields {
        bit<16> duration;
        bit<48> ra;
        bit<48> bssid;
        bit<32> fcs;
    }
}


//Data frames
header_type dot11_data_frame_t {
    fields {
        bit<16> duration;
        bit<48> addr1;
        bit<48> addr2;
        bit<48> addr3;
        bit<16> sc;
        bit<48> addr4;
        //frame body
        //fcs
    }
}

header_type dot11_no_data_frame_t {
    fields {
        bit<16> duration;
        bit<48> addr1;
        bit<48> addr2;
        bit<48> addr3;
        bit<16> sc;
        //frame body
        //fcs
    }
}