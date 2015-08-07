class JSONAPI(object):
    def __init__(self, base):
        self.base = base
        self.models = {
            k: v
            for k, v in base._decl_class_registry.items()
            if not k.startswith('_')
        }

    def get(self, session, args, type,
            id=None,
            relation=None,
            relationship=None):
        pass

    def post(self, session, data, type, id=None, relationship=None):
        pass

    def patch(self, session, data, type, id=None, relationship=None):
        pass

    def delete(self, session, data, type, id=None, relationship=None):
        pass
