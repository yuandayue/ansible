#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_context
short_description: Manage private networks (aka. contexts) on Cisco ACI fabrics
description:
- Manage private networks (aka. contexts) on Cisco ACI fabrics.
- Each context is a private network associated to a tenant, i.e. VRF.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- Tested with ACI Fabric 1.0(3f)+
notes:
- The tenant used must exist before using this module in your playbook. The M(aci_tenant) module can be used for this.
options:
  tenant:
    description:
    - The name of the Tenant the VRF should belong to.
    aliases: [ tenant_name ]
  vrf:
    description:
    - The name of the VRF.
    aliases: [ context, name, vrf_name ]
  policy_control_direction:
    description:
    - Determines if the policy should be enforced by the fabric on ingress or egress.
    choices: [ egress, ingress ]
  policy_control_preference:
    description:
    - Determines if the Fabric should enforce Contrac Policies.
    choices: [ enforced, unenforced ]
  description:
    description:
    - Description for the VRF.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new VRF to a tenant
  aci_context:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    vrf: vrf_lab
    tenant: lab_tenant
    descr: Lab VRF
    policy_control_preference: enforced
    policy_control_direction: ingress
    state: present

- name: Remove a VRF for a tenant
  aci_context:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    vrf: vrf_lab
    tenant: lab_tenant
    state: absent

- name: Query a VRF of a tenant
  aci_context:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    vrf: vrf_lab
    tenant: lab_tenant
    state: query

- name: Query all VRFs
  aci_context:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query
'''

RETURN = r''' # '''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        description=dict(type='str', aliases=['descr']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
        policy_control_direction=dict(choices=['ingress', 'egress'], type='str'),
        policy_control_preference=dict(choices=['enforced', 'unenforced'], type='str'),
        state=dict(choices=['absent', 'present', 'query'], type='str', default='present'),
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
        vrf=dict(type='str', required=False, aliases=['context', 'name', 'vrf_name']),  # Not required for querying all objects
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    description = module.params['description']
    policy_control_direction = module.params['policy_control_direction']
    policy_control_preference = module.params['policy_control_preference']
    state = module.params['state']
    tenant = module.params['tenant']
    vrf = module.params['vrf']

    aci = ACIModule(module)

    if vrf is not None:
        if tenant is not None:
            path = 'api/mo/uni/tn-%(tenant)s/ctx-%(vrf)s.json' % module.params
        elif state == 'query':
            path = 'api/mo/uni/tn-%(tenant)s.json?rsp-subtree=children&rsp-subtree-class=fvCtx&rsp-subtree-include=no-scoped' % module.params
        else:
            module.fail_json(msg="Parameter 'tenant' is required for state 'absent' or 'present'")
    elif state == 'query':
        path = 'api/class/fvCtx.json'
    else:
        module.fail_json(msg="Parameter 'vrf' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module params with null values
        aci.payload(aci_class='fvCtx', class_config=dict(descr=description, pcEnfDir=policy_control_direction, pcEnfPref=policy_control_preference, name=vrf))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvCtx')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
