class GameObject(object):

    refnames = ['QualitiesAffected', 'QualitiesRequired', 'QualitiesPossessedList', 'Enhancements', 'Personae',
                'StartingArea', 'LimitedToArea', 'Deck', 'Category', 'SettingIds', 'Shops', 'Availabilities',
                'QualitiesAffectedOnTarget', 'QualitiesAffectedOnVictory', 'PurchaseQuality', 'Quality',
                'ChildBranches', 'ParentEvent', 'areaid']

    def __init__(self, row_dict, recurse):
        self.id = row_dict['Id']
        del row_dict['Id']
        self.recursive_add = recurse
        self.attrs = {}
        self.refs = []
        self.init_attrs_and_refs(row_dict)

    def get_guid(self):
        return type(self).__name__ + str(self.id)

    def init_attrs_and_refs(self, row_dict):
        for k in row_dict:
            if k in self.refnames:
                self.refs.extend(self.destructure_ref(k, row_dict[k]))
            else:
                self.attrs[k] = row_dict[k]

    def destructure_ref(self, name, ref):
        if 'Qualities' in name or name == 'Enhancements':
            return ('qualities' + str(x['AssociatedQuality']['Id']) for x in ref)
        if 'Quality' in name:
            return 'qualities' + str(ref['Id'])
        if name == 'areaid':
            return 'areas' + ref
        if name == 'LimitedToArea':
            return 'areas' + str(ref['Id']),
        if 'Event' in name:
            return 'events' + str(ref['Id']),
        if name == 'SettingIds':
            return ('settings' + str(x) for x in ref)
        if name == 'StartingArea':
            ref['type'] = 'areas'
            return self.recursive_add(ref),
        if name == 'Personae' or name == 'Shops' or name == 'Availabilities' or name == 'ChildBranches':
            ret = []
            for x in ref:
                x['type'] = name.lower()
                ret.append(self.recursive_add(x))
            return ret
        if name == 'Deck':
            if len(ref) == 0:
                return name.lower() + str(ref)
            ref['type'] = name.lower()
            return self.recursive_add(ref),
        if name == 'Category':
            try:
                return name.lower() + ref['Id']
            except TypeError:
                return name.lower() + str(ref)
        raise ValueError("Cannot destructure reference to " + name)

    def to_graph_node(self):
        return (self.get_guid(), {k: (self.attrs[k] if type(self.attrs[k]) is str
                                      else str(self.attrs[k]))
                                  for k in self.attrs}),\
               ((self.get_guid(), x) for x in self.refs)


TYPES = {typename: type(typename, (GameObject,), {}) for typename in ('sidebarcontents', 'livingstories',
                                                                      'qualities', 'settings', 'personae',
                                                                      'accesscodes', 'newsitems', 'areas',
                                                                      'domiciles', 'events', 'deck', 'storeitems',
                                                                      'exchanges', 'shops', 'availabilities',
                                                                      'acts', 'childbranches')}


def parse_dict_to_game_object(row_dict, recurse):
    if 'type' not in row_dict:
        return None, None
    return TYPES[row_dict['type']](row_dict, recurse).to_graph_node()
