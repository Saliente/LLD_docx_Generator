from show_tech import ShowTechWireless
from Meraki import GetMerakiConfig
from docxtpl import DocxTemplate



def cisco_built_generator(show_tech_entry, cisco_template_entry):
    # Carregar dados do arquivo "show tech wireless"
    with open(f'{show_tech_entry}', 'r') as file:
        show_tech_data = file.read()

    # Criar a instância da classe
    show_tech = ShowTechWireless(show_tech_data)


    #Variaveis
    #WLC Hostname
    hostname = show_tech.get_hostname()

    #WLC IP
    wlc_if = show_tech.get_wlc_ip()
    wlc_if_dict = {}
    wlc_interfaces = ''
    wlc_ips = ''
    for item in wlc_if:
        wlc_if_dict[item[0]] = item[1]
        wlc_interfaces += f'{str(item[0])}\n'
        wlc_ips += f'{str(item[1])}\n'


    #Version
    version = show_tech.get_version()

    #NTPs Servers
    ntp = show_tech.get_ntp()

    #SNMP Communities
    snmp = show_tech.get_snmp()

    #SNMP Trap Servers
    snmp_trap = show_tech.get_snmp_trap()

    #SysLog
    logging = show_tech.get_loggin()

    #Radius Servers
    radius_servers = show_tech.get_radius_server()

    #Radius Groups
    radius_groups = show_tech.get_radius_group()

    #AP List
    ap_list = show_tech.get_ap_inventory()

    #ACL List
    acl = show_tech.get_acl()

    #WLAN Profile
    wlan = show_tech.get_wlan()

    #Policy Profile
    policy = show_tech.get_policy_profile()

    #Policy TAG
    policy_tag = show_tech.get_policy_tag()

    rf_tag = show_tech.get_rf_tag()

    rf_profiles = show_tech.get_rf_profile_details()

    # Testar todas as funções e imprimir seus resultados
    # print("WLC IP and Interface:", show_tech.get_wlc_ip())
    site_tag = show_tech.get_site_tag()

    flex_profile = show_tech.get_flex_profile()

    doc_template = DocxTemplate(f'{cisco_template_entry}')
    context = {
        ## Inventory
        'hostname': hostname,
        'wlc_interfaces': wlc_interfaces,
        'wlc_ips': wlc_ips,
        'version': version,
        #TODO: Credencials

        ## Network Time Protocol
        'ntp': ntp,
        #Simple Network Management Protocol
        'snmp': snmp,
        'snmp_trap': snmp_trap,
        ## Syslog
        'logging': logging,
        ## AAA
        'radius_servers': radius_servers,
        'radius_groups': radius_groups,
        ## ACL
        'acl': acl,
        ## POLICY
        'policy_tag': policy_tag,
        'wlan': wlan,
        'policy': policy,
        ## RF
        'rf_tag': rf_tag,
        'rf_profiles': rf_profiles,
        'ap_list': ap_list,
        ## Site
        'site_tag': site_tag,
        'flex_profile': flex_profile
    }

    doc_template.render(context)
    doc_template.save('AsBuilt_LLD.docx')

def meraki_built_generator(token, organization_name, template_entry, network_name = ''):
    # Start
    report = GetMerakiConfig(token, organization_name)

    #List Network IDs
    report.get_network_list(network_name)
    # List of all devices from Network IDs
    device_list = report.get_devices()
    # List type of networks
    report.get_product_types()
    productType = list(set(report.productType))

    # Get Wireless Settings
    wireless_settings = report.get_wireless_setting()
    # Get SSIDs
    ssids = report.get_ssid()

    ## Generate Document
    doc_template = DocxTemplate(f'{template_entry}')
    context = {
        'productType': productType,
        'device_list': device_list,
        'wireless_settings': wireless_settings,
        'ssids': ssids
    }

    doc_template.render(context)
    doc_template.save('Meraki_AsBuilt_LLD.docx')


if __name__ == '__main__':
    meraki_built_generator('2941aade49a4500f2ab56ae425ec9f92e5da23a5', 'Instituto Unibanco','C:\\Users\\pedro.dalcolli\\Downloads\\Netskills\\LLD\\LLD_Template_Meraki.docx')
