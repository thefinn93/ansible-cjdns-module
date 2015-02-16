# Ansible cjdns module

An ansible module to configure cjdns. Currently implemented are gathering of a few
key facts (cjdns IP and public key) and adding or removing AuthorizedPasswords.
Documentation will follow eventually, for now see `cjdns.yml`. Note that the
[cjdnsadmin](https://pypi.python.org/pypi/cjdnsadmin) library must be installed.
It can either be copied out of the cjdns `contrib/python` folder.

Sample `cjdns.yml` invocation:

    ANSIBLE_LIBRARY=. ansible-playbook cjdns.yml


*I have no idea how to package an ansible module. This is
proly super broken, I'll figure that shit out later*
