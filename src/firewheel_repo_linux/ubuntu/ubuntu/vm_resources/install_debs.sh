 #!/bin/bash

BINARY=$2

echo "Handling binary package: ${BINARY}"

install_debian_packages () {
    SINGLE=$1
    if [ ! -z "$SINGLE" ]; then
        PACKAGES=$SINGLE
    fi
    if [ -z "$SINGLE" ]; then
        PACKAGES=$(find . -name '*.deb')
    fi

    until dpkg -i --force-depends $PACKAGES
    do
        sleep 1
        echo "DPKG FAILING: Sleeping and trying again"
    done
}

# Check to see if it is a single debian package
if [ ! -z "$(file $BINARY | grep 'Debian binary package')" ]; then
    # Install the single deb
    install_debian_packages $BINARY
fi

# Check if the binary data is a compressed directory of debian packages
if [ ! -z "$(file $BINARY | grep -i 'compressed data')" ]; then
    tar xf $BINARY
    install_debian_packages
fi
