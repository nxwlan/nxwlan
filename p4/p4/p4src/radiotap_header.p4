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

//Change endianess
#define BE2LE2( x )    ( (((x) >> 8) & 0x00FF) | (((x) << 8) & 0xFF00) )
#define BE2LE3( x )    ( (((x) >> 16) & 0x0000FF) | ((x) & 0x00FF00) | \
					     (((x) << 16) & 0xFF0000) )
#define BE2LE4( x )    ( (((x) >> 24) & 0x000000FF) | (((x) >>  8) & 0x0000FF00) | \
					     (((x) <<  8) & 0x00FF0000) | (((x) << 24) & 0xFF000000) )


#define RADIOTAP_PRESENT_TSFT 1<<0
#define RADIOTAP_PRESENT_FLAGS 1<<1
#define RADIOTAP_PRESENT_RATE 1<<2
#define RADIOTAP_PRESENT_CHANNEL 1<<3
#define RADIOTAP_PRESENT_FHSS 1<<4
#define RADIOTAP_PRESENT_ANTENNA_SIGNAL 1<<5
#define RADIOTAP_PRESENT_ANTENNA_NOISE 1<<6
#define RADIOTAP_PRESENT_LOCK_QUALITY 1<<7
#define RADIOTAP_PRESENT_TX_ATTENUATION 1<<8
#define RADIOTAP_PRESENT_DB_TX_ATTENUATION 1<<9
#define RADIOTAP_PRESENT_DBM_TX_POWER 1<<10
#define RADIOTAP_PRESENT_ANTENNA 1<<11
#define RADIOTAP_PRESENT_DB_ANTENNA_SIGNAL 1<<12
#define RADIOTAP_PRESENT_DB_ANTENNA_NOISE 1<<13
#define RADIOTAP_PRESENT_RX_FLAGS 1<<14
#define RADIOTAP_PRESENT_B15 1<<15
#define RADIOTAP_PRESENT_B16 1<<16
#define RADIOTAP_PRESENT_B17 1<<17
#define RADIOTAP_PRESENT_B18 1<<18
#define RADIOTAP_PRESENT_MCS 1<<19
#define RADIOTAP_PRESENT_A_MPDU_STATUS 1<<20
#define RADIOTAP_PRESENT_VHT 1<<21
#define RADIOTAP_PRESENT_B22 1<<22
#define RADIOTAP_PRESENT_B23 1<<23
#define RADIOTAP_PRESENT_B24 1<<24
#define RADIOTAP_PRESENT_B25 1<<25
#define RADIOTAP_PRESENT_B26 1<<26
#define RADIOTAP_PRESENT_B27 1<<27
#define RADIOTAP_PRESENT_B28 1<<28
#define RADIOTAP_PRESENT_RESET 1<<29
#define RADIOTAP_PRESENT_VENDOR 1<<30
#define RADIOTAP_PRESENT_TSFT 1<<31
#define RADIOTAP_PRESENT_EXT 1<<32

header_type radiotap_t {
    fields {
        bit<8> version;
        bit<8> pad;
        bit<16> len;
        bit<32> present;
        varbit<240> rtapdata;
    }
    length : BE2LE2(len);
}