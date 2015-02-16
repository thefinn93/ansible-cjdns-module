#!/usr/bin/env python
import json


def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            authorizedPassword=dict(required=False),
            cjdroute=dict(required=False, default='/etc/cjdroute.conf'),
            autoclean=dict(requird=False, type='bool', default=True),
            udppeers=dict(required=False, type='DictType'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )
    changed = False
    try:
        import cjdnsadmin
        params = module.params
        cjdroute = json.load(open(params['cjdroute']))
        cjdns = cjdnsadmin.connect('127.0.0.1', 11234, cjdroute['admin']['password'])
        if params['authorizedPassword'] is not None:
            if not 'user' in params['authorizedPassword']:
                module.fail_json(msg='No user specified')
            elif not 'password' in params['authorizedPassword'] and param['state'] == 'present':
                module.fail_json(msg='No password specified')
            else:
                position = None
                for i in range(0, len(cjdroute['authorizedPasswords'])):
                    if cjdroute['authorizedPasswords'][i]['password'] == params['authorizedPassword']['password'] or cjdroute['authorizedPasswords'][i]['user'] == params['authorizedPassword']['user']:
                        position = i
                if params['state'] == 'present':
                    if position is not None:
                        if cjdroute['authorizedPasswords'][i]['user'] != params['authorizedPassword']['user']:
                            cjdroute['authorizedPasswords'][i]['user'] = params['authorizedPassword']['user']
                            changed = True
                        if cjdroute['authorizedPasswords'][i]['password'] != params['authorizedPassword']['password']:
                            cjdroute['authorizedPasswords'][i]['password'] = params['authorizedPassword']['password']
                            changed = True
                    else:
                        cjdroute['authorizedPasswords'].append(params['authorizedPassword'])
                        ipv6 = 0
                        if 'ipv6' in params['authorizedPassword']:
                            ipv6 = params['authorizedPassword']['ipv6']
                        cjdns.AuthorizedPasswords_add(params['authorizedPassword']['password'], params['authorizedPassword']['user'], ipv6=ipv6)
                        changed = True
                if params['state'] == 'absent' and position is not None:
                    cjdroute['authorizedPasswords'].pop(position)
                    cjdns.AuthorizedPasswords_remove(params['authorizedPassword']['user'])
                    changed = True
        if params['udppeer'] is not None:
            for peer in params['udppeers']:
                if params['state'] == 'absent':
                    if peer in cjdroute['interfaces']['UDPInterface'][0]['connectTo']:
                        del cjdroute['interfaces']['UDPInterface'][0]['connectTo'][peer]
                        changed = True
                elif params['state'] == 'present':
                    if peer in cjdroute['interfaces']['UDPInterface'][0]['connectTo']:
                        for key in params['udppeer'][peer]:
                            if key in cjdroute['interfaces']['UDPInterface'][0]['connectTo'][peer]:
                                if params['udppeer'][peer][key] != cjdroute['interfaces']['UDPInterface'][0]['connectTo'][peer][key]:
                                    cjdroute['interfaces']['UDPInterface'][0]['connectTo'][peer][key] = params['udppeer'][peer][key]
                                    changed = True
                            else:
                                cjdroute['interfaces']['UDPInterface'][0]['connectTo'][peer][key] = params['udppeer'][peer][key]
                                changed = True
                    else:
                        cjdroute['interfaces']['UDPInterface'][0]['connectTo'][peer] = params['udppeer'][peer]
                        cjdns.UDPInterface_beginConnection(
                            params['udppeer'][peer]['publicKey'],
                            peer, password=params['udppeer'][peer]['password'])
                        changed = True
        facts = {}
        if "ipv6" in cjdroute:
            facts['ip'] = cjdroute['ipv6']
        if "publicKey" in cjdroute:
            facts['public_key'] = cjdroute['publicKey']
        facts['UDPInterface'] = []
        for interface in cjdroute['interfaces']['UDPInterface']:
            bind = interface['bind'].split(":") # This is gonna break on IPv6 addresses
            facts['UDPInterface']
        if changed:
            with open(params['cjdroute'], 'w') as cjdroutefile:
                json.dump(cjdroute, cjdroutefile, indent=4,
                          separators=(',', ': '), sort_keys=True)
        module.exit_json(changed=changed, ansible_facts={"cjdns": facts})
    except ImportError:
        module.fail_json(msg='Please install the cjdnsadmin python library')
    except IOError:
        module.fail_json(msg='Failed to open cjdroute.conf')

# import module snippets
from ansible.module_utils.basic import *
main()
