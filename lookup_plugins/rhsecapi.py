# (c) 2017 Ken Evensen <kevensen@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.module_utils.basic import AnsibleModule

import json
import re
import unicodedata

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class LookupModule(LookupBase):

    def _kind_from_item(self, item=''):

        if item.startswith('RHSA'):
            return 'cvrf'
        elif item.startswith('CVE'):
            return 'cve'
        elif re.search(r"^\d\d\d\d", item):
            return 'iava'

        raise AnsibleError("Unable to determine item type  Must be" +
                           "one of: cvrf, cve, oval, iava.")

    def _get_information(self, url, validate_certs, use_proxy):
        display.vvv("rhsecapi lookup connecting to %s" % url)
        try:
            response = open_url(url,
                                validate_certs=validate_certs,
                                use_proxy=use_proxy)
            return response.read()
        except HTTPError as e:
            raise AnsibleError("Received HTTP error for %s : %s" %
                               (url, str(e)))
        except URLError as e:
            raise AnsibleError("Failed lookup url for %s : %s" % (url, str(e)))
        except SSLValidationError as e:
            raise AnsibleError("Error validating the server's certificate "
                               "for %s: %s" % (url, str(e)))
        except ConnectionError as e:
            raise AnsibleError("Error connecting to %s: %s" % (url, str(e)))


    def run(self, terms, variables=None, **kwargs):

        item    = terms[0]
        api_url = kwargs.get("api_url",
                             "https://access.redhat.com/labs/securitydataapi")
        kind    = kwargs.get("kind", self._kind_from_item(item))

        validate_certs = kwargs.get('validate_certs', True)
        use_proxy      = kwargs.get('use_proxy', True)

        api_url += '/'
        api_url += kind
        api_url += '/'
        api_url += item
        api_url += '.json'

        raw = self._get_information(api_url, validate_certs, use_proxy)
        display.vvv("raw output %s" % json.dumps(json.loads(raw)))

        return [json.loads(raw)]
