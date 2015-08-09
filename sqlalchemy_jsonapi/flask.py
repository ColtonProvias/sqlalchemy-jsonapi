from .serializer import JSONAPI
from blinker import signal
from flask import request, jsonify


class FlaskJSONAPI(object):
    def __init__(self, app, sqla, namespace='api', route_prefix='/api'):
        self.app = app
        self.sqla = sqla
        self.serializer = JSONAPI(sqla.Model)
        self.on_request = signal('jsonapi-on-request')
        self.on_response = signal('jsonapi-on-response')
        for model_name in self.serializer.models.keys():
            setattr(self, 'on_request_' + model_name, signal(
                'jsonapi-on-request-' + model_name))

        for endpoint in ['get_collection', 'post_collection', 'get_resource',
                         'patch_resource', 'delete_resource', 'get_related',
                         'get_relationship', 'post_relationship',
                         'patch_relationship', 'delete_relationship']:
            for when in ['before', 'after']:
                name = '_'.join([when, endpoint])
                setattr(self, name, signal(
                    'jsonapi-' + name.replace('_', '-')))

        self.app.add_url_rule(route_prefix + '/<api_type>/',
                              namespace + '_get_collection',
                              self.get_collection)
        self.app.add_url_rule(route_prefix + '/<api_type>/',
                              namespace + '_post_collection',
                              self.post_collection,
                              methods=('POST'))
        self.app.add_url_rule(route_prefix + '/<api_type>/<obj_id>/',
                              namespace + '_get_resource', self.get_resource)
        self.app.add_url_rule(route_prefix + '/<api_type>/<obj_id>/',
                              namespace + '_patch_resource',
                              self.patch_resource,
                              methods=('PATCH'))
        self.app.add_url_rule(route_prefix + '/<api_type>/<obj_id>/',
                              namespace + '_delete_resource',
                              self.delete_resource,
                              methods=('DELETE'))
        self.app.add_url_rule(
            route_prefix + '/<api_type>/<obj_id>/<relationship>/',
            namespace + '_get_related', self.get_related)
        self.app.add_url_rule(
            route_prefix +
            '/<api_type>/<obj_id>/relationships/<relationship>/',
            namespace + '_get_relationship', self.get_relationship)
        self.app.add_url_rule(
            route_prefix +
            '/<api_type>/<obj_id>/relationships/<relationship>/',
            namespace + '_post_relationship', self.post_relationship,
            methods=('POST'))
        self.app.add_url_rule(
            route_prefix +
            '/<api_type>/<obj_id>/relationships/<relationship>/',
            namespace + '_patch_relationship', self.patch_relationship,
            methods=('PATCH'))
        self.app.add_url_rule(
            route_prefix +
            '/<api_type>/<obj_id>/relationships/<relationship>/',
            namespace + '_delete_relationship', self.delete_relationship,
            methods=('DELETE'))

    def handle_response(self, api_response):
        if api_response.status_code == 204:
            return {}, 204
        return jsonify(api_response.data), api_response.status_code

    def get_collection(self, api_type):
        self.on_request.send(self, api_type=api_type)
        self.before_get_collection.send(self, api_type=api_type)
        response = self.serializer.get(self.sqla.session, request.args,
                                       api_type)
        self.after_get_collection.send(self,
                                       api_type=api_type,
                                       response=response)
        self.on_response.send(self, api_type=api_type, response=response)
        return self.handle_response(response)

    def post_collection(self, api_type):
        self.on_request.send(self, api_type=api_type)
        self.before_post_collection.send(self, api_type=api_type)
        response = self.serializer.post(self.sqla.session, request.get_json(
            force=True), api_type)
        self.after_post_collection.send(self,
                                        api_type=api_type,
                                        response=response)
        self.on_response.send(self, api_type=api_type, response=response)
        return self.handle_response(response)

    def get_resource(self, api_type, obj_id):
        self.on_request.send(self, api_type=api_type, obj_id=obj_id)
        self.before_get_resource.send(self, api_type=api_type, obj_id=obj_id)
        response = self.serializer.get(self.sqla.session, request.args,
                                       api_type, obj_id)
        self.after_get_resource.send(self,
                                     api_type=api_type,
                                     obj_id=obj_id,
                                     response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              response=response)
        return self.handle_response(response)

    def patch_resource(self, api_type, obj_id):
        self.on_request.send(self, api_type=api_type, obj_id=obj_id)
        self.before_patch_resource.send(self, api_type=api_type, obj_id=obj_id)
        response = self.serializer.patch(self.sqla.session, request.get_json(
            force=True), api_type, obj_id)
        self.after_patch_resource.send(self,
                                       api_type=api_type,
                                       obj_id=obj_id,
                                       response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              response=response)
        return self.handle_response(response)

    def delete_resource(self, api_type, obj_id):
        self.on_request.send(self, api_type=api_type, obj_id=obj_id)
        self.before_delete_resource.send(self,
                                         api_type=api_type,
                                         obj_id=obj_id)
        response = self.serializer.delete(self.sqla.session, None, api_type,
                                          obj_id)
        self.after_delete_resource.send(self,
                                        api_type=api_type,
                                        obj_id=obj_id,
                                        response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              response=response)
        return self.handle_response(response)

    def get_related(self, api_type, obj_id, relationship):
        self.on_request.send(self,
                             api_type=api_type,
                             obj_id=obj_id,
                             relationship=relationship)
        self.before_get_related.send(self,
                                     api_type=api_type,
                                     obj_id=obj_id,
                                     relationship=relationship)
        response = self.serializer.get(self.sqla.session, request.args,
                                       api_type, obj_id, relationship)
        self.after_get_related.send(self,
                                    api_type=api_type,
                                    obj_id=obj_id,
                                    relationship=relationship,
                                    response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              relationship=relationship,
                              response=response)
        return self.handle_response(response)

    def get_relationship(self, api_type, obj_id, relationship):
        self.on_request.send(self,
                             api_type=api_type,
                             obj_id=obj_id,
                             relationship=relationship)
        self.before_get_relationship.send(self,
                                          api_type=api_type,
                                          obj_id=obj_id,
                                          relationship=relationship)
        response = self.serializer.get(self.sqla.session, request.args,
                                       api_type, obj_id,
                                       relationship=relationship)
        self.after_get_relationship.send(self,
                                         api_type=api_type,
                                         obj_id=obj_id,
                                         relationship=relationship,
                                         response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              relationship=relationship,
                              response=response)
        return self.handle_response(response)

    def post_relationship(self, api_type, obj_id, relationship):
        self.on_request.send(self,
                             api_type=api_type,
                             obj_id=obj_id,
                             relationship=relationship)
        self.before_post_relationship.send(self,
                                           api_type=api_type,
                                           obj_id=obj_id,
                                           relationship=relationship)
        response = self.serializer.post(self.sqla.session, request.get_json(
            force=True), api_type, obj_id, relationship)
        self.after_post_relationship.send(self,
                                          api_type=api_type,
                                          obj_id=obj_id,
                                          relationship=relationship,
                                          response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              relationship=relationship,
                              response=response)
        return self.handle_response(response)

    def patch_relationship(self, api_type, obj_id, relationship):
        self.on_request.send(self,
                             api_type=api_type,
                             obj_id=obj_id,
                             relationship=relationship)
        self.before_patch_relationship.send(self,
                                            api_type=api_type,
                                            obj_id=obj_id,
                                            relationship=relationship)
        response = self.serializer.patch(self.sqla.session, request.get_json(
            force=True), api_type, obj_id, relationship)
        self.after_patch_relationship.send(self,
                                           api_type=api_type,
                                           obj_id=obj_id,
                                           relationship=relationship,
                                           response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              relationship=relationship,
                              response=response)
        return self.handle_response(response)

    def delete_relationship(self, api_type, obj_id, relationship):
        self.on_request.send(self,
                             api_type=api_type,
                             obj_id=obj_id,
                             relationship=relationship)
        self.before_delete_relationship.send(self,
                                             api_type=api_type,
                                             obj_id=obj_id,
                                             relationship=relationship)
        response = self.serializer.delete(self.sqla.session, request.get_json(
            force=True), api_type, obj_id, relationship)
        self.after_delete_relationship.send(self,
                                            api_type=api_type,
                                            obj_id=obj_id,
                                            relationship=relationship,
                                            response=response)
        self.on_response.send(self,
                              api_type=api_type,
                              obj_id=obj_id,
                              relationship=relationship,
                              response=response)
        return self.handle_response(response)
