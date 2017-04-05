"""A serializer for serializing SQLAlchemy models to JSON API spec."""

import datetime

from inflection import dasherize, underscore


class JSONAPISerializer(object):
    """A JSON API serializer that serializes SQLAlchemy models."""

    def serialize(self, resources):
        """Serialize resource(s) according to json-api spec."""
        try:
            self.fields
            self.model
            self.dasherize
        except AttributeError:
            raise

        if 'id' not in self.fields:
            raise ValueError
        serialized = {
            'meta': {
                'sqlalchemy_jsonapi_version': '4.0.9'
            },
            'jsonapi': {
                'version': '1.0'
            }
        }
        # Determine multiple resources by checking for SQLAlchemy query count.
        if hasattr(resources, 'count'):
            serialized['data'] = []
            for resource in resources:
                serialized['data'].append(
                    self._render_resource(resource))
        else:
            serialized['data'] = self._render_resource(resources)

        return serialized

    def _render_resource(self, resource):
        """Renders a resource's top level members based on json-api spec.

        Top level members include:
            'id', 'type', 'attributes', 'relationships'
        """
        if not resource:
            return None
        # Must not render a resource that has same named
        # attributes as different model.
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
        attrs_to_ignore = set()

        for key, relationship in resource.__mapper__.relationships.items():
            attrs_to_ignore.update(set(
                [column.name for column in relationship.local_columns]).union(
                    {key}))

        if self.dasherize:
            mapped_fields = {x: dasherize(underscore(x)) for x in self.fields}
        else:
            mapped_fields = {x: x for x in self.fields}

        for attribute in self.fields:
            if attribute == 'id':
                continue
            # Per json-api spec, we cannot render foreign keys
            # or relationsips in attributes.
            if attribute in attrs_to_ignore:
                raise AttributeError
            try:
                value = getattr(resource, attribute)
                if isinstance(value, datetime.datetime):
                    attributes[mapped_fields[attribute]] = value.isoformat()
                else:
                    attributes[mapped_fields[attribute]] = value
            except AttributeError:
                raise

        return attributes

    def _render_relationships(self, resource):
        """Render the resource's relationships."""
        relationships = {}
        related_models = resource.__mapper__.relationships.keys()
        if self.dasherize:
            mapped_relationships = {
                x: dasherize(underscore(x)) for x in related_models}
        else:
            mapped_relationships = {x: x for x in related_models}

        for model in related_models:
            relationships[mapped_relationships[model]] = {
                'links': {
                    'self': '/{}/{}/relationships/{}'.format(
                        resource.__tablename__, resource.id,
                        mapped_relationships[model]),
                    'related': '/{}/{}/{}'.format(
                        resource.__tablename__, resource.id,
                        mapped_relationships[model])
                }
            }

        return relationships
