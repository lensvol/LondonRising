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
        return []

    def destructure_ref(self, name, ref):
        if 'Qualities' in name:
            try:
                return (Quality.__name__ + str(x['AssociatedQuality']['Id']) for x in ref)
            except (TypeError, KeyError):
                return Quality.__name__ + str(ref['Id'])
        if name == 'LimitedToArea':
            return Area.__name__ + str(ref['Id']),
        if name == 'StartingArea':
            ref['type'] = name.lower()
            return self.recursive_add(ref),
        if name == 'Personae':
            ret = []
            for x in ref:
                x['type'] = 'persona'
                ret.append(self.recursive_add(x))
            return ret
        if name == 'Enhancements':
            ref['type'] = name.lower()
            return self.recursive_add(ref),
        if name == 'Deck':
            ref['type'] = name.lower()
            return self.recursive_add(ref),
        if name == 'Category':
            return name.lower() + ref['Id'] + ref['Title']
        raise ValueError("Cannot destructure reference to " + name)

    def to_graph_node(self):
        return (self.get_guid(), self.attrs), ((self.get_guid(), x) for x in self.refs)


class SideBarContents(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)


class LivingStory(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)

    def get_ref_names(self):
        return ['QualitiesAffected', 'QualitiesRequired']


class Quality(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)

    def get_ref_names(self):
        return ['QualitiesPossessedList', 'Enhancements']


class Setting(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)

    def get_ref_names(self):
        return ['Personae', 'StartingArea']


class Area(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)


class Persona(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)


class AccessCode(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)

    def get_ref_names(self):
        return ['QualitiesAffected']


class NewsItem(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)


class Domicile(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)


class Event(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)

    def get_ref_names(self):
        return ['LimitedToArea', 'QualitiesAffected', 'QualitiesRequired', 'Deck']


class Deck(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)


class StoreItem(GameObject):
    def __init__(self, row_dict, recurse):
        super().__init__(row_dict, recurse)

    def get_ref_names(self):
        return ['QualitiesAffected', 'QualitiesRequired', 'Category']


def parse_dict_to_game_object(row_dict, recurse):
    types = {
        'sidebarcontents': SideBarContents,
        'livingstories': LivingStory,
        'qualities': Quality,
        'settings': Setting,
        'startingarea': Area,
        'persona': Persona,
        'accesscodes': AccessCode,
        'newsitems': NewsItem,
        'areas': Area,
        'domiciles': Domicile,
        'events': Event,
        'deck': Deck,
        'storeitems': StoreItem
        #  TODO: acts, exchanges
    }
    if 'type' not in row_dict:
        return None, None
    curr_type = row_dict['type']
    del row_dict['type']
    try:
        return types[curr_type](row_dict, recurse).to_graph_node()
    except KeyError:
        import traceback
        traceback.print_exc()
        return GameObject(row_dict, recurse).to_graph_node()
