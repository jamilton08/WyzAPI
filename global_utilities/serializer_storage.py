def organization(query, many = False):
    from orgs.serializers import OrgSerializer
    instance = OrgSerializer(query, many = many)
    return instance.data

def session(query, many = False):
    pass

def wyzdatemodel(query, many = False):
    from tiempo.serializers import WyzDateModelSerializer
    instance = WyzDateModelSerializer(query, many = many)
    return instance.data

def wyztimemodel(query, many = False):
    from tiempo.serializers import WyzTimeModelSerializer
    instance = WyzTimeModelSerializer(query, many = many)
    return instance.data

def wyzfloatmodel(query, many = False):
    from tiempo.serializers import WyzFloatModelSerializer
    instance = WyzFloatModelSerializer(query, many = many)
    return instance.data
