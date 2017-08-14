# devstack/plugin.sh
# Functions necessary to install networking-opencontrail


function install_opencontrail() {
    echo_summary "Installing Networking OpenContrail Driver"
    setup_develop $OPENCONTRAIL_DIR
}

function configure_opencontrail() {
    echo_summary "Configuring Neutron for OpenContrail Driver"
    cp $OPENCONTRAIL_ML2_CONF_SAMPLE $OPENCONTRAIL_ML2_CONF_FILE

    iniset $OPENCONTRAIL_ML2_CONF_FILE APISERVER api_server_ip $OPENCONTRAIL_APISERVER_IP
    iniset $OPENCONTRAIL_ML2_CONF_FILE APISERVER api_server_port $OPENCONTRAIL_APISERVER_PORT

    if [ -n "${OPENCONTRAIL_USE_SSL+x}" ]; then
        iniset $OPENCONTRAIL_ML2_CONF_FILE APISERVER use_ssl $OPENCONTRAIL_USE_SSL
    fi
    if [ -n "${OPENCONTRAIL_INSECURE+x}" ]; then
        iniset $OPENCONTRAIL_ML2_CONF_FILE APISERVER insecure $OPENCONTRAIL_INSECURE
    fi
    if [ -n "${OPENCONTRAIL_CERT_FILE+x}" ]; then
        iniset $OPENCONTRAIL_ML2_CONF_FILE APISERVER certfile $OPENCONTRAIL_CERT_FILE
    fi
    if [ -n "${OPENCONTRAIL_KEY_FILE+x}" ]; then
        iniset $OPENCONTRAIL_ML2_CONF_FILE APISERVER keyfile $OPENCONTRAIL_KEY_FILE
    fi
    if [ -n "${OPENCONTRAIL_CA_FILE+x}" ]; then
        iniset $OPENCONTRAIL_ML2_CONF_FILE APISERVER cafile $OPENCONTRAIL_CA_FILE
    fi

    neutron_server_config_add $OPENCONTRAIL_ML2_CONF_FILE
}

if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
    # no-op
    :
elif [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_opencontrail

elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_opencontrail

elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
    # no-op
    :
fi

if [[ "$1" == "unstack" ]]; then
    # no-op
    :
fi

if [[ "$1" == "clean" ]]; then
    # no-op
    :
fi

