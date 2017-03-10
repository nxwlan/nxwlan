//Parsers

parser start {
    return select(standard_metadata.ingress_port) {
        0 : parse_radiotap;
        1 : parse_radiotap;
        default : parse_ethernet;
    }
}

header ethernet_t ethernet;
parser parse_ethernet {
    extract(ethernet);
    return select(ethernet.etherType) {
        CRAN_RADIO_TAP : parse_radiotap;
        default: ingress;
    }
}

header radiotap_t radiotap;
metadata radiotap_metadata_t radiotap_metadata;
parser parse_radiotap {
    extract(radiotap);

    set_metadata(radiotap_metadata.present, BE2LE4(radiotap.present));
    set_metadata(radiotap_metadata.rx, (BE2LE4(radiotap.present) & RADIOTAP_PRESENT_RX_FLAGS) >> 14);

    return parse_dot11_frame_control;
}

header dot11_frame_control_t dot11_frame_control;
metadata dot11_fc_metadata_t dot11_fc_metadata;

parser parse_dot11_frame_control {
    extract(dot11_frame_control);

    set_metadata(dot11_fc_metadata.Version, (dot11_frame_control.Type & 0x03) >> 0);
    set_metadata(dot11_fc_metadata.Type, (dot11_frame_control.Type & 0x0c) >> 2);
    set_metadata(dot11_fc_metadata.Subtype, (dot11_frame_control.Type & 0xf0) >> 4);

    return select(dot11_fc_metadata.Type) {
        DOT11_TYPE_MGMT : parse_dot11_mgmt;
        DOT11_TYPE_CTRL : parse_dot11_ctrl;
        DOT11_TYPE_DATA : parse_dot11_data;
        default : ingress;
    }
}

header dot11_mgmt_frame_t dot11_mgmt_frame;
parser parse_dot11_mgmt {
    extract(dot11_mgmt_frame);
    set_metadata(dot11_fc_metadata.da, dot11_mgmt_frame.da);
    set_metadata(dot11_fc_metadata.sa, dot11_mgmt_frame.sa);
    set_metadata(dot11_fc_metadata.bssid, dot11_mgmt_frame.bssid);

    return select(dot11_fc_metadata.Subtype) {
        DOT11_SUBTYPE_ASSOC_REQ : ingress;
        DOT11_SUBTYPE_ASSOC_RESP : ingress;
        DOT11_SUBTYPE_REASOC_REQ : ingress;
        DOT11_SUBTYPE_REASOC_RESP : ingress;
        DOT11_SUBTYPE_PROBE_REQ : ingress;
        DOT11_SUBTYPE_PROBE_RESP : ingress;
        DOT11_SUBTYPE_BEACON : ingress;
        DOT11_SUBTYPE_ATIM : ingress;
        DOT11_SUBTYPE_DISASSOC : ingress;
        DOT11_SUBTYPE_AUTH : ingress;
        DOT11_SUBTYPE_DEAUTH : ingress;
        default : ingress;
    }
}


parser parse_dot11_ctrl {
    set_metadata(dot11_fc_metadata.da, 0);
    set_metadata(dot11_fc_metadata.sa, 0);
    set_metadata(dot11_fc_metadata.bssid, 0);

    return select(dot11_fc_metadata.Subtype) {
        DOT11_SUBTYPE_PS_POLL : ingress;
        DOT11_SUBTYPE_RTS : ingress;
        DOT11_SUBTYPE_CTS : ingress;
        DOT11_SUBTYPE_ACK : ingress;
        DOT11_SUBTYPE_CF_END : ingress;
        DOT11_SUBTYPE_CF_END_CF_ACK : ingress;
        default : ingress;
    }
}

parser parse_dot11_data {
    set_metadata(dot11_fc_metadata.da, 0);
    set_metadata(dot11_fc_metadata.sa, 0);
    set_metadata(dot11_fc_metadata.bssid, 0);

    return select(dot11_fc_metadata.Subtype) {
        DOT11_SUBTYPE_DATA : parse_dot11_normal_data;
        DOT11_SUBTYPE_DATA_CF_ACK : parse_dot11_normal_data;
        DOT11_SUBTYPE_DATA_CF_POLL : parse_dot11_normal_data;
        DOT11_SUBTYPE_DATA_CF_ACK_CF_POLL : parse_dot11_normal_data;
        DOT11_SUBTYPE_NULL : parse_dot11_no_data;
        DOT11_SUBTYPE_CF_ACK_NO_DATA : parse_dot11_no_data;
        DOT11_SUBTYPE_CF_POLL_NO_DATA : parse_dot11_no_data;
        DOT11_SUBTYPE_CF_ACK_CF_POLL_NO_DATA : parse_dot11_no_data;
        default : ingress;
    }
}

header dot11_data_frame_t dot11_data_frame;
parser parse_dot11_normal_data {
    extract(dot11_data_frame);
    set_metadata(dot11_fc_metadata.da, dot11_data_frame.addr1);
    set_metadata(dot11_fc_metadata.sa, dot11_data_frame.addr2);
    set_metadata(dot11_fc_metadata.bssid, dot11_data_frame.addr3);
    return ingress;
}

header  dot11_no_data_frame_t dot11_no_data_frame;
parser parse_dot11_no_data {
    extract(dot11_no_data_frame);
    set_metadata(dot11_fc_metadata.da, dot11_no_data_frame.addr1);
    set_metadata(dot11_fc_metadata.sa, dot11_no_data_frame.addr2);
    set_metadata(dot11_fc_metadata.bssid, dot11_no_data_frame.addr3);
    return ingress;
}