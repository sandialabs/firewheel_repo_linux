#!/bin/bash

DEVS=()
MACS=()
USED_DEVS=()
NAMESERVERS=$(head -n 1 $1)
# Remove nameservers from the dynamic file
sed -i '1d' $1

get_interface_names () {
    DEVS=($(ip -o link show | awk -F': ' '{print $2}'))
}

get_macs () {
    for dev in ${DEVS[@]}
    do
        mac="$(ip address show $dev | grep ether | awk '{print $2}')"
        MACS+=("${mac}")
    done
}

get_interface_info () {
    get_interface_names
    get_macs

    for (( i=0; i<${#MACS[@]}; i++ ))
    do
        if [[ -z ${MACS[$i]} ]]
        then
            continue
        fi
        echo "${DEVS[$i]} -> ${MACS[$i]}"
    done
}

get_interface_info

set_gateway () {
    if [ ! -z $1 ]
    then
        ip route add default via $1
    fi
}

set_dns_nameservers () {
    if [ ! -z "$NAMESERVERS" ]; then
        DNS1=$(echo $NAMESERVERS | awk '{print $1}')
        echo "nameserver ${DNS1}" >> /etc/resolv.conf

        DNS2=$(echo $NAMESERVERS | awk '{print $2}')
        if [ ! -z "$DNS2" ]; then
            echo "nameserver ${DNS2}" >> /etc/resolv.conf
        fi
    fi
}

set_dns_nameservers

set_ip () {
    echo "SETTING $1 to IP: $2"
    ip addr flush dev $1
    ip addr add dev $1 $2
    ip link set dev $1 up

    ip addr | grep $2
    while [ $? -ne 0 ]; do
        echo "IP did not take, sleeping and trying again"
        sleep 1
        ip addr add dev $1 $2
        ip addr | grep $2
    done
}

find_device () {
    for (( i=0; i<${#MACS[@]}; i++ ));
    do
        if [ "${MACS[$i]}" == $1 ]
        then
            echo ${DEVS[$i]}
            return 0
        fi
    done

    echo ""
    return 1
}

add_persistent_network_manager_static_ip () {
    DEV=$1
    MAC=$2
    ADDR=$3
    NETMASK=$4
    GATEWAY=$5
    if [ -d /etc/network/interfaces.d ]; then
        cat >/etc/network/interfaces.d/${DEV} <<EOF
auto ${DEV}
iface ${DEV} inet static
    address ${ADDR}
    netmask ${NETMASK}
EOF

        if [ ! -z "$GATEWAY" ]; then
            echo "    gateway ${GATEWAY}" >> /etc/network/interfaces.d/${DEV}
        fi
        if [ ! -z "$NAMESERVERS" ]; then
            echo "    dns-nameservers ${NAMESERVERS}" >> /etc/network/interfaces.d/${DEV}
        fi
        return
    fi
    if [ -f /etc/network/interfaces ]; then
        cat >>/etc/network/interfaces <<EOF
auto ${DEV}
iface ${DEV} inet static
    address ${ADDR}
    netmask ${NETMASK}
EOF

        if [ ! -z "$GATEWAY" ]; then
            echo "    gateway ${GATEWAY}" >> /etc/network/interfaces
        fi
        if [ ! -z "$NAMESERVERS" ]; then
            echo "    dns-nameservers ${NAMESERVERS}" >> /etc/network/interfaces
        fi

        if ! grep -Fq 'source /etc/network/interfaces.d/*' /etc/network/interfaces
        then
            echo "" >> /etc/network/interfaces
            echo 'source /etc/network/interfaces.d/*' >> /etc/network/interfaces
        fi
    fi
}

add_persistent_sysconfig_static_ip () {
    DEV=$1
    MAC=$2
    ADDR=$3
    NETMASK=$4
    GATEWAY=$5
    IFACE_FILE="/etc/sysconfig/network-scripts/ifcfg-${DEV}"
    if [ -f $IFACE_FILE ]; then
        sed -i '/^BOOTPROTO=/d' $IFACE_FILE
        echo "IPADDR=${ADDR}" >> $IFACE_FILE
        echo "NETMASK=${NETMASK}" >> $IFACE_FILE
        echo "BOOTPROTO=static" >> $IFACE_FILE
    fi
    if [ ! -z "$GATEWAY" ]; then
        echo "GATEWAY=${GATEWAY}" >> $IFACE_FILE
    fi
    if [ ! -z "$NAMESERVERS" ]; then
        DNS1=$(echo $NAMESERVERS | awk '{print $1}')
        echo "DNS1=${DNS1}" >> $IFACE_FILE

        DNS2=$(echo $NAMESERVERS | awk '{print $2}')
        if [ ! -z "$DNS2" ]; then
            echo "DNS2=${DNS2}" >> $IFACE_FILE
        fi
    fi
}

add_persistent_systemd_static_ip () {
    # This function is for systemd configurations
    MAC=$1
    ADDR=$2
    PREFIX=$3
    GATEWAY=$4
    NETWORK=$5
    IP="${ADDR}/${PREFIX}"
    cat >/etc/systemd/network/${NETWORK}.network <<EOF
[Match]
MACAddress=${MAC}

[Network]
Address=$IP
Gateway=$GATEWAY
EOF
}

check_link_up () {
    # This function is for systemd configurations
    routable=$(networkctl status $1 | grep State | grep routable)
    if [ -z $routable ]
    then
        return 0
    fi

    configured=$(networkctl status $1 | grep State | grep configured)
    if [ -z $configured ]
    then
        return 0
    fi

    return 1
}

check_all_links () {
    # This function is for systemd configurations
    for link in ${USED_DEVS[@]}
    do
        while true; do
            if [ $(check_link_up $link) -eq 1 ]
            then
                break
            fi
            sleep 2
        done
    done
}

turn_off_network_manager() {

    if [ -f /lib/systemd/system/NetworkManager.service ]; then
        sudo systemctl stop network-manager.service
        sudo systemctl disable network-manager.service
    fi

    if [ -f /etc/init.d/network-manager ]; then
        sudo service network-manager stop
        sudo rm /etc/init.d/network-manager
    fi
}

turn_off_network_manager

while read line; do
    read -ra args <<<"$line"

    if [ ${#args[@]} -gt 2 ]
    then
        while true; do
            NETWORK=${args[0]}
            MAC=${args[1]}
            ADDR=${args[2]}
            NETMASK=${args[3]}
            PREFIX=${args[4]}
            GATEWAY=""

            if [ ${#args[@]} -eq 6 ]
            then
                GATEWAY=${args[5]}
            fi

            DEV=$(find_device $MAC)

            if [[ ! -z $DEV ]]
            then
                set_ip $DEV "${ADDR}/${PREFIX}"
                set_gateway $GATEWAY
                if [ -d /etc/network ]; then
                    add_persistent_network_manager_static_ip $DEV $MAC $ADDR $NETMASK $GATEWAY
                fi
                if [ -d /etc/sysconfig/network-scripts ]; then
                    add_persistent_sysconfig_static_ip $DEV $MAC $ADDR $NETMASK $GATEWAY
                fi
                break
            fi

            >&2 echo "UNABLE TO FIND DEVICE FOR $MAC, sleeping"
            sleep 5
            get_interface_info
        done
    fi
done < $1
