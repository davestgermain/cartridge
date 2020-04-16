import zipfile
import re
from collections import OrderedDict
from xml.etree import ElementTree

class Item(OrderedDict):
    def __init__(self, cart, data=None):
        OrderedDict.__init__(self, data)
        self._cart = cart

    def open(self):
        return self._cart.get_resource(self['resource_id'])


class Cartridge:
    ns = {'ims': 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1'}

    def __init__(self, cartridge_file):
        self.cartridge = zipfile.ZipFile(cartridge_file)
        self.metadata = None
        self.resources = None
        self.organizations = None
        self.version = '1.1'

    def load_manifest(self):
        with self.cartridge.open('imsmanifest.xml') as fp:
            tree = ElementTree.parse(fp).getroot()
            self.ns['ims'] = ns = re.match('\{(.*)\}', tree.tag).group(1)
            self.version = ns.split('/')[-1].split('_')[-1].replace('p', '.')
            self.metadata = self.parse_metadata(tree.find('./ims:metadata', self.ns))
            self.organizations = self.parse_organizations(tree.find('./ims:organizations', self.ns))
            self.resources = self.parse_resources(tree.find('./ims:resources', self.ns))
            return tree

    def parse_metadata(self, meta):
        if meta is not None:
            children = list(meta)
            # print(children)

    def parse_organizations(self, organizations):
        orgs = []
        for org in organizations or []:
            orgs.append(self.parse_organization(org))
        return orgs

    def parse_organization(self, org):
        items = []
        for item in org or []:
            items.append(self.parse_item(item))
        return items

    def parse_item(self, item):
        item_dict = Item(self, {
            'id': item.get('identifier'),
            'resource_id': item.get('identifierref'),
        })
        items = []
        title = item.find('./ims:title', self.ns)
        if title is not None:
            item_dict['title'] = title.text
        for subitem in item.findall('./ims:item', self.ns):
            items.append(self.parse_item(subitem))
        if items:
            item_dict['items'] = items
        return item_dict

    def parse_resources(self, resources):
        r_dict = OrderedDict()
        for resource in resources or []:
            r_dict[resource.get('identifier')] = {
                'type': resource.get('type'),
                'file': resource.get('href'),
                'files': [e.get('href') for e in resource],
            }
        return r_dict

    def get_resource(self, resource_id):
        if resource_id:
            resource = self.resources[resource_id]
            return self.cartridge.open(resource.get('file') or resource['files'][0])


if __name__ == '__main__':
    import sys
    cart = Cartridge(sys.argv[1])
    tree = cart.load_manifest()
    print('Cartridge Version: {}'.format(cart.version))

