class GameObject(object):
    def __init__(self, row_dict, recurse):
        try:
            self.id = row_dict['Id']
            del row_dict['Id']
        except KeyError:
            self.id = 0
        self.recursive_add = recurse
        self.refs = self._get_refs(row_dict)
        self.attrs = row_dict

    def get_guid(self):
        return type(self).__name__ + str(self.id)

    def _get_refs(self, row_dict):
        ret = []
        for x in self.get_ref_names():
            try:
                for y in self.destructure_ref(x, row_dict[x]):
                    ret.append(y)
                del row_dict[x]
            except KeyError:
                pass
            except TypeError:
                pass
        return ret

    def get_ref_names(self):
        return ['QualitiesAffected', 'QualitiesRequired', 'QualitiesPossessedList', 'Enhancements', 'Personae',
                'StartingArea', 'LimitedToArea', 'Deck', 'Category', 'SettingIds', 'Shops', 'Availabilities',
                'QualitiesAffectedOnTarget', 'QualitiesAffectedOnVictory', 'PurchaseQuality', 'Quality']

    def destructure_ref(self, name, ref):
        if 'Qualities' in name or 'Quality' in name:
            try:
                return ('qualities' + str(x['AssociatedQuality']['Id']) for x in ref)
            except (TypeError, KeyError):
                return 'qualities' + str(ref['Id'])
        if name == 'LimitedToArea':
            return 'areas' + str(ref['Id']),
        if name == 'SettingIds':
            return ('settings' + str(x) for x in ref)
        if name == 'StartingArea':
            ref['type'] = 'areas'
            return self.recursive_add(ref),
        if name == 'Personae' or name == 'Shops' or name == 'Availabilities':
            ret = []
            for x in ref:
                x['type'] = name.lower()
                ret.append(self.recursive_add(x))
            return ret
        if name == 'Enhancements' or name == 'Deck':
            ref['type'] = name.lower()
            return self.recursive_add(ref),
        if name == 'Category':
            return name.lower() + ref['Id'] + ref['Title']
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
                                                                      'acts')}


def parse_dict_to_game_object(row_dict, recurse):
    if 'type' not in row_dict:
        return None, None
    return TYPES[row_dict['tye']](row_dict, recurse).to_graph_node()
