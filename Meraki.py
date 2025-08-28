from itertools import product

import meraki


class GetMerakiConfig:
    dashboard = ''
    organization = ['']
    network = ['']
    productType = []

    def __init__(self, api, organization_name=''):
        """
        Structure the output to be used by docxtpl returning in list or dictionary
        :param api: API Token from your Meraki user
        :param organization_name: The oganization Name that you want to extract the information
        """
        self.api = str(api)
        self.dashboard = meraki.DashboardAPI(self.api)

    ## Get organization ID from name
        organizations_json = self.dashboard.organizations.getOrganizations()
        org_list = []
        for item in organizations_json:
            if organization_name == item['name']:
                org_dict = {item['name']: item['id']}
                org_list = [org_dict]
                break
            else:
                org_dict = {item['name']: item['id']}
                org_list.append(org_dict)
        self.organization = org_list


    #Get Organization ID from name or from Organization
    def get_network_list(self, network_name = ''):
        network_list = []
        for item in self.organization:
            network = self.dashboard.organizations.getOrganizationNetworks(
                list(item.values())[0], total_pages='all'
            )
            for json_file in network:
                if network_name == json_file['name']:
                    network_dict = {json_file['name']: json_file['id']}
                    network_list = [network_dict]
                    break
                else:
                    network_dict = {json_file['name']: json_file['id']}
                    network_list.append(network_dict)
        self.network = network_list

    def get_network_array(self):
        network_array = []
        # verify network list
        if self.network == ['']:
            self.get_network_list()
        # get only network IDs in array
        for net in self.network:
            net = list(net.values())[0]
            network_array.append(net)
        return network_array

    def get_devices(self):
        devices = []
        #get devices for each network in self.network
        for org in self.organization:
            org = list(org.values())[0]
            devices.append(self.dashboard.organizations.getOrganizationDevices(
                org, total_pages='all', networkIds=self.get_network_array() )
            )
        return devices[0]

    def get_product_types(self, device_list=''):
        if device_list == '':
            device_list = self.get_devices()
        for device in device_list:
            if device not in self.productType:
                self.productType.append(device['productType'])
            else:
                pass

        # self.productType = self.productType.sort()
        return self.productType

    def get_wireless_setting(self):

        network_settings = []

        for network in self.get_network_array():
            network_json = self.dashboard.networks.getNetwork(network)
            if 'wireless' in network_json['productTypes']:
                network_settings.append(self.dashboard.wireless.getNetworkWirelessSettings(network))
                network_settings[-1]['network'] = network_json['name']
        if not network_settings:
            return [{'meshingEnabled': 'Not Supported',
                     'ipv6BridgeEnabled': 'Not Supported',
                     'regulatoryDomainName': 'Not Supported',
                     'countryCode': 'Not Supported',
                     'permits6e': 'Not Supported',
                     'name': 'Not Supported'}]
        else:
            net_sets = []
            for dictionary in network_settings:
                item = {'meshingEnabled': dictionary['meshingEnabled'],
                        'ipv6BridgeEnabled': dictionary['ipv6BridgeEnabled'],
                        'regulatoryDomainName': dictionary['regulatoryDomain']['name'],
                        'countryCode': dictionary['regulatoryDomain']['countryCode'],
                        'permits6e': dictionary['regulatoryDomain']['permits6e'],
                        'name': dictionary['network']}
                net_sets.append(item)

            return net_sets

    def get_ssid(self):
        ssids = []
        for network in self.get_network_array():
            network_json = self.dashboard.networks.getNetwork(network)

            if 'wireless' in network_json['productTypes']:
                ssids_setting = self.dashboard.wireless.getNetworkWirelessSsids(network_json['id'])
                
                for ssid_setting in ssids_setting:
                    if ssid_setting['enabled']:
                        # Create a Dict with important info
                        ssid_values = {
                            'name': ssid_setting['name'],
                            'bandSelection': ssid_setting['bandSelection'],
                            'availabilityTags': ssid_setting['availabilityTags'],
                            'authMode': ssid_setting['authMode'],
                            'minBitrate': ssid_setting['minBitrate']
                        }

                        # Get the Auth Config values Value in one key
                        if ssid_setting['authMode'] == 'psk':
                            ssid_values['authValue'] = ssid_setting['psk']


                        elif ssid_setting['authMode'] == '8021x-radius':
                            servers = 'Radius Auth:\n'
                            for server in ssid_setting['radiusServers']:
                                servers += f'{server['host']}:{server['port']}\n'

                            servers += 'Accounting:\n'


                            for server in ssid_setting['radiusAccountingServers']:
                                servers += f'{server['host']}:{server['port']}\n'

                            ssid_values['authValue'] = servers


                        elif ssid_setting['authMode'] == '8021x-meraki':
                            ssid_values['authValue'] = 'System Manager'
                        elif ssid_setting['authMode'] == 'open':
                            if ssid_setting['splashPage'] == 'Sponsored guest':
                                ssid_values['authValue'] = f'Sponsor e-mail:\n{ssid_setting['splashGuestSponsorDomains']}'
                            elif ssid_setting['authMode'] == 'Click-through splash page':
                                ssid_values['authValue'] = f'External Portal: \n{ssid_setting['adminSplashUrl']}'
                            else:
                                ssid_values['authValue'] = 'Open'
                        else:
                            ssid_values['authValue'] = ssid_setting['authMode']
        
                        # Encrypt Algorithm
                        if ssid_setting['authMode'] != 'open':
                            ssid_values['wpaEncryptionMode'] = ssid_setting['wpaEncryptionMode']

                            # Get the PMF Value in one key
                            if ssid_setting['dot11w']['enabled'] and ssid_setting['dot11w']['required']:
                                ssid_values['dot11w'] = 'Required'
                            elif ssid_setting['dot11w']['enabled']:
                                ssid_values['dot11w'] = 'Enabled'
                            else:
                                ssid_values['dot11w'] = 'Disabled'

                            # Get the FastRoaming Value in one key
                            if ssid_setting['dot11r']['enabled'] and ssid_setting['dot11r']['adaptive']:
                                ssid_values['dot11r'] = 'Adaptive'
                            elif ssid_setting['dot11r']['enabled']:
                                ssid_values['dot11r'] = 'Enabled'
                            else:
                                ssid_values['dot11r'] = 'Disabled'

                        else:
                            ssid_values['wpaEncryptionMode'] = ssid_setting['authMode']
                            ssid_values['dot11r'] = 'Not Required'
                            ssid_values['dot11w'] = 'Not Required'

                        # Get VLAN
                        if ssid_setting['useVlanTagging']:
                            ssid_values['defaultVlanId'] = ssid_setting['defaultVlanId']
                        else:
                            ssid_values['defaultVlanId'] = 'Meraki NAT'


                        ssids.append(ssid_values)

                    else:
                        pass
            else:
                pass

        return ssids









if __name__ == "__main__":
    report = GetMerakiConfig('2941aade49a4500f2ab56ae425ec9f92e5da23a5', 'JEITTO MEIOS DE PAGAMENTOS LTDA')
    report.get_network_list()
    #Get Array devices dictionary
    device_list = report.get_devices()
    ssids = report.get_ssid()
    product = list(set(report.get_product_types()))
    print(product)



