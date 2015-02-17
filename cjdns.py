#!/usr/bin/env python
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import json


def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            authorizedPassword=dict(required=False),
            cjdroute=dict(required=False, default='/etc/cjdroute.conf'),
            autoclean=dict(requird=False, type='bool', default=True),
            udppeer=dict(required=False),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )
    changed = False
    try:
        import cjdnsadmin
        params = module.params
        cjdroute = json.load(open(params['cjdroute']))
        cjdns = cjdnsadmin.connect('127.0.0.1',
                                   11234, cjdroute['admin']['password'])
        if params['authorizedPassword'] is not None:
            if not 'user' in params['authorizedPassword']:
                module.fail_json(msg='No user specified')
            elif not 'password' in params['authorizedPassword'] and params['state'] == 'present':
                module.fail_json(msg='No password specified')
            else:
                position = None
                for i in range(0, len(cjdroute['authorizedPasswords'])):
                    passwordmatches = cjdroute['authorizedPasswords'][i]['password'] == params['authorizedPassword']['password']
                    usermatches = False
                    if 'user' in cjdroute['authorizedPasswords'][i]:
                        usermatches = cjdroute['authorizedPasswords'][i]['user'] == params['authorizedPassword']['user']
                    if passwordmatches or usermatches:
                        position = i
                if params['state'] == 'present':
                    if position is not None:
                        if cjdroute['authorizedPasswords'][position]['user'] != params['authorizedPassword']['user']:
                            cjdroute['authorizedPasswords'][position]['user'] = params['authorizedPassword']['user']
                            changed = True
                        if cjdroute['authorizedPasswords'][position]['password'] != params['authorizedPassword']['password']:
                            cjdroute['authorizedPasswords'][position]['password'] = params['authorizedPassword']['password']
                            changed = True
                    else:
                        cjdroute['authorizedPasswords'].append(params['authorizedPassword'])
                        ipv6 = 0
                        if 'ipv6' in params['authorizedPassword']:
                            ipv6 = params['authorizedPassword']['ipv6']
                        cjdns.AuthorizedPasswords_add(params['authorizedPassword']['password'],
                                                      params['authorizedPassword']['user'],
                                                      ipv6=ipv6)
                        changed = True
                if params['state'] == 'absent' and position is not None:
                    cjdroute['authorizedPasswords'].pop(position)
                    cjdns.AuthorizedPasswords_remove(params['authorizedPassword']['user'])
                    changed = True
        if params['udppeer'] is not None:
            if params['state'] == 'absent':
                if params['udppeer']['address'] in cjdroute['interfaces']['UDPInterface'][0]['connectTo']:
                    del cjdroute['interfaces']['UDPInterface'][0]['connectTo'][params['udppeer']['address']]
                    changed = True
            elif params['state'] == 'present':
                if params['udppeer']['address'] in cjdroute['interfaces']['UDPInterface'][0]['connectTo']:
                    for key in params['udppeer']['data']:
                        if key in cjdroute['interfaces']['UDPInterface'][0]['connectTo'][params['udppeer']['address']]:
                            if params['udppeer']['data'][key] != cjdroute['interfaces']['UDPInterface'][0]['connectTo'][params['udppeer']['address']][key]:
                                cjdroute['interfaces']['UDPInterface'][0]['connectTo'][params['udppeer']['address']][key] = params['udppeer']['data'][key]
                                changed = True
                        else:
                            cjdroute['interfaces']['UDPInterface'][0]['connectTo'][params['udppeer']['address']][key] = params['udppeer']['data'][key]
                            changed = True
                else:
                    cjdroute['interfaces']['UDPInterface'][0]['connectTo'][params['udppeer']['address']] = params['udppeer']['data']
                    cjdns.UDPInterface_beginConnection(
                        params['udppeer']['data']['publicKey'], params['udppeer']['address'], password=params['udppeer']['data']['password'])
                    changed = True
        facts = {}
        if "ipv6" in cjdroute:
            facts['ip'] = cjdroute['ipv6']
        if "publicKey" in cjdroute:
            facts['public_key'] = cjdroute['publicKey']
        facts['UDPInterface'] = []
        for interface in cjdroute['interfaces']['UDPInterface']:
            bind = interface['bind'].split(":")  # This is gonna break on IPv6
            udpiffact = {
                "port": bind[-1],
                "host": ":".join(bind[0:-1])    # This should handle IPv6 shit
            }
            facts['UDPInterface'].append(udpiffact)
        if changed:
            with open(params['cjdroute'], 'w') as cjdroutefile:
                json.dump(cjdroute, cjdroutefile, indent=4,
                          separators=(',', ': '), sort_keys=True)
        module.exit_json(changed=changed, ansible_facts={"cjdns": facts})
    except ImportError:
        module.fail_json(msg='Please install the cjdnsadmin python library')
    except IOError as e:
        module.fail_json(msg='Failed to open cjdroute.conf: %s' % e)

# import module snippets
from ansible.module_utils.basic import *
main()
