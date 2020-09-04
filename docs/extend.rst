Customizing
===========

This package is built to be extended. You can either use the `Zope Component
Architecture` and provide an specific Adapter to control what is being returned
by the API or you simply write your own route provider.

This section will show how to build a custom route provider for an example
content type. It will also show how to write and register a custom data adapter
for this content type. It is even possible to customize how the fields of a
specific content type can be accessed or modified.

.. _ROUTE_PROVIDER:

Adding a custom route provider
------------------------------

Each route provider shipped with this package, provides the basic CRUD
functionality to `get`, `create`, `delete` and `update` the resource handled.

The same functionality can be used to provide this behavior for custom content
types. All necessary functions are located in the `api` module within this
package.


.. code-block:: python

    # CRUD
    from senaite.jsonapi.api import get_batched
    from senaite.jsonapi.api import create_items
    from senaite.jsonapi.api import update_items
    from senaite.jsonapi.api import delete_items

    # route dispatcher
    from senaite.jsonapi import add_route

    # GET
    @add_route("/todos", "todos", methods=["GET"])
    @add_route("/todos/<string:uid>", "todos", methods=["GET"])
    def get(context, request, uid=None):
        """ get all todos
        """
        return get_batched("Todo", uid=uid, endpoint="todo")


You can also specify an own `query` and pass it to the `get_batched` function of
the api. This gives full control over the executed query on the catalog:

.. code-block:: python

    @add_route("/mytodos", "mytodos", methods=["GET"])
    def mytodos(context, request):
        """ Returns all my todos
        """
        myself =
        query = {"portal_type": "Todo",
                 "creator": api.get_current_user().getId() }
        return get_batched(query=query)

.. note:: Other keywords (except `uid`) are ignored, if the `query` keyword is
          detected.

The upper example registers a function named `get` with the `add_route`
decorator. This ensures that this function gets called when the `/todos`
route is called, e.g. `http://localhost:8080/senaite/@@API/senaite/v1/todos`.

The second argument of the decorator is the endpoint, which is kind of the
registration key for our function. The last argument is the methods we would
like to handle here. In this case we're only interested in GET requests.

All route providers get always the `context` and the `request` as the first two
arguments. The `uid` keyword argument is passed in, when a UID was appended to
the URL, e.g `http://localhost:8080/senaite/@@API/v1/senaite/todo/a3f3f9efd0b4df190d16ea63d`.

The `get_batched` function we call inside our function will do all the heavy
lifting for us. We simply need to pass in the `portal_type` as the first
argument, the `UID` and the `endpoint`.

To be able to create, update and delete our `Todo` content type, it is
necessary to provide the following functions as well. The behavior is analogue
to the upper example but as there is no need for batching, the functions return
a Python `<list>` instead of a complete mapping as above.


.. code-block:: python

    ACTIONS = "create,update,delete,cut,copy,paste"

    # http://werkzeug.pocoo.org/docs/0.11/routing/#builtin-converters
    # http://werkzeug.pocoo.org/docs/0.11/routing/#custom-converters
    @route("/<any(" + ACTIONS + "):action>",
          "senaite.jsonapi.v1.action", methods=["POST"])
    @route("/<any(" + ACTIONS + "):action>/<string(maxlength=32):uid>",
          "senaite.jsonapi.v1.action", methods=["POST"])
    @route("/<string:resource>/<any(" + ACTIONS + "):action>",
          "senaite.jsonapi.v1.action", methods=["POST"])
    @route("/<string:resource>/<any(" + ACTIONS + "):action>/<string(maxlength=32):uid>",
          "senaite.jsonapi.v1.action", methods=["POST"])
    def action(context, request, action=None, resource=None, uid=None):
        """Various HTTP POST actions

        Case 1: <action>
        <site_id>/@@API/v1/senaite/<action>

        Case 2: <action>/<uid>
        -> The actions (update, delete) will performed on the object identified by <uid>
        -> The action (create) will use the <uid> as the parent folder
        <site_id>/@@API/v1/senaite/<action>/<uid>

        Case 3: <resource>/<action>
        -> The "target" object will be located by a location given in the request body (uid, path, parent_path + id)
        -> The actions (update, delete) will performed on the target object
        -> The action (create) will use the target object as the container
        <site_id>/@@API/v1/senaite/<resource>/<action>

        Case 4: <resource>/<action>/<uid>
        -> The actions (update, delete) will performed on the object identified by <uid>
        -> The action (create) will use the <uid> as the parent folder
        <Plonesite>/@@API/plone/api/1.0/<resource>/<action>
        """

        # Fetch and call the action function of the API
        func_name = "{}_items".format(action)
        action_func = getattr(api, func_name, None)
        if action_func is None:
            api.fail(500, "API has no member named '{}'".format(func_name))

        portal_type = api.resource_to_portal_type(resource)
        items = action_func(portal_type=portal_type, uid=uid)

        return {
            "count": len(items),
            "items": items,
            "url": api.url_for("senaite.jsonapi.v1.action", action=action),
        }


.. _DATA_ADAPTER:

Adding a custom  data adapter
-----------------------------

The data returned by the API for each content type is extracted by the `IInfo`
Adapter. This Adapter simply extracts all field values from the content.

To customize how the data is extracted from the content, you have to register an
adapter for a more specific interface on the content.

This adapter has to implement the `IInfo` interface.

.. code-block:: python

    from senaite.jsonapi.interfaces import IInfo
    from zope import interface


    class TodoAdapter(object):
        """ A custom adapter for Todo content types
        """
        interface.implements(IInfo)

        def __init__(self, context):
            self.context = context

        def to_dict(self):
            return {} # whatever data you need

        def __call__(self):
            # just implement it like this, don't ask x_X
            return self.to_dict()

Register the adapter in your `configure.zcml` file for your special interface:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for my custom content type -->
        <adapter
            for="my.addon.interfaces.ITodo"
            factory=".adapters.TodoAdapter"
            />

    </configure>


.. _DATA_MANAGER:

Adding a custom data manager
----------------------------

The data sent by the API for **each content type** is set by the `IDataManager`
Adapter. This Adapter has a simple interface:

.. code-block:: python

    class IDataManager(interface.Interface):
        """ Field Interface
        """

        def get(name):
            """ Get the value of the named field with
            """

        def set(name, value):
            """ Set the value of the named field
            """

        def json_data(name, default=None):
            """ Get a JSON compatible structure from the value
            """

To customize how the data is set to each field of the content, you have to
register an adapter for a more specific interface on the content.
This adapter has to implement the `IDataManager` interface.

.. note:: The `json_data` function is called by the Data Provider Adapter
          (`IInfo`) to get a JSON compatible return Value, e.g.:
          DateTime('2017/05/14 14:46:18.746800 GMT+2') -> "2017-05-14T14:46:18+02:00"

.. important:: Please be aware that you have to implement security for field
               level access on your own.

.. code-block:: python

    from persistent.dict import PersistentDict
    from senaite.jsonapi.interfaces import IDataManager
    from zope import interface
    from zope.annotation import IAnnotations


    class TodoDataManager(object):
        """ A custom data manager for Todo content types
        """
        interface.implements(IDataManager)

        def __init__(self, context):
            self.context = context

        @property
        def storage(self):
            return IAnnotations(self.context).setdefault('my.addon.todo', PersistentDict())

        def get(self, name):
            self.storage.get("name")

        def set(self, name, value):
            self.storage["name"] = value


Register the adapter in your `configure.zcml` file for your special interface:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for my custom content type -->
        <adapter
            for="my.addon.interfaces.ITodo"
            factory=".adapters.TodoDataManager"
            />

    </configure>


.. _FIELD_MANAGER:

Adding a custom field manager
-----------------------------

The default data managers (`IDataManager`) defined in this package know how to
`set` and `get` the values from fields. But sometimes it might be useful to be
more granular and know how to `set` and `get` a value for a **specific field**.

Therefore, `senaite.jsonapi` introduces Field Managers (`IFieldManager`), which
adapt a field.

This Adapter has a simple interface:

.. code-block:: python

    class IFieldManager(interface.Interface):
        """A Field Manager is able to set/get the values of a single field.
        """

        def get(instance, **kwargs):
            """Get the value of the field
            """

        def set(instance, value, **kwargs):
            """Set the value of the field
            """

        def json_data(instance, default=None):
            """Get a JSON compatible structure from the value
            """

To customize how the data is set to each field of the content, you have to
register a more specific adapter to a field.

This adapter has to implement then the `IFieldManager` interface.

.. note:: The `json_data` function is called by the Data Manager Adapter
          (`IDataManager`) to get a JSON compatible return Value, e.g.:
          DateTime('2017/05/14 14:46:18.746800 GMT+2') -> "2017-05-14T14:46:18+02:00"

.. note:: The `json_data` method is defined on context level (`IDataManger`) as
          well as on field level (`IFieldManager`). This is to handle objects
          w/o fields, e.g. Catalog Brains, Portal Object etc. and Objects which
          contain fields and want to delegate the JSON representation to the
          field.

.. important:: Please be aware that you have to implement security for field
               level access on your own.

.. code-block:: python

    class DateTimeFieldManager(ATFieldManager):
        """Adapter to get/set the value of DateTime Fields
        """
        interface.implements(IFieldManager)

        def set(self, instance, value, **kw):
            """Converts the value into a DateTime object before setting.
            """
            try:
                value = DateTime(value)
            except SyntaxError:
                logger.warn("Value '{}' is not a valid DateTime string"
                            .format(value))
                return False

            self._set(instance, value, **kw)

        def json_data(self, instance, default=None):
            """Get a JSON compatible value
            """
            value = self.get(instance)
            return api.to_iso_date(value) or default

Register the adapter in your `configure.zcml` file for your special interface:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

      <!-- Adapter for AT DateTime Field -->
      <adapter
          for="Products.Archetypes.interfaces.field.IDateTimeField"
          factory=".fieldmanagers.DateTimeFieldManager"
          />

    </configure>


.. _CATALOG:

Adding a custom catalog tool
----------------------------

.. note::
    Remember `senaite.jsonapi` searches against `portal_catalog` by default,
    but you can search against other catalogs by using the `catalog` parameter
    in the search query. See :ref:`_Search_Resource` for further information.

All search is done through a catalog adapter. This adapter has to provide at
least a `search` method. The others are optional, but recommended.

.. code-block:: python

    class ICatalog(interface.Interface):
        """ Catalog interface
        """

        def search(query):
            """ search the catalog and return the results
            """

        def get_catalog():
            """ get the used catalog tool
            """

        def get_indexes():
            """ get all indexes managed by this catalog
            """

        def get_index(name):
            """ get an index by name
            """

        def to_index_value(value, index):
            """ Convert the value for a given index
            """

To customize the catalog tool to get full control of the search, you have to
register an catalog adapter for a more specific interface on the portal. This
adapter has to implement the `ICatalog` interface.


.. code-block:: python

    from senaite.jsonapi.interfaces import ICatalog
    from senaite.jsonapi import api
    from zope import interface


    class MyCatalog(object):
        """My Catalog adapter
        """
        interface.implements(ICatalog)

        def __init__(self, context):
            self._catalog = api.get_tool("my_catalog")

        def search(self, query):
            """search the catalog
            """
            catalog = self.get_catalog()
            return catalog(query)

Register the adapter in your `configure.zcml` file for your special interface:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for a custom catalog adapter -->
        <adapter
            for=".interfaces.ICustomPortalMarkerInterface"
            factory=".catalog.MyCatalog"
            />

    </configure>


.. _CATALOG_QUERY:

Adding a custom catalog query adapter
-------------------------------------

.. note::
    Remember `senaite.jsonapi` searches against `portal_catalog` by default,
    but you can search against other catalogs by using the `catalog` parameter
    in the search query. See :ref:`_Search_Resource` for further information.

All search is done through a catalog adapter. The `ICatalogQuery` adapter
provides a suitable query usable for the `ICatalog` adapter. It should at least
provide a `make_query` method.

.. code-block:: python

    class ICatalogQuery(interface.Interface):
        """ Catalog query interface
        """

        def make_query(**kw):
            """ create a new query or augment an given query
            """

To customize a custom catalog tool to perform a search, you have to
register an catalog adapter for a more specific interface on the portal.
This adapter has to implement the `ICatalog` interface.


.. code-block:: python

    from senaite.jsonapi.interfaces import ICatalogQuery
    from zope import interface


    class MyCatalogQuery(object):
        """MyCatalog query adapter
        """
        interface.implements(ICatalogQuery)

        def __init__(self, catalog):
            self.catalog = catalog

        def make_query(self, **kw):
            """create a query suitable for the catalog
            """
            query = {"sort_on": "created", "sort_order": "descending"}
            query.update(kw)
            return query

Register the adapter in your `configure.zcml` file for your special interface:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for a custom query adapter -->
        <adapter
            for=".interface.ICustomCatalogInterface"
            factory=".catalog.MyCatalogQuery"
            />

    </configure>


.. _ADAPTER_CREATE:

Adding an adapter for create operation
--------------------------------------

SENAITE JSONAPI is *portal_type-naive*. This means that this add-on delegates
the responsibility of creation operation to the underlying add-on where the given
portal type is registered. This is true in most cases, except when:

- the container is the portal root (`senaite` path)
- the container is senaite's setup (`senaite/bika_setup` path)
- the container does not allow the specified `portal_type`

For the cases above, `senaite.jsonapi` will always return a 401 response.

Sometimes, one might want to handle the creation of a given object differently,
either because:

- you want a portal type to never be created through `senaite.jsonapi`
- you want a portal type to only be created in some specific circumstances
- you want to add some additional logic within the creation process
- etc.

SENAITE.JSONAPI provides the `ICreate` interface that allows you to handle
the `create` operation with more granularity. An Adapter of this interface is
initialized with the container object to be created. This interface provides
the following signatures:

.. code-block:: python

    class ICreate(interface.Interface):
        """Interface to handle creation of objects
        """

        def is_creation_allowed(self):
            """Returns whether the creation of this portal type for the given
            container is allowed
            """

        def is_creation_delegated(self):
            """Return whether the creation of this portal type has to be delegated
            to this adapter
            """

        def create_object(self, **data):
            """Creates an object
            """


Allow/disallow the creation of a content type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For instance, say you don't want to allow the creation of objects from type
`Todo` through the `senaite.jsonapi`:

.. code-block:: python

    from senaite.jsonapi.interfaces import ICreate
    from zope import interface


    class TodoCreateAdapter(object):
        """Custom adapter for the creation of Todo type
        """
        interface.implements(ICreate)

        def __init__(self, container):
            self.container = container

        def is_creation_allowed(self):
            """Returns whether the creation of the portal_type is allowed
            """
            return False


Register the adapter in your `configure.zcml` file for your special interface:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for a creation custom adapter -->
        <adapter
          name="Todo"
          factory=".TodoCreateAdapter"
          provides="senaite.jsonapi.interfaces.ICreate"
          for="*" />

    </configure>


.. note::
    This is a "named" adapter in which the name is the portal type.

Note that if you wanted this `Todo` type to be created through `senaite.jsonapi`,
except inside the container `Client`, you could do so by registering the adapter
for `IClient` type only:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for custom creation of Todo -->
        <adapter
          name="Todo"
          factory=".TodoCreateAdapter"
          provides="senaite.jsonapi.interfaces.ICreate"
          for="bika.lims.interfaces.IClient" />

    </configure>

.. note::
    We've used here a custom `Todo` type, but you can use this approach for any
    type registered in the system, being it from `senaite.core` (e.g. `Client',
    `SampleType`, etc.) or from any other add-on.


Custom creation of a content type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As we've explained before, you might want to have full control on the creation
of a given portal type because you have to add additional logic. You can use
the same adapter as before:

.. code-block:: python

    from Products.CMFPlone.utils import _createObjectByType
    from senaite.jsonapi.interfaces import ICreate
    from zope import interface


    class TodoCreateAdapter(object):
        """Custom adapter for the creation of Todo type
        """
        interface.implements(ICreate)

        def __init__(self, container):
            self.container = container

        def is_creation_allowed(self):
            """Returns whether the creation of the portal_type is allowed
            """
            return True

        def is_creation_delegated(self):
            """Returns whether the creation of this portal type has to be
            delegated to this adapter
            """
            return True

        def create_object(self, **data):
            """Creates an object
            """
            obj = _createObjectByType("Todo", self.container, tmpID())
            obj.edit(**data)
            obj.unmarkCreationFlag()
            obj.reindexObject()
            return obj

With this example, `senaite.jsonapi` will not follow the default procedure of
creation, but delegate the operation to the function `create_object` of this
adapter. Note the creation will only be delegated when the function
`is_creation_delegated` returns True.


.. _ADAPTER_UPDATE:

Adding an adapter for update operation
--------------------------------------

Sometimes, one might want to handle the update of a given object differently,
either because:

- you want an object to never be updated through `senaite.jsonapi`
- you want an object to only be updated in some specific circumstances
- you want to add some additional logic within the update process
- etc.

:ref:`DATA_MANAGER` or :ref:`FIELD_MANAGER` allows to achieve these goals
partially, cause their scope is at field level. If you need full control over
the update process, you can also create an adapter implementing `IUpdate`
interface. This interface allows you to handle the `update` operation by your
own. This interface provides the folllowing signatures:

.. code-block:: python

    class IUpdate(interface.Interface):
        """Interface to handle update of objects
        """

        def is_update_allowed(self):
            """Returns whether the update of the object is allowed
            """

        def update_object(self, **data):
            """Updates the object
            """


Allow/disallow to update an object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For instance, say you don't want to allow the update of objects from type
`Todo` through the `senaite.jsonapi`:

.. code-block:: python

    from senaite.jsonapi.interfaces import IUpdate
    from zope import interface


    class TodoUpdateAdapter(object):
        """Custom adapter for the update of objects from Todo type
        """
        interface.implements(IUpdate)

        def __init__(self, context):
            self.context = context

        def is_update_allowed(self):
            """Returns whether the update of the object is allowed
            """
            return False


Register the adapter in your `configure.zcml` file for your special interface:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for custom update -->
        <adapter
          factory=".TodoUpdateAdapter"
          provides="senaite.jsonapi.interfaces.IUpdate"
          for="my.addon.interfaces.ITodo" />

    </configure>


.. note::
    This adapter is initialized with `context`, the object to be updated.

.. note::
    We've used here a custom `Todo` type, but you can use this approach for any
    type registered in the system, being it from `senaite.core` (e.g. `Client',
    `SampleType`, etc.) or from any other add-on.


Custom update of an object
~~~~~~~~~~~~~~~~~~~~~~~~~~

Imagine that besides updating your object, you want to add a `Remarks` at the
same time. You can use the same adapter as before:

.. code-block:: python

    from senaite.jsonapi.interfaces import IUpdate
    from zope import interface


    class TodoUpdateAdapter(object):
        """Custom adapter for the update of objects from Todo type
        """
        interface.implements(IUpdate)

        def __init__(self, context):
            self.context = context

        def is_update_allowed(self):
            """Returns whether the update of the object is allowed
            """
            return True

        def update_object(self, **data):
            """Updates the object
            """
            self.context.setRemarks("Updated through json.api")
            self.context.edit(**data)
            self.context.reindexObject()


With this example, `senaite.jsonapi` will not follow the default procedure of
update, but delegate the operation to the function `update_object` of this
adapter.


.. __PUSH:

PUSH endpoint. Custom jobs
--------------------------

Sometimes is useful to have and endpoint to allow the execution of custom logic
without bothering about creating views, handing JSON, etc. This add-on provides
and end-point `push` that acts as a gateway for custom processes or actions.

Imagine you want to ask SENAITE to send an email to all contacts telling them
that the system won't be available for maintenance reasons for a while.

Add the following adapter in your add-on:

.. code-block:: python

    from bika.lims import api
    from bika.lims.api import mail as mailapi
    from senaite.jsonapi.interfaces import IPushConsumer
    from zope import interface


    class EmailNotifier(object):
        """Custom adapter for sending e-mail notifications to contacts
        """
        interface.implements(IPushConsumer)

        def __init__(self, data):
            self.data = data

        def process(self):
            """Send notifications to contacts
            """
            # Get the subject and body to be sent
            subject = data.get("subject")
            message = data.get("message")

            # Get e-mail addresses from all contacts
            emails = self.get_emails()

            # Send the emails
            success = map(lambda e: self.send(e, subject, message), emails)
            return any(success)

        def get_emails(self):
            """Returns the emails from all registered contacts
            """
            query = {"portal_type": ["Contact", "LabContact"]}
            contacts = map(api.get_object, api.search(query, "portal_catalog"))
            emails = map(lambda c: c.getEmailAddress(), contacts)
            emails = filter(None, emails)
            return list(OrderedDict.fromkeys(uids))

        def send(self, email, subject, body):
            """Creates and sends an email message
            """
            lab = api.get_setup().laboratory
            from_addr = lab.getEmailAddress()
            msg = mailapi.compose(from_addr, email, subject, body)
            return mailapi.send_email(mime_msg)


And register the adapter in your `configure.zcml` as follows:

.. code-block:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope">

        <!-- Adapter for processing email notifications -->
        <adapter
          name="my.addon.push.emailnotifier"
          factory=".EmailNotifier"
          provides="senaite.jsonapi.interfaces.IPushConsumer"
          for="*" />

    </configure>


You can now make use of `push` end-point to send messages:

http://localhost:8080/senaite/@@API/senaite/v1/push

Body Content type (application/json):

.. code-block:: javascript

    {
        "consumer": "my.addon.push.emailnotifier",
        "subject": "Sheduled LIMS maintenance",
        "message": "System will not be available from 16:00 to 18:00",
    }

Note the field `consumer` is mandatory and it's value must match with the name
of the adapter to use to process the job. You can add as many fields as required
by the job processor (consumer).
