CRUD
====

Each content route provider shipped with this package, provides the basic CRUD
:ref:`Operations` functionality to `create`, `read`, `update` and `delete` the
resource handled, except that the `delete` operation tries to deactivate the
resource instead of deleting it. The reason is that for traceability reasons,
*delete* operation is not supported in SENAITE LIMS.

Keep in mind that available operations are strongly bound to permissions, so
the operation will only take place if the user has enough privileges for that
operation and resource status.


Unified API
-----------

:URL Schema: ``<BASE URL>/<OPERATION>/<uid:optional>``

There is a convenient and unified way to fetch the content without knowing the
resource. This unified resource is directly located at the :ref:`BASE_URL`.


CREATE
------

The `create` route will create the content inside the container located at the
given UID.

http://localhost:8080/senaite/@@API/senaite/v1/<RESOURCE:optional>/create/<uid:optional>

The given RESOURCE defines the type of object to create. You can omit this value
and specify the type with `portal_type` variable in the HTTP POST body. Check
:ref:`Operations`: for more information.

The given optional UID defines the target container. You can omit this UID
and specify all the information in the HTTP POST body.

The following are the POST parameters required for the creation of any type of
object:

- `portal_type`: The type name of to object to be created (e.g. `Client`),
  Required if `<RESOURCE>` is omitted in the url.
- `parent_path`: Physical path of the parent container (e.g. `/senaite/clients`),
  Required if `<uid>` is omitted in the url.

.. note:: `parent_uid` (the UID of the parent container) can be used instead of
          `parent_path`

Additional fields might be required depending on the resource to be created. For
instance, for the creation of a `Client` object, values for two additional
fields are required: `Name` and `ClientID`.

.. important::
   SENAITE.JSONAPI does not allow the creation of objects when:

   - the container is the portal root (`senaite` path)
   - the container is senaite's setup (`senaite/bika_setup` path)
   - the container does not allow the specified `portal_type`

   In such cases, `senaite.jsonapi` will always return a 401 response.


The examples below show possible variations of a HTTP POST body sent to the
JSON API with the header **Content-Type: application/json** set. Remember you
can use the `Advanced Rest Client`_ Application to send POST requests. See
:doc:`installation` for details.


Example: Client creation
........................

Request URL:

http://localhost:8080/senaite/@@API/senaite/v1/create

Body Content type (application/json):

.. code-block:: javascript

    {
        "portal_type": "Client",
        "title": "Test Client",
        "ClientID": "TEST-01",
        "parent_path": "/senaite/clients"
    }

Example: Sample Type creation
.............................

Request URL:

http://localhost:8080/senaite/@@API/senaite/v1/create

Body Content type (application/json):

.. code-block:: javascript

    {
        "portal_type": "SampleType",
        "title": "Test Sample Type",
        "description": "This is a new Sample Type",
        "Hazardous": false,
        "Prefix": "TST",
        "MinimumVolume": "10 mL",
        "RetentionPeriod": {
          "days": 5,
          "hours": 0,
          "minutes": 0
        },
        "parent_path": "/senaite/bika_setup/bika_sampletypes"
    }


Example: Sample Creation
........................

Request URL:

http://localhost:8080/senaite/@@API/senaite/v1/AnalysisRequest/create/<client_uid>

Body Content type (application/json):

.. code-block:: javascript

    {
        "Contact": <client_contact_uid>,
        "SampleType": <sample_type_uid>,
        "DateSampled": "2020-03-05 14:21:20",
        "Template": <ar_template_uid>,
    }


where:

- `<client_uid>` is the UID of the Client
- `<client_contact_uid>` is the UID of a Contact from the Client
- `<sample_type_uid>` is the UID of the Sample Type
- `<ar_template_uid>` is the UID of the Sample Template

.. note:: In this example, the RESOURCE (`AnalysisRequest`) has been defined in
          the url, as well as the parent container. This is also supported, as
          explained in :ref:`Operations`.
          Remember that in SENAITE LIMS, the portal type that represents samples
          is `AnalysisRequest`.


READ
----

The `read` route does not exist, use the base url to retrieve a content by uid,
as explained in :ref:`Operations`. E.g.:

http://localhost:8080/senaite/@@API/senaite/v1/<uid>

Please, refer to :ref:`Search_Resource` section to learn how to search objects.


UPDATE
------

The `update` route will update the content located at the given UID.

http://localhost:8080/senaite/@@API/senaite/v1/update/<uid:optional>

The given optional UID defines the object to update. You can omit this UID and
specify all the information in the HTTP POST body by using either:

- `path` parameter, as the physical path to the object, or
- `uid` parameter, as the UID of the object

Alternatively, you can use `id` and `parent_path` parameters with the values
from the parent container as well.

.. important::
   SENAITE.JSONAPI does not allow the update of objects when:

   - the container is the portal root (`senaite` path)
   - the container is senaite's setup (`senaite/bika_setup` path)

   In such cases, `senaite.jsonapi` will always return a 401 response.

The `update` route can also be used to perform transitions by using the keyword
`transition` in the HTTP POST body.

The examples below show possible variations of a HTTP POST body sent to the
JSON API with the header **Content-Type: application/json** set. Remember you
can use the `Advanced Rest Client`_ Application to send POST requests. See
:doc:`installation` for details.

Example
.......

Given this Request URL:

http://localhost:8080/senaite/@@API/senaite/v1/update

the following POSTs are equivalent, all them update the "Priority" of sample
DBS-00012 to 2:

.. code-block:: javascript

    {
        "path": "/senaite/clients/client-1/DBS-00012",
        "Priority": 2,
    }

.. code-block:: javascript

    {
        "uid": <uid_of_sample_DBS-00012>,
        "Priority": 2,
    }

.. code-block:: javascript

    {
        "id": "DBS-00012",
        "parent_path": "/senaite/clients/client-1",
        "Priority": 2,
    }

Using the same URL with this HTTP POST body:

.. code-block:: javascript

    {
        "uid": <uid_of_sample_DBS-00012>,
        "Priority": 2,
        "transition": "receive"
    }

will update the "Priority" field of the sample to `2` and will perform the
transition "receive" to the Sample with id `DBS-00012`. This transition will
only take place if the sample is in a suitable status and the user has enough
privileges for the transition to take place.

DELETE
------

The `delete` route will deactivate the content located at the given UID.

http://localhost:8080/senaite/@@API/senaite/v1/delete/<uid:optional>

The given optional UID defines the object to deactivate. You can omit this UID
and specify all the information in the HTTP POST body.

Example
.......

Deactivate an object by its **physical path**:

http://localhost:8080/senaite/@@API/senaite/v1/delete?path=/senaite/clients/client-1

Or you can specify the **parent path** and the **id** of the object

http://localhost:8080/Plone/@@API/plone/api/1.0/delete?parent_path=/senaite/clients&id=client-1

Or you can specify these information in the request body:

.. code-block:: javascript

    {
        uid: "<object_uid>"
    }



.. Links

.. _Advanced Rest Client: https://chrome.google.com/webstore/detail/advanced-rest-client/hgmloofddffdnphfgcellkdfbfbjeloo