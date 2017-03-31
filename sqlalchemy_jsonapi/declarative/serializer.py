"""A serializer for serializing SQLAlchemy models to JSON API spec."""


class JSONAPISerializer(object):
    """A JSON API serializer that serializes SQLAlchemy models."""

    def serialize(self, resources):
        """Serialize resource(s) according to JSON API spec.

        Args:
            resources: SQLAlchemy model or SQLAlchemy query
        """
        if 'id' not in self.fields:
            raise AttributeError

        serialized_object = {
            'included': [],
            'jsonapi': {
                'version': '1.0'
            },
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            }
        }
        if isinstance(resources, self.model):
            serialized_object['data'] = self._render_resource(resources)
        else:
            serialized_object['data'] = []
            for resource in resources:
                serialized_object['data'].append(
                    self._render_resource(resource))

        return serialized_object

    def _render_resource(self, resource):
        """Renders a resource's top level members based on JSON API spec.

        Top level members include:
            'id', 'type', 'attributes', 'relationships'
        """
        # Must not render a resource that has same named attributes as different model.
        if not isinstance(resource, self.model):
            raise TypeError

        top_level_members = {}
        top_level_members['id'] = str(resource.id)
        top_level_members['type'] = resource.__tablename__
        top_level_members['attributes'] = self._render_attributes(resource)
        top_level_members['relationships'] = self._render_relationships(
                                                resource)

        return top_level_members

    def _render_attributes(self, resource):
        """Render the resources's attributes."""
        attributes = {}
        related_models = resource.__mapper__.relationships.keys()
        for attribute in self.fields:
            if attribute in related_models or attribute == 'id':
                continue
            try:
                attributes[attribute] = getattr(resource, attribute)
            except AttributeError:
                raise

        return attributes

    def _render_relationships(self, resource):
        """Render the resource's relationships."""
        relationships = {}
        related_models = resource.__mapper__.relationships.keys()
        for model in related_models:
            relationships[model] = {
                'links': {
                    'self': '/{}/{}/relationships/{}'.format(
                        resource.__tablename__, resource.id, model),
                    'related': '/{}/{}/{}'.format(
                        resource.__tablename__, resource.id, model)
                }
            }

        return relationships
