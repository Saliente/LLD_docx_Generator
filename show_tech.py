import re


class ShowTechWireless:
    def __init__(self, show_tech_data):
        self.data = show_tech_data

    def get_hostname(self):
        match = re.search(r'hostname\s+(\S+)', self.data)
        if match:
            return match.group(1)
        return None

    def get_wlc_ip(self):
        match = re.search(
            r'------------------\s*show\s+ip\s+interface\s+brief\s*------------------(.*?)------------------',
            self.data, re.DOTALL)
        if match:
            interface_data = match.group(1)  # Extract the section after "show ip interface brief"

            # Now, we need to look for IP address and interface within this section
            ip_match = re.findall(r'(\S+)\s+(\d+\.\d+\.\d+\.\d+)\s+.*', interface_data)

            if ip_match:
                return ip_match
        return None

    def get_version(self):
        match = re.search(r'Cisco\s+IOS\s+XE\s+Software,\s+Version\s+(\S+)', self.data)
        if match:
            version = match.group(1)
            if "C9800-CL" in self.data:
                return version, "Virtual Controller"
            return version, "Physical Controller"
        return None

    def get_policy_tag(self):
        policy_tags = []

        # Regex para capturar as Policy Tags, Descrições e a Tabela de WLAN Profile e Policy Name
        pattern = r"Policy Tag Name\s*:\s*(\S+)\s*Description\s*:\s*([\w\s]*)\s*Number of WLAN-POLICY maps\s*:\s*(\d+)\s*([\s\S]*?)(?=\n\s*Policy Tag Name|\Z)"
        matches = re.findall(pattern, self.data)

        for match in matches:
            tag_name = match[0]
            description = match[1].strip()  # Remover quebras de linha extras
            wlan_count = int(match[2])
            wlan_info = []

            # Caso haja WLANs mapeadas, extrai os pares (WLAN Profile Name, Policy Name), excluindo o cabeçalho e divisor
            if wlan_count > 0:
                # Regex para capturar as linhas da tabela, excluindo o cabeçalho e o divisor
                wlan_pattern = r"(\S+)\s+(\S+)\s*(?=\n|$)"
                wlan_matches = re.findall(wlan_pattern, match[3])
                for wlan_match in wlan_matches:
                    if (wlan_match[0] != 'Policy') and (wlan_match[1] != 'Name'):
                        # wlan: policy
                        wlan_info.append({f'{wlan_match[0]}': f'{wlan_match[1]}'})

            wlan_map = ''

            for item in wlan_info:
                wlan_map += f'{list(item.keys())[0]}: {list(item.values())[0]}\n'

            policy_tags.append({
                "name": tag_name,
                "description": description,
                "wlan_policy_maps": wlan_map
            })

        return policy_tags

    def get_rf_tag(self):
        rf_tags = []

        # Regex para capturar as RF Tags e os RF Policies associados (6GHz, 5GHz, 2.4GHz)
        pattern = r"Tag Name\s*:\s*(\S+)\s*Description\s*:\s*([\w\s]*)\s*-{30,}\s*6ghz RF Policy\s*:\s*(\S+)\s*5ghz RF Policy\s*:\s*(\S+)\s*2.4ghz RF Policy\s*:\s*(\S+)"
        matches = re.findall(pattern, self.data)

        for match in matches:
            tag_name = match[0]
            description = match[1].strip()  # Remover quebras de linha extras

            rf_tags.append({
                "name": tag_name,
                "description": description,
                "wifi_ax": match[2],
                "wifi_ac": match[3],
                "wifi_n": match[4]
            })

        return rf_tags

    def get_rf_profile_details(self):
        """
        Extrai os detalhes de configuração de cada RF Profile.

        Captura blocos de 'ap dot11 <banda> rf-profile <nome>' e analisa
        as configurações internas para extrair potência, canais, RX-SOP e taxas de dados.

        Returns:
            list: Uma lista de dicionários, cada um representando um RF Profile.
        """
        rf_profiles_list: list = []

        # Regex para dividir o texto em blocos, cada um começando com "ap dot11"
        # Usa um "positive lookahead" para não consumir o delimitador.
        profile_blocks = re.split(r'(?=ap dot11 \S+ rf-profile)', self.data)

        for block in profile_blocks:
            # Pula blocos vazios ou que não são de um perfil de RF
            if not block.strip() or not block.startswith("ap dot11"):
                continue

            # Extrai a linha principal para obter nome e frequência
            header_match = re.match(r"ap dot11 (\S+) rf-profile (\S+)", block)
            if not header_match:
                continue

            frequency_band = header_match.group(1)
            profile_name = header_match.group(2)

            # Dicionário para armazenar os detalhes do perfil atual
            profile_details = {
                'name': profile_name,
                'frequency_band': frequency_band,
                'tx_power_min': 'N/A',
                'tx_power_max': 'N/A',
                'channel_width_min': 'N/A',
                'channel_width_max': 'N/A',
                'rx_sop': 'N/A',
                'mandatory_rates': [],
                'supported_rates': []
            }

            # --- Função auxiliar para extrair valores simples ---
            def extract_value(pattern, default='N/A'):
                match = re.search(pattern, block, re.MULTILINE)
                return match.group(1).strip() if match else default

            # 1. Extrair Potência, Largura de Canal e RX-SOP
            profile_details['tx_power_min'] = extract_value(r"^\s+tx-power min\s+(.*)")
            profile_details['tx_power_max'] = extract_value(r"^\s+tx-power max\s+(.*)")
            profile_details['rx_sop'] = extract_value(r"^\s+high-density rx-sop threshold\s+(.*)")

            # Lógica especial para largura de canal
            chan_width_min_match = extract_value(r"^\s+channel chan-width minimum\s+(.*)")
            chan_width_max_match = extract_value(r"^\s+channel chan-width maximum\s+(.*)")
            chan_width_best_match = re.search(r"^\s+channel chan-width best", block, re.MULTILINE)

            if chan_width_best_match:
                profile_details['channel_width_min'] = "best"
                profile_details['channel_width_max'] = "best"
            else:
                profile_details['channel_width_min'] = chan_width_min_match
                profile_details['channel_width_max'] = chan_width_max_match

            # 2. Extrair Taxas de Dados (Data Rates)
            rate_matches = re.findall(r"^\s+rate (\S+) (mandatory|supported)", block, re.MULTILINE)
            for rate, status in rate_matches:
                if status == 'mandatory':
                    profile_details['mandatory_rates'].append(rate)
                elif status == 'supported':
                    profile_details['supported_rates'].append(rate)

            # Converte as listas de taxas em strings para fácil exibição
            profile_details['mandatory_rates'] = ', '.join(profile_details['mandatory_rates']) or 'N/A'
            profile_details['supported_rates'] = ', '.join(profile_details['supported_rates']) or 'N/A'

            rf_profiles_list.append(profile_details)

        return rf_profiles_list

    def get_site_tag(self):
        """
        Extrai os detalhes de cada Site Tag a partir da saída de
        'show wireless tag site all'.

        A função localiza a seção correta, faz um loop por cada tag
        encontrada e extrai os campos 'name', 'description', 'flex_profile',
        'ap_profile' e 'local_site'.

        Returns:
            list: Uma lista de dicionários, onde cada dicionário representa
                  uma Site Tag com os detalhes extraídos.
        """
        site_tags_list = []

        # 1. Isola a seção inteira de 'show wireless tag site all' do arquivo.
        # A regex (.*?) captura todo o texto entre o cabeçalho e o próximo
        # cabeçalho de 'show', garantindo que peguemos apenas esta seção.
        show_tag_section_match = re.search(
            r'------------------ show wireless tag site all ------------------\n(.*?)(?=\n------------------ show)',
            self.data,
            re.DOTALL
        )

        # Se a seção não for encontrada no arquivo, retorna uma lista vazia.
        if not show_tag_section_match:
            return []

        tag_data_section = show_tag_section_match.group(1)

        # 2. Divide a seção em múltiplos blocos, um para cada "Site Tag Name".
        # O "lookahead" (?=...) é usado como delimitador para não remover o
        # "Site Tag Name" ao dividir o texto.
        tag_blocks = re.split(r'(?=Site Tag Name\s*:)', tag_data_section)

        # 3. Inicia o loop para processar cada bloco de Site Tag individualmente.
        for block in tag_blocks:
            # Pula blocos vazios ou de cabeçalho que não contêm dados de uma tag.
            if not block.strip() or "Site Tag Name" not in block:
                continue

            # Para cada bloco, busca por cada um dos campos de interesse.
            name_match = re.search(r"Site Tag Name\s*:\s*(.*)", block)
            desc_match = re.search(r"Description\s*:\s*(S*)", block)
            flex_match = re.search(r"Flex Profile\s*:\s*(.*)", block)
            ap_match = re.search(r"AP Profile\s*:\s*(.*)", block)
            local_site_match = re.search(r"Local-site\s*:\s*(.*)", block)

            # 4. Constrói o dicionário para a tag atual.
            # Para cada campo, verifica se a busca encontrou um resultado (match).
            # Se sim, usa o valor encontrado (.group(1).strip()).
            # Se não, ou se o valor for vazio, define como 'N/A'.
            # Isso trata elegantemente os campos opcionais como o Flex Profile.
            tag_details = {
                'name': name_match.group(1).strip() if name_match and name_match.group(1).strip() else 'N/A',
                'description': desc_match.group(1).strip() if desc_match and desc_match.group(1).strip() else 'N/A',
                'flex_profile': flex_match.group(1).strip() if flex_match and flex_match.group(1).strip() else 'N/A',
                'ap_profile': ap_match.group(1).strip() if ap_match and ap_match.group(1).strip() else 'N/A',
                'local_site': local_site_match.group(1).strip() if local_site_match and local_site_match.group(
                    1).strip() else 'N/A',
            }

            # Adiciona o dicionário populado à lista final.
            site_tags_list.append(tag_details)

        return site_tags_list

    def get_flex_profile(self):
        """
        Extrai os detalhes de configuração de cada Flex Profile.

        Captura blocos de 'show wireless profile flex all' e analisa
        as configurações internas para extrair o nome, Policy ACL,
        mapeamento de VLANs e a Native VLAN ID.

        Returns:
            list: Uma lista de dicionários, cada um representando um Flex Profile.
        """
        flex_profiles_list = []

        # 1. Isola a seção inteira de 'show wireless profile flex all' do arquivo.
        show_flex_section_match = re.search(
            r'-+\s+show\s+wireless\s+profile\s+flex\s+all\s+-+(.*?)(?=\n------------------ show)',
            self.data,
            re.DOTALL
        )

        flex_data_section = show_flex_section_match.group(1)

        # 2. Divide a seção em blocos, um para cada "Flex Profile Name".
        profile_blocks = re.split(r'(?=Flex Profile Name\s*:)', flex_data_section)

        # 3. Inicia o loop para processar cada bloco de Flex Profile.
        for block in profile_blocks:
            if not block.strip() or "Flex Profile Name" not in block or 'AP PMK propagation' in block:
                continue

            # Dicionário com valores padrão para cada perfil
            profile_details = {
                'name': 'N/A',
                'policy_acls': [],
                'vlan_mappings': [],
                'native_vlan_id': 'N/A'
            }

            # Extrai o nome do perfil e a Native VLAN ID
            name_match = re.search(r"Flex Profile Name\s*:\s*(.*)", block)
            if name_match:
                profile_details['name'] = name_match.group(1).strip()

            native_vlan_match = re.search(r"Native vlan ID\s*:\s*(\d+)", block)
            if native_vlan_match:
                profile_details['native_vlan_id'] = native_vlan_match.group(1).strip()

            # 4. Extrai as Policy ACLs
            policy_acl_section_match = re.search(
                r'Policy ACL\s*:\s*\n(.*?)(?=VLAN Name - VLAN ID mapping|HTTP-Proxy)',
                block,
                re.DOTALL
            )
            if policy_acl_section_match:
                acl_block = policy_acl_section_match.group(1)

                # Captura a primeira palavra de cada linha no bloco de ACLs
                all_first_words = re.findall(r'^\s*(\S+)', acl_block, re.MULTILINE)

                # Filtra a lista para manter apenas os nomes de ACL válidos
                acls = ''
                for word in all_first_words:
                    # Adiciona a palavra à lista somente se NÃO for um cabeçalho
                    # e NÃO for uma linha de separação (composta apenas por traços)
                    if word.upper() not in ['ACL', 'NAME'] and not all(c == '-' for c in word):
                        acls += f'{word}\n'

                profile_details['policy_acls'] = acls

            # 5. Extrai o Mapeamento de VLANs
            # Isola a subseção de VLAN Name - VLAN ID mapping
            vlan_mapping_section_match = re.search(
                r'VLAN Name - VLAN ID mapping\s*:\s*\n(.*?)(?=HTTP-Proxy)',
                block,
                re.DOTALL
            )
            if vlan_mapping_section_match:
                mapping_block = vlan_mapping_section_match.group(1)
                # Encontra todos os pares de Nome de VLAN e ID de VLAN
                mappings = re.findall(r'^\s*(\S+)\s+(\d+)', mapping_block, re.MULTILINE)
                vlan_id = ''
                for mapping in mappings:
                    vlan_id += f'{mapping[0]}: {mapping[1]}\n'
                profile_details['vlan_mappings'] = vlan_id

            flex_profiles_list.append(profile_details)

        return flex_profiles_list

    def get_ap_tag(self):
        ap_tags = []

        # Dividir o conteúdo em linhas
        lines = self.data.splitlines()

        # Encontrar a linha que contém "show ap tag summary"
        start_index = -1
        for i, line in enumerate(lines):
            if "show ap tag summary" in line:
                start_index = i
                break

        if start_index == -1:
            return ap_tags  # Se não encontrar a sessão, retorna lista vazia

        # A partir do start_index, começamos a capturar os dados dos APs
        # Ignoramos as linhas do cabeçalho até o divisor
        for i in range(start_index + 1, len(lines)):
            line = lines[i].strip()

            # Ignorar linha de cabeçalho ou qualquer linha irrelevante
            if line.startswith("AP Name") or line.startswith("Number of APs") or line.startswith(
                    "----------------------------------------------------------------"):
                continue

            # Procurar pelo divisor de linhas (------------------)
            if line.startswith("------------------"):
                break  # Interrompe a busca quando encontra o divisor

            # Para as linhas dos APs, dividimos a linha em campos
            fields = line.split()
            if len(fields) >= 6:  # Garantimos que estamos capturando a linha com os dados corretos
                ap_name = fields[0]
                ap_mac = fields[1]
                site_tag_name = fields[2]
                policy_tag_name = fields[3]
                rf_tag_name = fields[4]
                tag_source = fields[6]

                # Adiciona o dicionário com os dados do AP na lista
                ap_tags.append({
                    "ap_name": ap_name,
                    "ap_mac": ap_mac,
                    "site_tag_name": site_tag_name,
                    "policy_tag_name": policy_tag_name,
                    "rf_tag_name": rf_tag_name,
                    "tag_source": tag_source
                })

        return ap_tags

    def get_snmp(self):
        communities = []
        match = re.findall(r'snmp-server\s+community\s+(\S+)\s+(\S+)', self.data)
        for entry in match:
            communities.append({
                "community": entry[0],
                "permission": entry[1]
            })
        return communities

    def get_snmp_trap(self):
        communities = []
        match = re.findall(r'snmp-server\s+host\s+([0-9]+.[0-9]+.[0-9]+.[0-9]+)', self.data)
        for entry in match:
            communities.append(entry)
        return communities


    def get_loggin(self):
        servers = []
        match = re.findall(r'logging\s+host\s+([0-9]+.[0-9]+.[0-9]+.[0-9]+)', self.data)
        for entry in match:
            servers.append({
                "server": entry[0],
            })
        return servers

    def get_ntp(self):
        match = re.findall(r'ntp\s+ip\s+(\S+)', self.data)
        return match if match else None

    def get_dns(self):
        match = re.findall(r'ip\s+name-server\s+(\S+)', self.data)
        domain_match = re.search(r'ip\s+domain\s+name\s+(\S+)', self.data)
        dns_lookup_match = re.search(r'no\s+dns-lookups', self.data)
        dns_info = {
            "name-servers": match,
            "domain": domain_match.group(1) if domain_match else None,
            "dns-lookup-configured": not bool(dns_lookup_match)
        }
        return dns_info

    def get_acl(self):
        acl_list = []

        # Split the input data into lines for easier processing
        lines = self.data.splitlines()

        acl_name = None
        acl_commands = []

        # Process each line
        for line in lines:
            line = line.strip()  # Remove any leading/trailing spaces

            # Skip lines that are separators or headers
            if line.startswith("------------------"):
                # If we have collected an ACL, store it and reset
                if acl_name:
                    acl_list.append({
                        "acl_name": acl_name,
                        "acl_command": " ".join(acl_commands)  # Join the commands with space
                    })
                    acl_name = None
                    acl_commands = []  # Reset the commands for the next ACL
                continue  # Skip the separator line

            # Check if the line indicates a new ACL (starts with "Extended IP access list")
            elif line.startswith("Extended IP access list"):
                # If we already have a previous ACL, store it
                if acl_name:
                    acl_list.append({
                        "acl_name": acl_name,
                        "acl_command": " ".join(acl_commands)  # Join the commands with space
                    })

                # Get the new ACL name from the line (after "Extended IP access list ")
                acl_name = line.split("Extended IP access list ")[-1].strip()
                acl_commands = []  # Reset the list for the new ACL

            # Check if the line is a command line (lines starting with a number)
            elif line and line[0].isdigit():  # Check if the line starts with a number (indicating an ACL rule)
                acl_commands.append(f'{line}\n')

        # Don't forget to add the last ACL processed if it exists
        if acl_name:
            acl_list.append({
                "acl_name": acl_name,
                "acl_command": " ".join(acl_commands)  # Join the commands with space
            })

        return acl_list

    def get_radius_server(self):
        radius_servers = []
        match = re.findall(r'radius\s+server\s+(\S+)\s+address\s+ipv4\s+(\S+)\s+auth-port\s+(\S+)\s+acct-port\s+(\S+)', self.data)
        for entry in match:
            radius_servers.append({
                "name": entry[0],
                "ip": entry[1],
                "auth": entry[2],
                "acct": entry[3]
            })
        return radius_servers

    def get_radius_group(self):
        """
        Extrai os grupos de servidores RADIUS e os servidores associados a cada grupo.

        Captura blocos de configuração iniciados por 'aaa group server radius'
        e extrai os 'server name' de dentro de cada bloco.

        Returns:
            list: Uma lista de dicionários, onde cada dicionário contém o nome
                  do grupo e uma lista com os nomes dos servidores.
                  Ex: [{'group': 'ISE_GRP_1', 'server': ['ISE_01', 'ISE_02']}]
        """
        groups = []

        # Regex para encontrar cada bloco de configuração de grupo RADIUS.
        # Captura:
        # Grupo 1: O nome do grupo (\S+)
        # Grupo 2: Todo o bloco de configuração indentado que se segue ((?:^\s+.*\n?)*)
        pattern = re.compile(r"aaa\s+group\s+server\s+radius\s+(\S+)\n((?:^\s+.*\n?)*)", re.MULTILINE)

        # Itera sobre cada bloco de grupo encontrado no texto
        for match in pattern.finditer(self.data):
            group_name = match.group(1)
            config_block = match.group(2)

            # Agora, dentro do bloco de configuração, encontra todos os servidores
            servers = re.findall(r"^\s+server\s+name\s+(\S+)", config_block, re.MULTILINE)

            groups.append({
                "group": group_name,
                "server": servers
            })

        return groups

    def get_tacacs_server(self):
        tacacs_servers = []
        match = re.findall(r'tacacs-server\s+server\s+(\S+)', self.data)
        for server in match:
            tacacs_servers.append({"server": server})
        return tacacs_servers

    def get_tacacs_group(self):
        groups = []
        match = re.findall(r'tacacs-server\s+group\s+(\S+)', self.data)
        for group in match:
            groups.append({"group": group})
        return groups

    def get_method_list(self):
        methods = []
        match = re.findall(r'phase\s+(\S+)\s+name\s+(\S+)\s+type\s+(\S+)\s+group\s+(\S+)', self.data)
        for phase, name, type_, group in match:
            methods.append({
                "phase": phase,
                "name": name,
                "type": type_,
                "group": group
            })
        return methods

    def get_wlan(self):
        """
        Extrai os detalhes de configuração de cada WLAN.

        Captura blocos de 'wlan <profile_name> <id> <ssid>' e analisa
        as configurações internas para extrair políticas de rádio,
        listas de autenticação e o método de associação (PSK, 802.1x, etc.).

        Returns:
            list: Uma lista de dicionários, cada um representando uma WLAN
                  com seus detalhes de configuração.
        """
        wlan_list = []

        # Regex para encontrar cada bloco de configuração de WLAN.
        # Captura:
        # Grupo 1: Profile Name (\S+)
        # Grupo 2: ID (\d+)
        # Grupo 3: SSID (\S+)
        # Grupo 4: Todo o bloco de configuração indentado ((?:^\s+.*\n?)*)
        pattern = re.compile(r"^wlan\s+(\S+)\s+(\d+)\s+(\S+)\n((?:^\s+.*\n?)*)", re.MULTILINE)

        for match in pattern.finditer(self.data):
            profile_name = match.group(1)
            wlan_id = match.group(2)
            ssid = match.group(3)
            config_block = match.group(4)

            # Dicionário para armazenar os detalhes desta WLAN
            wlan_details = {
                "profile_name": profile_name,
                "id": wlan_id,
                "ssid": ssid,
                "wifi_n": "Disable",
                "wifi_ac": "Disable",
                "wifi_ax": "Disable",
                "auth_list": "N/A",
                "authz_list": "N/A",  # Authorization list
                "association_method": "Open",  # Valor padrão
                "psk": "N/A"
            }

            # --- Análise dentro do bloco de configuração ---

            # 1. Extrair Políticas de Rádio
            radio_24 = re.search(r"^\s+radio\s+policy\s+dot11\s+24ghz", config_block, re.MULTILINE)
            if radio_24:
                wlan_details["24ghz"] = "Enable"

            radio_5 = re.search(r"^\s+radio\s+policy\s+dot11\s+5ghz", config_block, re.MULTILINE)
            if radio_5:
                wlan_details["5ghz"] = "Enable"

            radio_6 = re.search(r"^\s+radio\s+policy\s+dot11\s+6ghz", config_block, re.MULTILINE)
            if radio_6:
                wlan_details["6ghz"] = "Enable"

            # 2. Extrair Listas de Autenticação e Autorização
            auth_list_match = re.search(r"^\s+security\s+dot1x\s+authentication-list\s+(\S+)", config_block,
                                        re.MULTILINE)
            if auth_list_match:
                wlan_details["auth_list"] = auth_list_match.group(1)

            authz_list_match = re.search(r"^\s+security\s+dot1x\s+authorization-list\s+(\S+)", config_block,
                                         re.MULTILINE)
            if authz_list_match:
                wlan_details["authz_list"] = authz_list_match.group(1)

            # 3. Determinar o Método de Associação
            if re.search(r"^\s+security\s+wpa\s+akm\s+psk", config_block, re.MULTILINE):
                wlan_details["association_method"] = "PSK"
                # Extrair a chave PSK, se houver
                psk_match = re.search(r"^\s+security\s+wpa\s+psk\s+set-key\s+ascii\s+\d\s+(.*)", config_block,
                                      re.MULTILINE)
                if psk_match:
                    wlan_details["psk"] = psk_match.group(1).strip()

            elif re.search(r"^\s+security\s+wpa\s+akm\s+sae", config_block, re.MULTILINE):
                wlan_details["association_method"] = "SAE"
                # Extrair a chave SAE (similar ao PSK)
                sae_match = re.search(r"^\s+security\s+sae\s+set-key\s+ascii\s+\d\s+(.*)", config_block, re.MULTILINE)
                if sae_match:
                    wlan_details["psk"] = sae_match.group(1).strip()  # Reutilizando campo PSK para simplificar

            elif re.search(r"^\s+security\s+(?:wpa\s+akm\s+)?dot1x", config_block, re.MULTILINE):
                wlan_details["association_method"] = "802.1X"

            # Adiciona os detalhes da WLAN processada à lista final
            wlan_list.append(wlan_details)

        return wlan_list

    def get_ap_inventory(self):
        ap_inventory = []

        # Dividindo o conteúdo em linhas
        lines = self.data.splitlines()

        # Encontrando o começo da seção com "Cisco AP Name   :"
        start_index = -1
        for i, line in enumerate(lines):
            if line.startswith("Cisco AP Name   :"):
                start_index = i
                break

        if start_index == -1:
            return ap_inventory  # Se não encontrar a sessão, retorna lista vazia

        # Variáveis para armazenar os dados do AP atual
        ap_name = ""
        country_code = ""
        ip_config = ""
        ip_address = ""
        ip_netmask = ""
        gateway_ip = ""
        ap_mode = ""
        software_version = ""
        ap_model = ""
        ap_user_name = ""

        # A partir do start_index, vamos começar a capturar os dados dos APs
        for i in range(start_index, len(lines)):
            line = lines[i].strip()

            # Ignorar as linhas de divisores
            if line.startswith("================================================="):
                continue

            # Quando encontrar um novo "Cisco AP Name", isso indica o começo de um novo AP
            if line.startswith("Cisco AP Name   :"):
                # Se já tivermos capturado dados de um AP, armazenamos
                if ap_name:
                    ap_inventory.append({
                        "ap_name": ap_name,
                        "country_code": country_code,
                        "ip_config": ip_config,
                        "ip_address": ip_address,
                        "ip_netmask": ip_netmask,
                        "gateway_ip": gateway_ip,
                        "ap_mode": ap_mode,
                        "software_version": software_version,
                        "ap_model": ap_model,
                        "ap_user_name": ap_user_name
                    })

                # Inicia a captura de um novo AP
                ap_name = line.split(":")[1].strip()
                country_code = ip_config = ip_address = ip_netmask = gateway_ip = ""
                ap_mode = software_version = ap_model = ap_user_name = ""

            # Captura o Country Code
            elif line.startswith("Country Code") and ":" in line:
                country_code = line.split(":")[1].strip()

            # Captura a configuração do IP
            elif line.startswith("IP Address Configuration") and ":" in line:
                ip_config = line.split(":")[1].strip()

            # Captura o IP Address
            elif line.startswith("IP Address") and ":" in line:
                ip_address = line.split(":")[1].strip()

            # Captura o IP Netmask
            elif line.startswith("IP Netmask") and ":" in line:
                ip_netmask = line.split(":")[1].strip()

            # Captura o Gateway IP Address
            elif line.startswith("Gateway IP Address") and ":" in line:
                gateway_ip = line.split(":")[1].strip()

            # Captura o AP Model
            elif line.startswith("AP Model") and ":" in line:
                ap_model = line.split(":")[1].strip()

            # Captura o AP Mode
            elif line.startswith("AP Mode") and ":" in line:
                ap_mode = line.split(":")[1].strip()

            # Captura a Software Version
            elif line.startswith("Software Version") and ":" in line:
                software_version = line.split(":")[1].strip()

            # Captura o AP User Name
            elif line.startswith("AP User Name") and ":" in line:
                ap_user_name = line.split(":")[1].strip()

        # Após o loop, adiciona o último AP (pois ele não será adicionado dentro do loop)
        if ap_name:
            ap_inventory.append({
                "ap_name": ap_name,
                "country_code": country_code,
                "ip_config": ip_config,
                "ip_address": ip_address,
                "ip_netmask": ip_netmask,
                "gateway_ip": gateway_ip,
                "ap_mode": ap_mode,
                "software_version": software_version,
                "ap_model": ap_model,
                "ap_user_name": ap_user_name
            })

        return ap_inventory

    def get_policy_profile(self):
        """
        Extrai os detalhes de configuração de cada Policy Profile.

        Captura blocos de "Policy Profile Name" e analisa as configurações
        internas para extrair VLAN, QoS, timeouts, políticas AAA e mais.

        Returns:
            list: Uma lista de dicionários, cada um representando um
                  Policy Profile com seus detalhes.
        """
        profiles_list = []

        # Regex para dividir o texto em blocos, cada um começando com "Policy Profile Name"
        # A expressão (?=...) é um "positive lookahead" que não consome o texto,
        # permitindo que a próxima busca comece a partir dele.
        profile_blocks = re.split(r'(?=Policy Profile Name\s*:)', self.data)

        for block in profile_blocks:
            if not block.strip() or "Policy Profile Name" not in block:
                continue

            # Dicionário para armazenar os detalhes do perfil atual
            profile_details = {
                'name': 'N/A',
                'vlan': 'N/A',
                'qos_per_ssid_ingress': 'N/A',
                'qos_per_ssid_egress': 'N/A',
                'qos_per_client_ingress': 'N/A',
                'qos_per_client_egress': 'N/A',
                'switching_mode': 'Local (FlexConnect)',  # Padrão
                'profiling': [],
                'idle_timeout': 'N/A',
                'session_timeout': 'N/A',
                'aaa_override': 'N/A',
                'nac': 'N/A',
                'accounting_list': 'N/A'
            }

            # --- Funções auxiliares para extrair valores ---
            def extract_value(pattern, default='N/A'):
                match = re.search(pattern, block, re.MULTILINE)
                return match.group(1).strip() if match else default

            # 1. Extrair os campos principais
            profile_details['name'] = extract_value(r"Policy Profile Name\s*:\s*(.*)")
            profile_details['vlan'] = extract_value(r"VLAN\s*:\s*(.*)")
            profile_details['idle_timeout'] = extract_value(r"Idle Timeout\s*:\s*(.*)")
            profile_details['session_timeout'] = extract_value(r"Session Timeout\s*:\s*(.*)")
            profile_details['aaa_override'] = extract_value(r"AAA Override\s*:\s*(.*)")
            profile_details['nac'] = extract_value(r"NAC\s*:\s*(.*)")
            profile_details['accounting_list'] = extract_value(r"Accounting List\s*:\s*(.*)")

            # 2. Extrair QoS
            profile_details['qos_per_ssid_ingress'] = extract_value(r"QOS per SSID\n\s+Ingress Service Name\s*:\s*(.*)")
            profile_details['qos_per_ssid_egress'] = extract_value(
                r"QOS per SSID\n(?:.*\n)\s+Egress Service Name\s*:\s*(.*)")
            profile_details['qos_per_client_ingress'] = extract_value(
                r"QOS per Client\n\s+Ingress Service Name\s*:\s*(.*)")
            profile_details['qos_per_client_egress'] = extract_value(
                r"QOS per Client\n(?:.*\n)\s+Egress Service Name\s*:\s*(.*)")

            # 3. Determinar o modo de Switching
            if "Flex Central Switching\s*:\s*ENABLED" in block:
                profile_details['switching_mode'] = 'Central'

            # 4. Verificar o Profiling
            if "RADIUS Profiling\s*:\s*ENABLED" in block:
                profile_details['profiling'].append('RADIUS')
            if "HTTP TLV caching\s*:\s*ENABLED" in block:
                profile_details['profiling'].append('HTTP')
            if "DHCP TLV caching\s*:\s*ENABLED" in block:
                profile_details['profiling'].append('DHCP')

            # Converte a lista de profiling em uma string
            if not profile_details['profiling']:
                profile_details['profiling'] = 'DISABLED'
            else:
                profile_details['profiling'] = ', '.join(profile_details['profiling'])

            profiles_list.append(profile_details)

        return profiles_list
